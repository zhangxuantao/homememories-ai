import { useState, useEffect, useCallback } from 'react';
import { api, MediaItem } from '../api/client';

interface UseApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): UseApiState<T> & { mutate: () => void } {
  const [state, setState] = useState<UseApiState<T>>({ data: null, error: null, loading: true });

  const fetch = useCallback(() => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    fetcher()
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((err) => setState({ data: null, error: (err as Error).message, loading: false }));
  }, deps);

  useEffect(() => { fetch(); }, [fetch]);

  return { ...state, mutate: fetch };
}

export function useRandomMedia(count: number = 4) {
  return useApi(() => api.get<MediaItem[]>('/api/media/random', { count }), [count]);
}

export function useOnThisDay(month: number, day: number) {
  return useApi(() => api.get<MediaItem[]>('/api/media/on-this-day', { month, day }), [month, day]);
}

export function useMediaById(id: number | null) {
  return useApi(
    () => (id ? api.get<MediaItem>(`/api/media/${id}`) : Promise.reject(new Error('No id'))),
    [id]
  );
}
