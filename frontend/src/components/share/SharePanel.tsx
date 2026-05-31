import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../api/client';

interface SharePanelProps {
  open: boolean;
  onClose: () => void;
  mediaIds: number[];
}

const EXPIRY_OPTIONS = [
  { label: '1小时', value: 1 },
  { label: '24小时', value: 24 },
  { label: '7天', value: 168 },
  { label: '永久', value: 0 },
];

export default function SharePanel({ open, onClose, mediaIds }: SharePanelProps) {
  const [title, setTitle] = useState('');
  const [expiry, setExpiry] = useState(24);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (open) {
      setTitle('');
      setExpiry(24);
      setShareUrl(null);
      setCopied(false);
    }
  }, [open]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const result = await api.createShare(
        mediaIds,
        title.trim() || undefined,
        expiry === 0 ? undefined : expiry,
      );
      const fullUrl = `${window.location.origin}${result.url}`;
      setShareUrl(fullUrl);
    } catch (err) {
      alert('创建分享失败: ' + (err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      alert('复制失败，请手动复制');
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
            className="fixed bottom-0 left-0 right-0 z-[80] bg-white rounded-t-2xl max-h-[70vh] flex flex-col md:ml-14"
          >
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>

            <h3 className="px-4 py-2 text-base font-semibold text-text">
              分享照片 ({mediaIds.length} 张)
            </h3>

            <div className="flex-1 overflow-y-auto px-4 pb-6">
              {!shareUrl ? (
                <>
                  <div className="mb-4">
                    <label className="text-xs text-text-light mb-1 block">标题（可选）</label>
                    <input
                      value={title}
                      onChange={e => setTitle(e.target.value)}
                      placeholder="给这次分享起个名字"
                      className="w-full px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary"
                    />
                  </div>

                  <div className="mb-4">
                    <label className="text-xs text-text-light mb-2 block">有效期</label>
                    <div className="flex gap-2">
                      {EXPIRY_OPTIONS.map(opt => (
                        <button
                          key={opt.value}
                          onClick={() => setExpiry(opt.value)}
                          className={`flex-1 py-2 rounded-btn text-sm font-medium transition-colors ${
                            expiry === opt.value
                              ? 'bg-primary text-white'
                              : 'bg-misty text-text'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={handleCreate}
                    disabled={creating}
                    className="w-full py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    {creating ? '创建中...' : '创建分享链接'}
                  </button>
                </>
              ) : (
                <>
                  <p className="text-sm text-text-light mb-3">分享链接已生成：</p>
                  <div className="flex gap-2 mb-3">
                    <input
                      readOnly
                      value={shareUrl}
                      className="flex-1 px-3 py-2 border border-misty rounded-btn text-xs outline-none bg-misty/30"
                    />
                    <button
                      onClick={handleCopy}
                      className={`px-4 py-2 rounded-btn text-sm font-medium transition-colors ${
                        copied ? 'bg-green-100 text-green-700' : 'bg-primary text-white'
                      }`}
                    >
                      {copied ? '已复制 ✓' : '复制'}
                    </button>
                  </div>
                  <p className="text-xs text-text-light">
                    局域网内其他设备打开此链接即可查看照片
                  </p>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
