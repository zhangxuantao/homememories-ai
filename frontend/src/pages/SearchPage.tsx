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

type SearchMode = 'text' | 'image';

export default function SearchPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<SearchMode>('text');
  const textSearch = useTextSearch();
  const imageSearch = useImageSearch();
  const selection = useSelection();

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

  const handleAddToAlbum = async () => {
    try {
      const albums = await api.get<{id: number; name: string}[]>('/api/albums');
      const name = prompt('输入相册名称（已有相册：' + albums.map(a => a.name).join('、') + '）或新建:');
      if (!name) return;

      let albumId = albums.find(a => a.name === name)?.id;
      if (!albumId) {
        const created = await api.post<{id: number}>('/api/albums', { name });
        albumId = created.id;
      }

      const ids = Array.from(selection.selectedIds);
      await api.post(`/api/albums/${albumId}/media`, { media_ids: ids });
      alert(`已加入 ${ids.length} 张到「${name}」`);
    } catch (err) {
      alert('操作失败: ' + (err as Error).message);
    }
    selection.exitSelectMode();
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
    </div>
  );
}
