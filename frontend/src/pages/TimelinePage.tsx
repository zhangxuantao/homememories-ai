import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTimelineYears, useEvents, useEventMedia } from '../hooks/useTimeline';
import type { TimelineEvent } from '../api/client';
import { SkeletonCard } from '../components/ui/Skeleton';
import YearPills from '../components/timeline/YearPills';
import EventStrip from '../components/timeline/EventStrip';

export default function TimelinePage() {
  const navigate = useNavigate();
  const { years, loading: yearsLoading } = useTimelineYears();
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const { events, loading: eventsLoading } = useEvents(selectedYear);

  useEffect(() => {
    if (years.length > 0 && selectedYear === null) setSelectedYear(years[0]);
  }, [years, selectedYear]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-4">时间线</h1>

      {yearsLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <YearPills years={years} selectedYear={selectedYear} onSelect={setSelectedYear} />

          {eventsLoading ? (
            <div className="mt-4 space-y-3">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : events.length === 0 ? (
            <p className="text-center text-text-light py-12">这一年还没有照片哦</p>
          ) : (
            <div className="mt-4 space-y-3">
              {events.map((event) => (
                <EventItem key={event.id} event={event} navigate={navigate} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function EventItem({ event, navigate }: { event: TimelineEvent; navigate: ReturnType<typeof useNavigate> }) {
  const { items } = useEventMedia(event.id);

  const handlePhotoClick = (mediaId: number) => {
    navigate(`/photo/${mediaId}`, { state: { from: '/timeline' } });
  };

  return <EventStrip event={event} media={items} onPhotoClick={handlePhotoClick} />;
}
