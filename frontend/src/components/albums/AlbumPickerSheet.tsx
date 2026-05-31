import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, type Album } from '../../api/client';

interface AlbumPickerSheetProps {
  open: boolean;
  onClose: () => void;
  mediaIds: number[];
  onDone: () => void;
}

export default function AlbumPickerSheet({ open, onClose, mediaIds, onDone }: AlbumPickerSheetProps) {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (open) {
      setLoading(true);
      api.listAlbums().then(setAlbums).finally(() => setLoading(false));
      setNewName('');
    }
  }, [open]);

  const handleAdd = async (albumId: number, albumName: string) => {
    setAdding(true);
    try {
      await api.addToAlbum(albumId, mediaIds);
      alert(`已添加 ${mediaIds.length} 张到「${albumName}」`);
      onDone();
      onClose();
    } catch (err) {
      alert('添加失败: ' + (err as Error).message);
    } finally {
      setAdding(false);
    }
  };

  const handleCreateAndAdd = async () => {
    const name = newName.trim();
    if (!name) return;
    setAdding(true);
    try {
      const album = await api.createAlbum(name);
      await api.addToAlbum(album.id, mediaIds);
      alert(`已创建「${name}」并添加 ${mediaIds.length} 张照片`);
      onDone();
      onClose();
    } catch (err) {
      alert('操作失败: ' + (err as Error).message);
    } finally {
      setAdding(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[70] bg-black/40"
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-[80] bg-white rounded-t-2xl max-h-[60vh] flex flex-col md:ml-14"
          >
            {/* Handle */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-gray-300" />
            </div>

            <h3 className="px-4 py-2 text-base font-semibold text-text">
              加入相册 ({mediaIds.length} 张)
            </h3>

            {/* Create new */}
            <div className="px-4 pb-3 flex gap-2">
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreateAndAdd()}
                placeholder="新建相册..."
                className="flex-1 px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary"
                disabled={adding}
              />
              <button
                onClick={handleCreateAndAdd}
                disabled={!newName.trim() || adding}
                className="px-4 py-2 bg-primary text-white rounded-btn text-sm font-medium disabled:opacity-50"
              >
                创建
              </button>
            </div>

            {/* Album list */}
            <div className="flex-1 overflow-y-auto px-4 pb-6">
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : albums.length === 0 ? (
                <p className="text-center text-text-light py-8 text-sm">暂无相册，在上面新建一个</p>
              ) : (
                <div className="space-y-1">
                  {albums.map(album => (
                    <button
                      key={album.id}
                      onClick={() => handleAdd(album.id, album.name)}
                      disabled={adding}
                      className="w-full flex items-center gap-3 p-2.5 rounded-btn hover:bg-misty/50 transition-colors text-left"
                    >
                      <div className="w-12 h-12 rounded-lg bg-misty flex-shrink-0 overflow-hidden">
                        {album.cover_thumbnail ? (
                          <img
                            src={api.thumbUrl(album.cover_thumbnail)}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-xl">📁</div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text truncate">{album.name}</p>
                        <p className="text-xs text-text-light">{album.media_count} 张</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
