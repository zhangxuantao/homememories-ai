import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAlbums } from '../hooks/useAlbums';
import { api } from '../api/client';

export default function AlbumsPage() {
  const navigate = useNavigate();
  const { albums, loading, refresh } = useAlbums();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [menuAlbumId, setMenuAlbumId] = useState<number | null>(null);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    try {
      const album = await api.createAlbum(name);
      setNewName('');
      setShowCreate(false);
      navigate(`/albums/${album.id}`);
    } catch (err) {
      alert('创建失败: ' + (err as Error).message);
    }
  };

  const handleRename = async (id: number) => {
    const name = prompt('新名称:');
    if (!name) return;
    try {
      await api.updateAlbum(id, { name });
      refresh();
    } catch (err) {
      alert('重命名失败: ' + (err as Error).message);
    }
    setMenuAlbumId(null);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`确定删除相册「${name}」？照片不会被删除。`)) return;
    try {
      await api.deleteAlbum(id);
      refresh();
    } catch (err) {
      alert('删除失败: ' + (err as Error).message);
    }
    setMenuAlbumId(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!loading && albums.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">📁</span>
        <p className="text-lg text-text font-semibold mb-2">还没有相册哦</p>
        <p className="text-sm text-text-light mb-6">创建相册，手动整理你的照片吧</p>
        {!showCreate ? (
          <button
            onClick={() => setShowCreate(true)}
            className="px-6 py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity"
          >
            创建第一个相册
          </button>
        ) : (
          <div className="flex gap-2">
            <input
              autoFocus
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              placeholder="相册名称"
              className="px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary"
            />
            <button onClick={handleCreate} className="px-4 py-2 bg-primary text-white rounded-btn text-sm font-medium">创建</button>
            <button onClick={() => { setShowCreate(false); setNewName(''); }} className="px-4 py-2 text-text-light text-sm">取消</button>
          </div>
        )}
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
          📁 我的相册
        </motion.h1>

        <button
          onClick={() => {
            setShowCreate(!showCreate);
            setNewName('');
            setMenuAlbumId(null);
          }}
          className="w-9 h-9 flex items-center justify-center rounded-full bg-primary text-white text-lg hover:opacity-90 transition-opacity"
        >
          +
        </button>
      </div>

      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden mb-4"
          >
            <div className="flex gap-2 p-3 bg-misty/30 rounded-card">
              <input
                autoFocus
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreate()}
                placeholder="输入相册名称"
                className="flex-1 px-3 py-2 border border-misty rounded-btn text-sm outline-none focus:border-primary bg-white"
              />
              <button onClick={handleCreate} className="px-4 py-2 bg-primary text-white rounded-btn text-sm font-medium">创建</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {albums.map(album => (
          <div key={album.id} className="relative group">
            <div
              className="rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-90 transition-opacity"
              onClick={() => navigate(`/albums/${album.id}`)}
              onContextMenu={e => { e.preventDefault(); setMenuAlbumId(menuAlbumId === album.id ? null : album.id); }}
            >
              <div className="aspect-[4/3]">
                {album.cover_thumbnail ? (
                  <img
                    src={api.thumbUrl(album.cover_thumbnail)}
                    alt={album.name}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl">📁</div>
                )}
              </div>
              <div className="p-2.5">
                <p className="text-sm font-medium text-text truncate">{album.name}</p>
                <p className="text-xs text-text-light mt-0.5">{album.media_count} 张照片</p>
              </div>
            </div>

            {/* Context menu */}
            <AnimatePresence>
              {menuAlbumId === album.id && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="absolute top-2 right-2 bg-white rounded-card shadow-lg border border-misty py-1 z-10"
                >
                  <button
                    onClick={() => handleRename(album.id)}
                    className="block w-full text-left px-3 py-1.5 text-sm text-text hover:bg-misty/50"
                  >
                    重命名
                  </button>
                  <button
                    onClick={() => handleDelete(album.id, album.name)}
                    className="block w-full text-left px-3 py-1.5 text-sm text-red-500 hover:bg-misty/50"
                  >
                    删除
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
}
