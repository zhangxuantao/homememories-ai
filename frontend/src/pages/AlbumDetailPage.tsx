// frontend/src/pages/AlbumDetailPage.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api, type Album, type MediaItem } from '../api/client';
import { useSelection } from '../hooks/useSelection';
import { useAlbumMedia } from '../hooks/useAlbums';
import SelectionBar from '../components/gallery/SelectionBar';

export default function AlbumDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const albumId = Number(id);
  const [album, setAlbum] = useState<Album | null>(null);
  const { items, loading, refresh } = useAlbumMedia(albumId);
  const selection = useSelection();

  useEffect(() => {
    api.getAlbum(albumId).then(setAlbum).catch(() => navigate('/albums'));
  }, [albumId, navigate]);

  const handleRemoveFromAlbum = async () => {
    const ids = Array.from(selection.selectedIds);
    if (!confirm(`从相册中移除这 ${ids.length} 张照片？`)) return;
    try {
      await api.removeFromAlbum(albumId, ids);
      selection.exitSelectMode();
      refresh();
    } catch (err) {
      alert('操作失败: ' + (err as Error).message);
    }
  };

  const handleDeleteAlbum = async () => {
    if (!album) return;
    if (!confirm(`确定删除相册「${album.name}」？照片不会被删除。`)) return;
    try {
      await api.deleteAlbum(albumId);
      navigate('/albums');
    } catch (err) {
      alert('删除失败: ' + (err as Error).message);
    }
  };

  const handleRename = async () => {
    if (!album) return;
    const name = prompt('新名称:', album.name);
    if (!name) return;
    try {
      const updated = await api.updateAlbum(albumId, { name });
      setAlbum(updated);
    } catch (err) {
      alert('重命名失败: ' + (err as Error).message);
    }
  };

  const handleSetCover = async (mediaId: number) => {
    try {
      const updated = await api.updateAlbum(albumId, { cover_media_id: mediaId });
      setAlbum(updated);
    } catch (err) {
      alert('设置封面失败: ' + (err as Error).message);
    }
  };

  const handleAddPhotos = () => {
    navigate('/search');
  };

  if (!album) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      {/* Back button */}
      <button
        onClick={() => navigate('/albums')}
        className="flex items-center gap-1 text-sm text-text-light hover:text-text mb-4 transition-colors"
      >
        <span>&larr;</span> 返回相册列表
      </button>

      {/* Hero */}
      <div className="relative rounded-card overflow-hidden mb-6 aspect-[3/1] bg-misty">
        {album.cover_thumbnail ? (
          <img
            src={api.thumbUrl(album.cover_thumbnail)}
            alt={album.name}
            className="w-full h-full object-cover blur-sm scale-110"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-6xl">{'\uD83D\uDCC1'}</div>
        )}
        <div className="absolute inset-0 bg-black/30 flex items-end p-4">
          <div>
            <h1 className="text-xl font-bold text-white">{album.name}</h1>
            <p className="text-sm text-white/70">{album.media_count} 张照片</p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="absolute top-3 right-3 flex gap-1.5">
          <button
            onClick={handleAddPhotos}
            className="px-3 py-1.5 bg-white/90 text-text text-xs rounded-btn font-medium hover:bg-white transition-colors"
          >
            + 添加照片
          </button>
          <button
            onClick={handleRename}
            className="px-3 py-1.5 bg-white/90 text-text text-xs rounded-btn font-medium hover:bg-white transition-colors"
          >
            重命名
          </button>
          <button
            onClick={handleDeleteAlbum}
            className="px-3 py-1.5 bg-white/90 text-red-500 text-xs rounded-btn font-medium hover:bg-white transition-colors"
          >
            删除
          </button>
        </div>
      </div>

      {/* Selection bar */}
      {selection.selectMode && (
        <SelectionBar
          count={selection.selectedCount}
          onSelectAll={() => selection.selectAll(items.map(i => i.id))}
          onClearAll={() => selection.selectAll([])}
          onExit={selection.exitSelectMode}
        />
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
          <span className="text-5xl mb-4">{'\uD83D\uDCC1'}</span>
          <p className="text-lg text-text font-semibold mb-2">相册还是空的</p>
          <p className="text-sm text-text-light mb-6">去搜索页面选中照片加入此相册</p>
          <button
            onClick={() => navigate('/search')}
            className="px-6 py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity"
          >
            去搜索
          </button>
        </div>
      )}

      {/* Masonry grid */}
      {!loading && items.length > 0 && (
        <div
          className="columns-2 md:columns-4 gap-2"
          style={selection.selectMode ? { marginTop: '3rem', marginBottom: '3.5rem' } : undefined}
        >
          {items.map(item => {
            const isSel = selection.isSelected(item.id);
            return (
              <div
                key={item.id}
                className={`break-inside-avoid mb-2 rounded-card overflow-hidden bg-misty relative group cursor-pointer transition-all ${
                  selection.selectMode
                    ? isSel
                      ? 'ring-2 ring-primary ring-offset-1'
                      : 'opacity-50'
                    : 'hover:opacity-90'
                }`}
                onClick={() =>
                  selection.handleItemClick(item.id, () =>
                    navigate(`/photo/${item.id}`, { state: { from: `/albums/${albumId}` } })
                  )
                }
                onPointerDown={() => selection.onPointerDown(item.id)}
                onPointerUp={selection.onPointerUp}
                onContextMenu={e => {
                  if (!selection.selectMode) {
                    e.preventDefault();
                    handleSetCover(item.id);
                  }
                }}
              >
                {item.thumbnail_path ? (
                  <img
                    src={api.thumbUrl(item.thumbnail_path)}
                    alt={item.filename}
                    className="w-full h-auto"
                    loading="lazy"
                    draggable={false}
                  />
                ) : (
                  <div className="w-full aspect-square flex items-center justify-center text-3xl">{'\uD83D\uDCF7'}</div>
                )}

                {selection.selectMode && (
                  <div className={`absolute top-1.5 left-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                    isSel ? 'bg-primary border-primary text-white' : 'bg-black/30 border-white'
                  }`}>
                    {isSel && <span className="text-[10px] leading-none">&check;</span>}
                  </div>
                )}

                {!selection.selectMode && (
                  <button
                    onClick={e => { e.stopPropagation(); handleSetCover(item.id); }}
                    className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-black/40 text-white text-[10px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                    title="设为封面"
                  >
                    &#11088;
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Bottom action bar in selection mode */}
      {selection.selectMode && (
        <div className="fixed bottom-0 left-0 right-0 z-[60] flex justify-around items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
          <button
            onClick={handleRemoveFromAlbum}
            className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors"
          >
            <span className="text-xl">{'\uD83D\uDCE4'}</span>
            <span className="text-[10px]">从相册移除 ({selection.selectedCount})</span>
          </button>
        </div>
      )}
    </div>
  );
}
