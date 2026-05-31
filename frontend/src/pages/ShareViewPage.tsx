import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, type MediaItem } from '../api/client';
import PhotoGrid from '../components/gallery/PhotoGrid';

export default function ShareViewPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [title, setTitle] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getSharedMedia(token)
      .then(data => {
        setMedia(data.media);
        setTitle(data.title);
        setExpiresAt(data.expires_at);
      })
      .catch(err => {
        if (err.message.includes('410')) {
          setError('此分享链接已过期');
        } else {
          setError('分享不存在或已失效');
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 text-center">
        <span className="text-6xl mb-4">🔗</span>
        <p className="text-lg text-text font-semibold mb-2">{error}</p>
        <p className="text-sm text-text-light">请联系分享者获取新的链接</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-text">
              {title || '分享的照片'}
            </h1>
            <p className="text-sm text-text-light mt-1">
              {media.length} 张照片
              {expiresAt && ` · 过期时间: ${new Date(expiresAt).toLocaleString('zh-CN')}`}
            </p>
          </div>
        </div>

        <PhotoGrid
          items={media}
          onItemClick={(id) => navigate(`/photo/${id}`, { state: { from: `/share/${token}` } })}
        />
      </div>
    </div>
  );
}
