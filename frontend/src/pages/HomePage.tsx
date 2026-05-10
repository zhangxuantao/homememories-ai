import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOnThisDay, useRandomMedia } from '../hooks/useMedia';
import MemoryCard from '../components/cards/MemoryCard';
import { api } from '../api/client';

const today = new Date();

export default function HomePage() {
  const navigate = useNavigate();
  const onThisDay = useOnThisDay(today.getMonth() + 1, today.getDate());
  const randomFirst = useRandomMedia(4);
  const randomSecond = useRandomMedia(4);

  const randomItems = useMemo(() => {
    const ids = new Set<number>();
    const combined = [...(randomFirst.data || []), ...(randomSecond.data || [])];
    return combined.filter((item) => {
      if (ids.has(item.id)) return false;
      ids.add(item.id);
      return true;
    }).slice(0, 4);
  }, [randomFirst.data, randomSecond.data]);

  const hasOnThisDay = onThisDay.data && onThisDay.data.length > 0;
  const hasRandom = randomItems.length > 0;
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
      <motion.h1
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-text mb-6"
      >
        家庭回忆
      </motion.h1>

      {/* Section 1: 去年今天 */}
      {hasOnThisDay && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">去年今天</h2>
          {onThisDay.data!.slice(0, 3).map((item, i) => (
            <MemoryCard
              key={item.id}
              item={item}
              variant="hero"
              index={i}
              title={item.date_taken?.slice(0, 10)}
              subtitle={item.filename}
              onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
            />
          ))}
        </section>
      )}

      {/* Section 2: 随机回忆 */}
      {hasRandom && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">随机回忆</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {randomItems.map((item, i) => (
              <MemoryCard
                key={item.id}
                item={item}
                index={i}
                title={item.date_taken?.slice(0, 10)}
                subtitle={item.filename}
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/' } })}
              />
            ))}
          </div>
        </section>
      )}

      {/* Section 3: 最近添加 */}
      {hasRandom && (
        <section>
          <h2 className="text-base font-semibold text-text mb-3">最近添加</h2>
          <div className="flex gap-3 overflow-x-auto pb-2">
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
