import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface PhotoGridProps {
  items: MediaItem[];
  onItemClick: (id: number) => void;
}

export default function PhotoGrid({ items, onItemClick }: PhotoGridProps) {
  if (items.length === 0) {
    return <p className="text-center text-text-light py-8">暂无结果</p>;
  }

  return (
    <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="aspect-square rounded-card overflow-hidden bg-misty cursor-pointer relative group hover:opacity-90 transition-opacity"
          onClick={() => onItemClick(item.id)}
        >
          {item.thumbnail_path ? (
            <img
              src={api.thumbUrl(item.thumbnail_path)}
              alt={item.filename}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl">📷</div>
          )}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/50 to-transparent p-2">
            <span className="text-white text-[10px]">{item.date_taken?.slice(0, 10)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
