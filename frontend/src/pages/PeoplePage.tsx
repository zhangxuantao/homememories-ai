import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, FaceCluster, MediaItem, PaginatedResponse } from '../api/client';
import FaceCard from '../components/cards/FaceCard';
import PhotoGrid from '../components/gallery/PhotoGrid';

export default function PeoplePage() {
  const navigate = useNavigate();
  const [clusters, setClusters] = useState<FaceCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCluster, setSelectedCluster] = useState<FaceCluster | null>(null);
  const [clusterMedia, setClusterMedia] = useState<MediaItem[]>([]);

  useEffect(() => {
    api.get<FaceCluster[]>('/api/faces/clusters')
      .then(setClusters)
      .catch(() => setClusters([]))
      .finally(() => setLoading(false));
  }, []);

  const handleClusterClick = async (cluster: FaceCluster) => {
    setSelectedCluster(cluster);
    try {
      const res = await api.get<PaginatedResponse<MediaItem>>(`/api/faces/cluster/${cluster.id}/media`, { limit: 100 });
      setClusterMedia(res.items);
    } catch {
      setClusterMedia([]);
    }
  };

  const handleLabelChange = async (id: number, label: string) => {
    await api.patch(`/api/faces/cluster/${id}`, undefined, { label });
    setClusters(prev =>
      prev.map(c => c.id === id ? { ...c, label } : c)
    );
    if (selectedCluster?.id === id) {
      setSelectedCluster(prev => prev ? { ...prev, label } : null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-4">人物</h1>

      {selectedCluster ? (
        <div>
          <button
            onClick={() => setSelectedCluster(null)}
            className="text-sm text-primary mb-4 flex items-center gap-1"
          >
            ← 返回人物列表
          </button>
          <h2 className="text-lg font-semibold text-text mb-3">
            {selectedCluster.label || `人物 ${selectedCluster.id}`}
          </h2>
          {clusterMedia.length > 0 ? (
            <PhotoGrid items={clusterMedia} onItemClick={(id) => navigate(`/photo/${id}`, { state: { from: '/people' } })} />
          ) : (
            <p className="text-text-light text-center py-8">暂无照片</p>
          )}
        </div>
      ) : clusters.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <span className="text-6xl mb-4">👤</span>
          <p className="text-text font-medium mb-1">还没有检测到人物哦</p>
          <p className="text-text-light text-sm">先去设置页面运行人脸检测吧~</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
          {clusters.map((c, i) => (
            <FaceCard key={c.id} cluster={c} index={i} onClick={() => handleClusterClick(c)} onLabelChange={handleLabelChange} />
          ))}
        </div>
      )}
    </div>
  );
}
