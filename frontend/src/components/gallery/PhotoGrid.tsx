import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';
import type { useSelection } from '../../hooks/useSelection';

interface PhotoGridProps {
  items: MediaItem[];
  onItemClick: (id: number) => void;
  selection?: ReturnType<typeof useSelection> | null;
}

export default function PhotoGrid({ items, onItemClick, selection }: PhotoGridProps) {
  const sel = selection;
  const selectMode = sel?.selectMode ?? false;

  if (items.length === 0) {
    return <p className="text-center text-text-light py-8">暂无结果</p>;
  }

  return (
    <div className={`grid grid-cols-3 md:grid-cols-5 gap-2 ${selectMode ? 'mt-12 mb-28' : ''}`}>
      {items.map((item) => {
        const isSel = sel?.isSelected(item.id) ?? false;
        return (
          <div
            key={item.id}
            className={`aspect-square rounded-card overflow-hidden bg-misty relative group transition-all ${
              selectMode
                ? isSel
                  ? 'cursor-pointer ring-2 ring-primary ring-offset-1'
                  : 'cursor-pointer opacity-50'
                : 'cursor-pointer hover:opacity-90'
            }`}
            onClick={() => sel?.handleItemClick(item.id, () => onItemClick(item.id))}
            onPointerDown={() => sel?.onPointerDown(item.id)}
            onPointerUp={sel?.onPointerUp}
          >
            {item.thumbnail_path ? (
              <img
                src={api.thumbUrl(item.thumbnail_path)}
                alt={item.filename}
                className="w-full h-full object-cover"
                loading="lazy"
                draggable={false}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-2xl">📷</div>
            )}

            {/* Selection indicator */}
            {selectMode && (
              <div className={`absolute top-1.5 left-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                isSel ? 'bg-primary border-primary text-white' : 'bg-black/30 border-white'
              }`}>
                {isSel && <span className="text-[10px] leading-none">✓</span>}
              </div>
            )}

            {!selectMode && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/50 to-transparent p-2">
                <span className="text-white text-[10px]">{item.date_taken?.slice(0, 10)}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
