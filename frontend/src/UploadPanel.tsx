import { useRef } from 'react';
import { useUpload } from './hooks/useUpload';

interface UploadPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function UploadPanel({ open, onClose }: UploadPanelProps) {
  const { selectedFiles, uploading, progress, currentFile, result, addFiles, removeFile, upload, reset } = useUpload();
  const inputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  const handleClose = () => {
    reset();
    onClose();
  };

  const isDone = result && progress === 100;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/40 backdrop-blur-sm" onClick={handleClose}>
      <div className="w-full md:max-w-md bg-white rounded-t-2xl md:rounded-2xl shadow-xl max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-misty">
          <h2 className="text-lg font-semibold text-text">上传照片/视频</h2>
          <button onClick={handleClose} className="text-text-light hover:text-text text-xl leading-none">&times;</button>
        </div>

        <div className="p-5 space-y-4">
          {/* Drop zone */}
          {selectedFiles.length === 0 && !isDone && (
            <div
              className="border-2 border-dashed border-misty rounded-xl p-8 text-center cursor-pointer hover:border-primary transition-colors"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files); }}
            >
              <p className="text-3xl mb-2">📷</p>
              <p className="text-text font-medium">点击或拖拽选择文件</p>
              <p className="text-xs text-text-light mt-1">支持 JPG/PNG/MP4/MOV，单次最多 100 张</p>
              <input
                ref={inputRef}
                type="file"
                multiple
                accept="image/*,video/*"
                className="hidden"
                onChange={(e) => e.target.files && addFiles(e.target.files)}
              />
            </div>
          )}

          {/* Selected files preview */}
          {selectedFiles.length > 0 && !isDone && (
            <>
              <p className="text-sm text-text">已选 {selectedFiles.length} 张</p>
              <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto">
                {selectedFiles.map((f, i) => (
                  <div key={i} className="relative aspect-square rounded-lg overflow-hidden bg-misty/50">
                    <img src={URL.createObjectURL(f)} alt={f.name} className="w-full h-full object-cover" />
                    <button
                      onClick={() => removeFile(i)}
                      className="absolute top-0.5 right-0.5 w-5 h-5 bg-black/50 text-white rounded-full text-xs flex items-center justify-center"
                    >&times;</button>
                  </div>
                ))}
              </div>
              {!uploading && (
                <button
                  onClick={() => inputRef.current?.click()}
                  className="text-sm text-primary hover:underline"
                >+ 继续添加</button>
              )}
              <input
                ref={inputRef}
                type="file"
                multiple
                accept="image/*,video/*"
                className="hidden"
                onChange={(e) => e.target.files && addFiles(e.target.files)}
              />
            </>
          )}

          {/* Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="w-full h-2 bg-misty rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-text-light text-center truncate">
                {currentFile ? `正在上传: ${currentFile}` : '上传中...'}
              </p>
            </div>
          )}

          {/* Done state */}
          {isDone && result && (
            <div className="text-center py-4 space-y-3">
              <p className="text-3xl">✅</p>
              <p className="text-text font-medium">
                {result.uploaded.length} 张已上传{result.failed.length > 0 ? `，${result.failed.length} 张失败` : ''}，后台处理中...
              </p>
              <button onClick={handleClose} className="inline-block px-5 py-2 bg-primary text-white rounded-btn text-sm">
                去查看
              </button>
            </div>
          )}

          {/* Action button */}
          {selectedFiles.length > 0 && !uploading && !isDone && (
            <button onClick={upload} className="w-full py-2.5 bg-primary text-white rounded-btn font-medium text-sm hover:opacity-90 transition-opacity">
              开始上传 ({selectedFiles.length} 张)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
