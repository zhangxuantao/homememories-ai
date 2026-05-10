import { useState, useEffect, useCallback } from 'react';
import { api, TimelineEvent, PaginatedResponse, MediaItem } from '../api/client';

export function useTimelineYears() {
  const [years, setYears] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<number[]>('/api/timeline/years')
      .then(setYears)
      .catch(() => setYears([]))
      .finally(() => setLoading(false));
  }, []);

  return { years, loading };
}

export function useEvents(year: number | null) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (year === null) return;
    setLoading(true);
    api.get<TimelineEvent[]>('/api/timeline/events', { year })
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [year]);

  return { events, loading };
}

export function useEventMedia(eventId: number | null) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const fetchMore = useCallback(() => {
    if (!eventId || loading || !hasMore) return;
    setLoading(true);
    api.get<PaginatedResponse<MediaItem>>(`/api/timeline/event/${eventId}/media`, {
      cursor: nextCursor ?? undefined,
      limit: 100,
    })
      .then((res) => {
        setItems((prev) => {
          const existingIds = new Set(prev.map((i) => i.id));
          const newItems = res.items.filter((i) => !existingIds.has(i.id));
          return [...prev, ...newItems];
        });
        setNextCursor(res.next_cursor);
        setHasMore(!!res.next_cursor);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [eventId, nextCursor, loading, hasMore]);

  useEffect(() => {
    setItems([]);
    setNextCursor(null);
    setHasMore(true);
  }, [eventId]);

  useEffect(() => { fetchMore(); }, [eventId]);

  return { items, loading, hasMore, fetchMore };
}
