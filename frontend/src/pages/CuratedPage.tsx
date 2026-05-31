import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api, type MediaItem } from '../api/client';

interface MonthlyCuration {
  month: string;
  items: MediaItem[];
}

export default function CuratedPage() {
  const navigate = useNavigate();
  const [curations, setCurations] = useState<MonthlyCuration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const months: string[] = [];
    const now = new Date();
    for (let i = 0; i < 6; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
    }

    Promise.all(months.map(m => api.getCuration(m).catch(() => ({ month: m, items: [] }))))
      .then(results => setCurations(results.filter(c => c.items.length > 0)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (curations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">✨</span>
        <p className="text-lg text-text font-semibold mb-2">还没有精选集</p>
        <p className="text-sm text-text-light">去设置页生成精选集吧</p>
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
        ✨ 精选集
      </motion.h1>

      {curations.map(c => (
        <section key={c.month} className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">
            {c.month.replace('-', '年')}月 · {c.items.length} 张精选
          </h2>
          <div className="flex gap-2 overflow-x-auto scrollbar-none pb-1">
            {c.items.map(item => (
              <div
                key={item.id}
                className="flex-shrink-0 w-24 h-24 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => navigate(`/photo/${item.id}`, { state: { from: '/curated' } })}
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
      ))}
    </div>
  );
}
