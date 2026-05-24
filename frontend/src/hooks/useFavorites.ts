import { useState, useEffect, useCallback } from 'react';
import { api, MediaItem } from '../api/client';

export function useFavorites(limit: number = 50) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);

  const fetch = useCallback(async (reset = false) => {
    setLoading(true);
    const o = reset ? 0 : offset;
    try {
      const data = await api.getFavorites(limit, o);
      setItems(prev => reset ? data : [...prev, ...data]);
      if (reset) setOffset(limit);
      else setOffset(o + limit);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [limit, offset]);

  useEffect(() => { fetch(true); }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const loadMore = useCallback(() => fetch(false), [fetch]);
  const refresh = useCallback(() => fetch(true), [fetch]);

  const toggleFavorite = useCallback(async (mediaId: number) => {
    const res = await api.toggleFavorite(mediaId);
    if (!res.favorited) {
      setItems(prev => prev.filter(item => item.id !== mediaId));
    } else {
      refresh();
    }
    return res.favorited;
  }, [refresh]);

  return { items, loading, loadMore, toggleFavorite, refresh };
}

export function useRecentFavorites(limit: number = 6) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getRecentFavorites(limit);
      setItems(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => { fetch(); }, [fetch]);

  return { items, loading, refresh: fetch };
}

export function useFavoriteStatus(mediaId: number | null) {
  const [favorited, setFavorited] = useState(false);

  useEffect(() => {
    if (mediaId === null) return;
    api.checkFavorites([mediaId]).then(data => {
      setFavorited(data[String(mediaId)] ?? false);
    }).catch(() => {});
  }, [mediaId]);

  const toggle = useCallback(async () => {
    if (mediaId === null) return;
    const res = await api.toggleFavorite(mediaId);
    setFavorited(res.favorited);
  }, [mediaId]);

  return { favorited, toggle };
}
