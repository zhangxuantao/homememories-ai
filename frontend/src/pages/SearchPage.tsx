import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTextSearch, useImageSearch } from '../hooks/useSearch';
import SearchBar from '../components/ui/SearchBar';
import ImageUploader from '../components/ui/ImageUploader';
import PhotoGrid from '../components/gallery/PhotoGrid';

type SearchMode = 'text' | 'image';

export default function SearchPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<SearchMode>('text');
  const textSearch = useTextSearch();
  const imageSearch = useImageSearch();

  const recentSearches: string[] = JSON.parse(localStorage.getItem('recentSearches') || '[]');

  const currentResults = mode === 'text' ? textSearch.results : imageSearch.results;
  const currentLoading = mode === 'text' ? textSearch.loading : imageSearch.loading;

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
          <PhotoGrid
            items={currentResults.results}
            onItemClick={(id) => navigate(`/photo/${id}`, { state: { from: '/search' } })}
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
