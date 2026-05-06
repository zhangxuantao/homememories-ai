import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { api, MediaItem } from '../api/client';
import { useMediaById } from '../hooks/useMedia';
import Lightbox from '../components/gallery/Lightbox';

export default function PhotoDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const mediaId = Number(id);
  const { data: item, loading } = useMediaById(mediaId);

  const [hasPrev, setHasPrev] = useState(false);
  const [hasNext, setHasNext] = useState(false);

  useEffect(() => {
    if (!mediaId) return;
    api.get<MediaItem>(`/api/media/${mediaId - 1}`)
      .then(() => setHasPrev(true))
      .catch(() => setHasPrev(false));
    api.get<MediaItem>(`/api/media/${mediaId + 1}`)
      .then(() => setHasNext(true))
      .catch(() => setHasNext(false));
  }, [mediaId]);

  if (loading || !item) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <Lightbox
      item={item}
      onClose={() => navigate(-1)}
      onPrev={hasPrev ? () => navigate(`/photo/${mediaId - 1}`, { replace: true }) : null}
      onNext={hasNext ? () => navigate(`/photo/${mediaId + 1}`, { replace: true }) : null}
    />
  );
}
