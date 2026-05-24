interface SelectionBarProps {
  count: number;
  onSelectAll: () => void;
  onClearAll: () => void;
  onExit: () => void;
}

export default function SelectionBar({ count, onSelectAll, onClearAll, onExit }: SelectionBarProps) {
  return (
    <div className="fixed top-0 left-0 right-0 z-[60] flex items-center justify-between px-4 h-12 bg-white/95 backdrop-blur-md border-b border-misty md:ml-14">
      <button onClick={onExit} className="text-sm text-primary font-medium">
        &larr; 取消
      </button>
      <span className="text-sm font-semibold text-text">已选 {count} 项</span>
      <button onClick={onSelectAll} className="text-sm text-primary font-medium">
        全选
      </button>
    </div>
  );
}
