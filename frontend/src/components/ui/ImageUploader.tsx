import { useState, useRef, type DragEvent } from 'react';

interface ImageUploaderProps {
  onUpload: (file: File) => void;
  loading?: boolean;
}

export default function ImageUploader({ onUpload, loading }: ImageUploaderProps) {
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) return;
    setPreview(URL.createObjectURL(file));
    onUpload(file);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-card p-8 text-center transition-colors cursor-pointer ${
        dragging ? 'border-primary bg-subtle' : 'border-misty hover:border-primary/50'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileRef.current?.click()}
    >
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {preview ? (
        <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-card object-contain" />
      ) : (
        <>
          <span className="text-4xl block mb-3">🖼️</span>
          <p className="text-sm text-text">拖拽图片到此处或点击上传</p>
          <p className="text-xs text-text-light mt-1">支持 JPG, PNG, WebP</p>
        </>
      )}
      {loading && (
        <div className="mt-3 flex justify-center">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
