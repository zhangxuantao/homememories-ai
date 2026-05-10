import type { TimelineEvent, MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface EventStripProps {
  event: TimelineEvent;
  media: MediaItem[];
  onPhotoClick: (mediaId: number) => void;
}

export default function EventStrip({ event, media, onPhotoClick }: EventStripProps) {
  return (
    <div className="glass-card rounded-card p-3.5">
      <div className="flex items-center justify-between mb-2.5">
        <div>
          <h3 className="text-sm font-semibold text-text">{event.title}</h3>
          <p className="text-xs text-text-light mt-0.5">{event.media_count} 张照片</p>
        </div>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {media.slice(0, 15).map((m) => (
          <button
            key={m.id}
            onClick={() => onPhotoClick(m.id)}
            className="flex-shrink-0 w-[70px] h-[70px] rounded-lg overflow-hidden bg-misty cursor-pointer hover:ring-2 hover:ring-primary transition-all"
          >
            {m.thumbnail_path ? (
              <img src={api.thumbUrl(m.thumbnail_path)} alt="" className="w-full h-full object-cover" loading="lazy" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xl">{m.media_type === 'video' ? '🎬' : '📷'}</div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
