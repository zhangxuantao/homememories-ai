import { useState, useRef, useEffect } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
}

export default function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) {
      onSearch(trimmed);
      const recent = JSON.parse(localStorage.getItem('recentSearches') || '[]');
      const updated = [trimmed, ...recent.filter((s: string) => s !== trimmed)].slice(0, 8);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-light">🔍</span>
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索你的回忆..."
        className="w-full pl-10 pr-16 py-3 rounded-card border border-misty bg-white text-text placeholder-text-light text-sm focus:outline-none focus:border-primary transition-colors"
      />
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 bg-primary text-white text-xs rounded-btn disabled:opacity-50"
      >
        {loading ? '搜索中...' : '搜索'}
      </button>
    </form>
  );
}
