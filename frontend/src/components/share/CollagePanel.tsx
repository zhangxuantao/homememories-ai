import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../api/client';

interface CollagePanelProps {
  open: boolean;
  onClose: () => void;
  mediaIds: number[];
}

const LAYOUTS = [
  { label: '网格', value: 'grid', icon: '🔲' },
  { label: '横向', value: 'horizontal', icon: '↔️' },
  { label: '纵向', value: 'vertical', icon: '↕️' },
];

export default function CollagePanel({ open, onClose, mediaIds }: CollagePanelProps) {
  const [layout, setLayout] = useState('grid');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (open) {
      setLayout('grid');
    }
  }, [open]);

  const handleDownload = async () => {
    setGenerating(true);
    try {
      const blob = await api.createCollage(mediaIds, layout);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `collage_${Date.now()}.jpg`;
      a.click();
      URL.revokeObjectURL(url);
      onClose();
    } catch (err) {
      alert('生成拼图失败: ' + (err as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] bg-black/40"
            onClick={onClose}
          />

          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-[80] bg-white rounded-t-2xl flex flex-col md:ml-14"
          >
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>

            <h3 className="px-4 py-2 text-base font-semibold text-text">
              拼图 ({mediaIds.length} 张)
            </h3>

            <div className="px-4 pb-6">
              <label className="text-xs text-text-light mb-2 block">布局</label>
              <div className="flex gap-2 mb-4">
                {LAYOUTS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setLayout(opt.value)}
                    className={`flex-1 py-3 rounded-btn flex flex-col items-center gap-1 transition-colors ${
                      layout === opt.value
                        ? 'bg-primary/10 text-primary border border-primary'
                        : 'bg-misty text-text border border-transparent'
                    }`}
                  >
                    <span className="text-lg">{opt.icon}</span>
                    <span className="text-xs font-medium">{opt.label}</span>
                  </button>
                ))}
              </div>

              <button
                onClick={handleDownload}
                disabled={generating}
                className="w-full py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {generating ? '生成中...' : '下载拼图'}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
