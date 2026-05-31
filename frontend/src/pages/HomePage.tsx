import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOnThisDay, useRandomMedia } from '../hooks/useMedia';
import { api, MediaItem } from '../api/client';
import { useRecentFavorites } from '../hooks/useFavorites';

const today = new Date();

export default function HomePage() {
  const navigate = useNavigate();
  const onThisDay = useOnThisDay(today.getMonth() + 1, today.getDate());
  const randomFirst = useRandomMedia(4);
  const randomSecond = useRandomMedia(4);
  const randomItems = useMemo(() => {
    const ids = new Set<number>();
    const combined = [...(randomFirst.data || []), ...(randomSecond.data || [])];
    return combined
      .filter((item) => {
        if (ids.has(item.id)) return false;
        ids.add(item.id);
        return true;
      })
      .slice(0, 4);
  }, [randomFirst.data, randomSecond.data]);

  const { items: recentFavs } = useRecentFavorites(6);

  const [curated, setCurated] = useState<MediaItem[]>([]);
  useEffect(() => {
    const month = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`;
    api.getCuration(month)
      .then(data => setCurated(data.items || []))
      .catch(() => setCurated([]));
  }, []);

  const onThisDayItems = onThisDay.data || [];
  const hasOnThisDay = onThisDayItems.length > 0;
  const hasRandom = randomItems.length > 0;
  const hasRecentFavs = recentFavs.length > 0;
  const isEmpty = !hasOnThisDay && !hasRandom && !onThisDay.loading && !randomFirst.loading;

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">🖼️</span>
        <p className="text-lg text-text font-semibold mb-2">还没有照片哦</p>
        <p className="text-sm text-text-light mb-6">去设置页扫描吧~</p>
        <button
          onClick={() => navigate('/settings')}
          className="px-6 py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity"
        >
          去设置
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
        <div className="flex justify-between items-center mb-6">
          <motion.h1
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-bold text-text"
          >
            家庭回忆
          </motion.h1>
          <Link
            to="/settings"
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-misty transition-colors text-lg"
            title="设置"
          >
            ⚙️
          </Link>
        </div>

      {/* Section 1: 去年今天 — horizontal swipe, one large image at a time */}
      {hasOnThisDay && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">去年今天</h2>
          <div className="flex overflow-x-auto snap-x snap-mandatory scrollbar-none -mx-4 px-4">
            {onThisDayItems.map((item) => (
              <div
                key={item.id}
                className="flex-shrink-0 w-full snap-center pr-2 last:pr-0 cursor-pointer"
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
              >
                <div className="rounded-card overflow-hidden bg-misty aspect-[4/3]">
                  {item.thumbnail_path ? (
                    <img
                      src={api.thumbUrl(item.thumbnail_path)}
                      alt={item.filename}
                      className="w-full h-full object-contain bg-black/5"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-4xl">📷</div>
                  )}
                </div>
                <p className="text-xs text-text-light mt-1.5 truncate">
                  {item.date_taken?.slice(0, 10)} · {item.filename}
                </p>
              </div>
            ))}

          </div>

          {onThisDayItems.length > 1 && (
            <div className="flex justify-center gap-1.5 mt-3">
              {onThisDayItems.map((_, i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-misty data-[active]:bg-primary"
                />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Section 2: 随机回忆 — small thumbnail grid */}
      {hasRandom && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">随机回忆</h2>
          <div className="grid grid-cols-2 gap-2">
            {randomItems.map((item) => (
              <div
                key={item.id}
                className="aspect-square rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-90 transition-opacity"
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
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
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Section 2.5: 最近收藏 */}
      {hasRecentFavs && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3 flex justify-between items-center">
            <span>❤️ 最近收藏</span>
            <button
              onClick={() => navigate('/favorites')}
              className="text-xs text-primary font-normal hover:underline"
            >
              查看全部 →
            </button>
          </h2>
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
            {recentFavs.map((item) => (
              <div
                key={item.id}
                className="flex-shrink-0 w-20 h-20 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
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
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 本月精选 */}
      {curated.length > 0 && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3 flex justify-between items-center">
            <span>✨ 本月精选</span>
            <button
              onClick={() => navigate('/curated')}
              className="text-xs text-primary font-normal hover:underline"
            >
              查看全部 →
            </button>
          </h2>
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
            {curated.slice(0, 10).map((item) => (
              <div
                key={item.id}
                className="flex-shrink-0 w-24 h-24 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
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
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Section 3: 最近添加 — horizontal strip */}
      {hasRandom && (
        <section>
          <h2 className="text-base font-semibold text-text mb-3">最近添加</h2>
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
            {[...randomItems].reverse().slice(0, 10).map((item) => (
              <div
                key={item.id}
                className="flex-shrink-0 w-20 h-20 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
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
              </div>
            ))}
          </div>
        </section>
      )}

      {(onThisDay.loading || randomFirst.loading) && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
