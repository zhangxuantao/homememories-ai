import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, FaceCluster, MediaItem, PaginatedResponse } from '../api/client';
import FaceCard from '../components/cards/FaceCard';
import PhotoGrid from '../components/gallery/PhotoGrid';
import { useSelection } from '../hooks/useSelection';
import SelectionBar from '../components/gallery/SelectionBar';
import SelectionActions from '../components/gallery/SelectionActions';
import AlbumPickerSheet from '../components/albums/AlbumPickerSheet';
import SharePanel from '../components/share/SharePanel';
import CollagePanel from '../components/share/CollagePanel';

export default function PeoplePage() {
  const navigate = useNavigate();
  const [clusters, setClusters] = useState<FaceCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCluster, setSelectedCluster] = useState<FaceCluster | null>(null);
  const [clusterMedia, setClusterMedia] = useState<MediaItem[]>([]);
  const selection = useSelection();
  const [albumPickerOpen, setAlbumPickerOpen] = useState(false);
  const [pendingAlbumIds, setPendingAlbumIds] = useState<number[]>([]);

  const [shareOpen, setShareOpen] = useState(false);
  const [collageOpen, setCollageOpen] = useState(false);
  const [pendingActionIds, setPendingActionIds] = useState<number[]>([]);

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

  const handleBatchDownload = async () => {
    const ids = Array.from(selection.selectedIds);
    if (ids.length <= 5) {
      ids.forEach(id => window.open(api.originalUrl(id), '_blank'));
    } else {
      try {
        const res = await fetch(`${window.location.origin}/api/media/export-zip`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(ids),
        });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'homememories_export.zip';
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        alert('下载失败');
      }
    }
    selection.exitSelectMode();
  };

  const handleBatchDelete = async () => {
    const ids = Array.from(selection.selectedIds);
    if (!confirm(`确定删除这 ${ids.length} 张照片？此操作不可恢复。`)) return;
    for (const id of ids) {
      try { await api.delete(`/api/media/${id}`); } catch {}
    }
    selection.exitSelectMode();
    // Refresh cluster media
    if (selectedCluster) {
      const res = await api.get<PaginatedResponse<MediaItem>>(
        `/api/faces/cluster/${selectedCluster.id}/media`, { limit: 100 }
      );
      setClusterMedia(res.items);
    }
  };

  const handleShare = () => {
    const ids = Array.from(selection.selectedIds);
    setPendingActionIds(ids);
    setShareOpen(true);
  };

  const handleCollage = () => {
    const ids = Array.from(selection.selectedIds);
    if (ids.length < 2 || ids.length > 9) {
      alert('拼图需要选择 2-9 张照片');
      return;
    }
    setPendingActionIds(ids);
    setCollageOpen(true);
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
            <>
              {selection.selectMode && (
                <>
                  <SelectionBar
                    count={selection.selectedCount}
                    onSelectAll={() => selection.selectAll(clusterMedia.map(item => item.id))}
                    onClearAll={() => selection.selectAll([])}
                    onExit={selection.exitSelectMode}
                  />
                  <SelectionActions
                    onAddToAlbum={() => {
                      const ids = Array.from(selection.selectedIds);
                      setPendingAlbumIds(ids);
                      setAlbumPickerOpen(true);
                    }}
                    onShare={handleShare}
                    onCollage={handleCollage}
                    onDownload={handleBatchDownload}
                    onDelete={handleBatchDelete}
                  />
                </>
              )}
              <PhotoGrid
                items={clusterMedia}
                onItemClick={(id) => {
                  if (!selection.selectMode) navigate(`/photo/${id}`, { state: { from: '/people' } });
                }}
                selection={selection}
              />
            </>
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

      <AlbumPickerSheet
        open={albumPickerOpen}
        onClose={() => setAlbumPickerOpen(false)}
        mediaIds={pendingAlbumIds}
        onDone={() => selection.exitSelectMode()}
      />

      <SharePanel open={shareOpen} onClose={() => setShareOpen(false)} mediaIds={pendingActionIds} />
      <CollagePanel open={collageOpen} onClose={() => setCollageOpen(false)} mediaIds={pendingActionIds} />
    </div>
  );
}
