interface SelectionActionsProps {
  onAddToAlbum: () => void;
  onDownload: () => void;
  onDelete: () => void;
}

export default function SelectionActions({ onAddToAlbum, onDownload, onDelete }: SelectionActionsProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 flex justify-around items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
      <button
        onClick={onAddToAlbum}
        className="flex flex-col items-center gap-1 text-sm text-text hover:text-primary transition-colors"
      >
        <span className="text-xl">📁</span>
        <span className="text-[10px]">加入相册</span>
      </button>
      <button
        onClick={onDownload}
        className="flex flex-col items-center gap-1 text-sm text-text hover:text-primary transition-colors"
      >
        <span className="text-xl">⬇️</span>
        <span className="text-[10px]">下载</span>
      </button>
      <button
        onClick={onDelete}
        className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors"
      >
        <span className="text-xl">🗑️</span>
        <span className="text-[10px]">删除</span>
      </button>
    </div>
  );
}
