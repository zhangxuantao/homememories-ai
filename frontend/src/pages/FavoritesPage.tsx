import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useFavorites } from '../hooks/useFavorites';
import { useSelection } from '../hooks/useSelection';
import PhotoGrid from '../components/gallery/PhotoGrid';
import SelectionBar from '../components/gallery/SelectionBar';
import { api } from '../api/client';

export default function FavoritesPage() {
  const navigate = useNavigate();
  const { items, loading, loadMore } = useFavorites();
  const selection = useSelection();

  const handleItemClick = (id: number) => {
    navigate(`/photo/${id}`, { state: { from: '/favorites' } });
  };

  const handleBatchUnfavorite = async () => {
    const ids = Array.from(selection.selectedIds);
    if (!confirm(`确定取消收藏这 ${ids.length} 张照片？`)) return;
    for (const id of ids) {
      try {
        await api.toggleFavorite(id);
      } catch {}
    }
    selection.exitSelectMode();
    window.location.reload();
  };

  if (loading && items.length === 0) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!loading && items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">❤️</span>
        <p className="text-lg text-text font-semibold mb-2">还没有收藏照片哦</p>
        <p className="text-sm text-text-light">在照片详情页点击 ♡ 即可收藏</p>
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
        ❤️ 我的收藏
      </motion.h1>

      {selection.selectMode && (
            <SelectionBar
              count={selection.selectedCount}
              onSelectAll={() => selection.selectAll(items.map(i => i.id))}
              onClearAll={() => selection.selectAll([])}
              onExit={selection.exitSelectMode}
            />
          )}
      <PhotoGrid items={items} onItemClick={handleItemClick} selection={selection} />

      {selection.selectMode && (
        <div className="fixed bottom-0 left-0 right-0 z-[60] flex justify-center items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
          <button
            onClick={handleBatchUnfavorite}
            className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors"
          >
            <span className="text-xl">💔</span>
            <span className="text-[10px]">取消收藏 ({selection.selectedIds.size})</span>
          </button>
        </div>
      )}

      {!loading && items.length >= 50 && (
        <div className="flex justify-center mt-6">
          <button
            onClick={loadMore}
            className="px-4 py-2 text-sm text-primary border border-primary rounded-btn hover:bg-primary hover:text-white transition-colors"
          >
            加载更多
          </button>
        </div>
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-6">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
