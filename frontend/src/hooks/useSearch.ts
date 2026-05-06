import { useState, useCallback } from 'react';
import { api, SearchResponse } from '../api/client';

export function useTextSearch() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<SearchResponse>('/api/search/text', { query, limit: 50 });
      setResults(res);
    } catch (err) {
      setError((err as Error).message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { results, loading, error, search };
}

export function useImageSearch() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.upload<SearchResponse>('/api/search/image', file);
      setResults(res);
    } catch (err) {
      setError((err as Error).message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { results, loading, error, search };
}
