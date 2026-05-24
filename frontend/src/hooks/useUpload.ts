import { useState, useCallback } from 'react';
import { api } from '../api/client';

interface UploadResult {
  uploaded: { id: number; filename: string; media_type: string }[];
  failed: unknown[];
  processing: boolean;
}

export function useUpload() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<UploadResult | null>(null);

  const addFiles = useCallback((files: FileList | File[]) => {
    const incoming = Array.from(files).filter(
      f => f.type.startsWith('image/') || f.type.startsWith('video/')
    );
    setSelectedFiles(prev => {
      const merged = [...prev, ...incoming];
      if (merged.length > 100) {
        alert('单次最多上传 100 张');
        return merged.slice(0, 100);
      }
      return merged;
    });
    setResult(null);
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const upload = useCallback(async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setProgress(30);
    try {
      const formData = new FormData();
      selectedFiles.forEach(f => formData.append('files', f));
      const res = await api.uploadFormData<UploadResult>('/api/media/upload', formData);
      setProgress(100);
      setResult(res);
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setUploading(false);
    }
  }, [selectedFiles]);

  const reset = useCallback(() => {
    setSelectedFiles([]);
    setResult(null);
    setProgress(0);
  }, []);

  return { selectedFiles, uploading, progress, result, addFiles, removeFile, upload, reset };
}
