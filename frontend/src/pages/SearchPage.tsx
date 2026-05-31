import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTextSearch, useImageSearch } from '../hooks/useSearch';
import { useSelection } from '../hooks/useSelection';
import SearchBar from '../components/ui/SearchBar';
import ImageUploader from '../components/ui/ImageUploader';
import PhotoGrid from '../components/gallery/PhotoGrid';
import SelectionBar from '../components/gallery/SelectionBar';
import SelectionActions from '../components/gallery/SelectionActions';
import { api } from '../api/client';
import AlbumPickerSheet from '../components/albums/AlbumPickerSheet';
import SharePanel from '../components/share/SharePanel';
import CollagePanel from '../components/share/CollagePanel';

type SearchMode = 'text' | 'image';

export default function SearchPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<SearchMode>('text');
  const textSearch = useTextSearch();
  const imageSearch = useImageSearch();
  const selection = useSelection();

  const [albumPickerOpen, setAlbumPickerOpen] = useState(false);
  const [pendingAlbumIds, setPendingAlbumIds] = useState<number[]>([]);

  const [shareOpen, setShareOpen] = useState(false);
  const [collageOpen, setCollageOpen] = useState(false);
  const [pendingActionIds, setPendingActionIds] = useState<number[]>([]);

  const recentSearches: string[] = JSON.parse(localStorage.getItem('recentSearches') || '[]');

  const currentResults = mode === 'text' ? textSearch.results : imageSearch.results;
  const currentLoading = mode === 'text' ? textSearch.loading : imageSearch.loading;

  const handleBatchDelete = async () => {
    const ids = Array.from(selection.selectedIds);
    if (!confirm(`确定删除这 ${ids.length} 张照片？此操作不可恢复。`)) return;
    for (const id of ids) {
      try { await api.delete(`/api/media/${id}`); } catch {}
    }
    selection.exitSelectMode();
  };

  const handleBatchDownload = async () => {
    const ids = Array.from(selection.selectedIds);
    if (ids.length <= 5) {
      ids.forEach(id => window.open(api.originalUrl(id), '_blank'));
    } else {
      try {
        const res = await fetch(`${window.location.origin}/api/media/export-zip`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(ids),
        });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'homememories_export.zip';
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        alert('下载失败: ' + (err as Error).message);
      }
    }
    selection.exitSelectMode();
  };

  const handleAddToAlbum = () => {
    const ids = Array.from(selection.selectedIds);
    setPendingAlbumIds(ids);
    setAlbumPickerOpen(true);
  };

  const handleShare = () => {
    const ids = Array.from(selection.selectedIds);
    setPendingActionIds(ids);
    setShareOpen(true);
  };

  const handleCollage = () => {
    const ids = Array.from(selection.selectedIds);
    if (ids.length < 2 || ids.length > 9) {
      alert('拼图需要选择 2-9 张照片');
      return;
    }
    setPendingActionIds(ids);
    setCollageOpen(true);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-4">搜索</h1>

      <div className="flex gap-2 mb-4">
        {(['text', 'image'] as SearchMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
              mode === m ? 'bg-primary text-white' : 'bg-misty text-text'
            }`}
          >
            {m === 'text' ? '文字搜索' : '图片搜索'}
          </button>
        ))}
      </div>

      {mode === 'text' ? (
        <>
          <SearchBar onSearch={textSearch.search} loading={textSearch.loading} />
          {recentSearches.length > 0 && !currentResults && (
            <div className="mt-4">
              <p className="text-xs text-text-light mb-2">最近搜索</p>
              <div className="flex flex-wrap gap-2">
                {recentSearches.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => textSearch.search(s)}
                    className="px-3 py-1 rounded-pill bg-misty text-text text-xs hover:bg-primary/20 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <ImageUploader onUpload={imageSearch.search} loading={imageSearch.loading} />
      )}

      {(textSearch.error || imageSearch.error) && (
        <p className="text-red-400 text-sm mt-4 text-center">
          {mode === 'text' ? textSearch.error : imageSearch.error}
        </p>
      )}

      {currentResults && (
        <div className="mt-6">
          <p className="text-sm text-text-light mb-3">
            找到 {currentResults.results.length} 个结果
          </p>
          {selection.selectMode && (
            <>
              <SelectionBar
                count={selection.selectedCount}
                onSelectAll={() => selection.selectAll(currentResults.results.map(r => r.id))}
                onClearAll={() => selection.selectAll([])}
                onExit={selection.exitSelectMode}
              />
              <SelectionActions
                onAddToAlbum={handleAddToAlbum}
                onShare={handleShare}
                onCollage={handleCollage}
                onDownload={handleBatchDownload}
                onDelete={handleBatchDelete}
              />
            </>
          )}
          <PhotoGrid
            items={currentResults.results}
            onItemClick={(id) => navigate(`/photo/${id}`, { state: { from: '/search' } })}
            selection={selection}
          />
        </div>
      )}

      {currentLoading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      <AlbumPickerSheet
        open={albumPickerOpen}
        onClose={() => setAlbumPickerOpen(false)}
        mediaIds={pendingAlbumIds}
        onDone={() => selection.exitSelectMode()}
      />

      <SharePanel open={shareOpen} onClose={() => setShareOpen(false)} mediaIds={pendingActionIds} />
      <CollagePanel open={collageOpen} onClose={() => setCollageOpen(false)} mediaIds={pendingActionIds} />
    </div>
  );
}
