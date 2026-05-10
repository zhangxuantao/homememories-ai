import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface LightboxProps {
  item: MediaItem;
  onClose: () => void;
  onPrev: (() => void) | null;
  onNext: (() => void) | null;
  onNavigate?: (id: number) => void;
}

export default function Lightbox({ item, onClose, onPrev, onNext, onNavigate }: LightboxProps) {
  const [displayUrl, setDisplayUrl] = useState(() => api.originalUrl(item.path));
  const [useThumb, setUseThumb] = useState(false);
  const [showSimilar, setShowSimilar] = useState(false);
  const [similarItems, setSimilarItems] = useState<MediaItem[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  // Reset when item changes
  useEffect(() => {
    setDisplayUrl(api.originalUrl(item.path));
    setUseThumb(false);
    setShowSimilar(false);
    setSimilarItems([]);
  }, [item.id]);

  const handleShowSimilar = useCallback(async () => {
    if (showSimilar) {
      setShowSimilar(false);
      return;
    }
    setShowSimilar(true);
    if (similarItems.length === 0) {
      setLoadingSimilar(true);
      try {
        const items = await api.get<MediaItem[]>(`/api/media/${item.id}/similar`, { limit: 12 });
        setSimilarItems(items);
      } catch {
        setSimilarItems([]);
      } finally {
        setLoadingSimilar(false);
      }
    }
  }, [showSimilar, similarItems.length, item.id]);

  const handleImgError = () => {
    const thumb = api.thumbUrl(item.thumbnail_path);
    if (thumb && !useThumb) {
      setDisplayUrl(thumb);
      setUseThumb(true);
    }
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft' && onPrev) onPrev();
      if (e.key === 'ArrowRight' && onNext) onNext();
    };
    window.addEventListener('keydown', handler);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handler);
      document.body.style.overflow = '';
    };
  }, [onClose, onPrev, onNext]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] bg-black/90 flex flex-col"
        onClick={onClose}
      >
        <div className="flex items-center justify-between px-4 py-3 text-white text-sm">
          <button onClick={onClose} className="hover:text-primary transition-colors">✕ 关闭</button>
          <div className="flex items-center gap-4">
            <button
              onClick={handleShowSimilar}
              className={`hover:text-primary transition-colors ${showSimilar ? 'text-primary' : ''}`}
            >
              {showSimilar ? '隐藏相似' : '相似照片'}
            </button>
            <a
              href={displayUrl}
              download={item.filename}
              className="hover:text-primary transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              下载
            </a>
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center" onClick={(e) => e.stopPropagation()}>
          {onPrev && (
            <button
              onClick={onPrev}
              className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/10 text-white text-xl hover:bg-white/20 transition-colors flex items-center justify-center"
            >
              ‹
            </button>
          )}

          <img
            src={displayUrl}
            alt={item.filename}
            className="max-w-full max-h-[80vh] object-contain select-none"
            draggable={false}
            onError={handleImgError}
          />

          {onNext && (
            <button
              onClick={onNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/10 text-white text-xl hover:bg-white/20 transition-colors flex items-center justify-center"
            >
              ›
            </button>
          )}
        </div>

        {showSimilar && (
          <div className="px-4" onClick={(e) => e.stopPropagation()}>
            {loadingSimilar ? (
              <div className="flex items-center gap-2 py-2 text-white/60 text-sm">
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                查找相似照片...
              </div>
            ) : similarItems.length === 0 ? (
              <p className="py-2 text-white/50 text-sm">暂无相似照片</p>
            ) : (
              <div className="flex gap-2 overflow-x-auto py-2 scrollbar-thin">
                {similarItems.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => onNavigate?.(s.id)}
                    className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden bg-white/10 hover:ring-2 hover:ring-primary transition-all"
                  >
                    <img
                      src={api.thumbUrl(s.thumbnail_path)}
                      alt={s.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="px-4 py-3 text-white text-sm bg-gradient-to-t from-black/60 to-transparent">
          {item.date_taken && (
            <p className="text-white/80">{item.date_taken.slice(0, 10)}</p>
          )}
          <p className="text-white/50 text-xs mt-0.5">
            {item.width}×{item.height} · {item.filename}
            {useThumb && ' (缩略图)'}
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
