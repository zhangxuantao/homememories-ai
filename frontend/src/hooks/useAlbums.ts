// frontend/src/hooks/useAlbums.ts
import { useState, useEffect, useCallback } from 'react';
import { api, type Album, type MediaItem } from '../api/client';

export function useAlbums() {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listAlbums();
      setAlbums(data);
    } catch (err) {
      console.error('Failed to load albums:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { albums, loading, refresh };
}

export function useAlbumMedia(albumId: number) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAlbumMedia(albumId, 500);
      setItems(data);
    } catch (err) {
      console.error('Failed to load album media:', err);
    } finally {
      setLoading(false);
    }
  }, [albumId]);

  useEffect(() => { refresh(); }, [refresh]);

  return { items, loading, refresh };
}
