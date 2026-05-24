import { useState, useCallback } from 'react';
import { api } from '../api/client';

interface UploadResult {
  uploaded: { id: number; filename: string; media_type: string }[];
  failed: unknown[];
  processing: boolean;
}

const ALLOWED_EXTENSIONS = new Set([
  '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif',
  '.heic', '.heif',
  '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v',
]);

function isValidFile(file: File): boolean {
  // Check MIME type first
  if (file.type.startsWith('image/') || file.type.startsWith('video/')) return true;
  // Fallback: check extension for files with empty MIME type (e.g. HEIC on some browsers)
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  return ALLOWED_EXTENSIONS.has(ext);
}

export function useUpload() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [result, setResult] = useState<UploadResult | null>(null);

  const addFiles = useCallback((files: FileList | File[]) => {
    const incoming = Array.from(files).filter(isValidFile);
    const skipped = Array.from(files).length - incoming.length;
    setSelectedFiles(prev => {
      const merged = [...prev, ...incoming];
      if (merged.length > 100) {
        alert('单次最多上传 100 张');
        return merged.slice(0, 100);
      }
      return merged;
    });
    if (skipped > 0) {
      alert(`${skipped} 个文件格式不支持，已跳过`);
    }
    setResult(null);
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const upload = useCallback(async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setProgress(0);

    const allUploaded: UploadResult['uploaded'] = [];
    const allFailed: unknown[] = [];

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      setCurrentFile(file.name);
      setProgress(Math.round((i / selectedFiles.length) * 100));

      try {
        const formData = new FormData();
        formData.append('files', file);
        const res = await api.uploadFormData<UploadResult>('/api/media/upload', formData);
        allUploaded.push(...res.uploaded);
        allFailed.push(...res.failed);
      } catch (err) {
        allFailed.push({ name: file.name, error: (err as Error).message });
      }
    }

    setProgress(100);
    setResult({ uploaded: allUploaded, failed: allFailed, processing: allUploaded.length > 0 });
    setUploading(false);
  }, [selectedFiles]);

  const reset = useCallback(() => {
    setSelectedFiles([]);
    setResult(null);
    setProgress(0);
    setCurrentFile('');
  }, []);

  return { selectedFiles, uploading, progress, currentFile, result, addFiles, removeFile, upload, reset };
}
