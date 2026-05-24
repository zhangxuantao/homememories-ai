import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAdminStats, useJobStatus, useAdminActions } from '../hooks/useAdmin';
import { api, MediaItem, ServerInfo } from '../api/client';
import QrCode from '../components/ui/QrCode';
import PhotoGrid from '../components/gallery/PhotoGrid';
import { useSelection } from '../hooks/useSelection';
import SelectionBar from '../components/gallery/SelectionBar';
import SelectionActions from '../components/gallery/SelectionActions';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="text-base font-semibold text-text mb-3">{title}</h2>
      {children}
    </section>
  );
}

function ActionButton({ label, onClick, disabled }: { label: string; onClick: () => void; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full px-4 py-2.5 rounded-btn bg-primary text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
    >
      {label}
    </button>
  );
}

function SmallButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1 rounded-btn text-xs font-medium text-primary border border-primary hover:bg-primary hover:text-white transition-colors"
    >
      {label}
    </button>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-misty last:border-0">
      <span className="text-sm text-text">{label}</span>
      <span className="text-sm font-medium text-text">{value}</span>
    </div>
  );
}

function ThumbTile({ item, api }: { item: MediaItem; api: { thumbUrl: (p: string | null | undefined) => string } }) {
  const src = api.thumbUrl(item.thumbnail_path);
  return (
    <div className="relative aspect-square rounded-lg overflow-hidden bg-misty/50">
      {src ? (
        <img src={src} alt={item.filename} className="w-full h-full object-cover" loading="lazy" />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-2xl">
          {item.media_type === 'video' ? '🎬' : '🖼️'}
        </div>
      )}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-1.5">
        <span className="text-[10px] text-white/90 truncate block">{item.date_taken?.slice(0, 10) || item.filename}</span>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { stats, loading: statsLoading, refresh: refreshStats } = useAdminStats();
  const { currentJobId, startScan, generateEmbeddings, startFaceDetection, startProcessAll, startBlurCheck, startDuplicateCheck, startClustering, fetchBlurryMedia, fetchDuplicatePairs, deleteBlurryMedia } = useAdminActions();
  const { status: jobStatus } = useJobStatus(currentJobId);
  const [scanPath, setScanPath] = useState('');

  // Cleanup results state
  const [blurryItems, setBlurryItems] = useState<MediaItem[] | null>(null);
  const [duplicatePairs, setDuplicatePairs] = useState<MediaItem[][] | null>(null);
  const [showBlurry, setShowBlurry] = useState(false);
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set());

  const navigate = useNavigate();
  const blurrySelection = useSelection();
  const duplicateSelection = useSelection();

  const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null);
  const frontendUrl = window.location.origin;
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.getServerInfo().then(setServerInfo).catch(() => {});
  }, []);

  const isLan = (ip: string) =>
    /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(ip);

  const formatBytes = (bytes: number) => {
    if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    if (bytes > 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  const handleViewBlurry = async () => {
    setShowBlurry(!showBlurry);
    if (blurryItems === null) {
      const items = await fetchBlurryMedia();
      setBlurryItems(items);
    }
  };

  const handleViewDuplicates = async () => {
    setShowDuplicates(!showDuplicates);
    if (duplicatePairs === null) {
      const pairs = await fetchDuplicatePairs();
      setDuplicatePairs(pairs);
    }
  };

  const handleBlurryBatchDelete = async () => {
    const ids = Array.from(blurrySelection.selectedIds);
    if (!confirm(`确定删除这 ${ids.length} 张模糊照片？此操作不可恢复。`)) return;
    for (const id of ids) {
      try {
        await api.delete(`/api/media/${id}`);
      } catch {}
    }
    blurrySelection.exitSelectMode();
    const items = await fetchBlurryMedia();
    setBlurryItems(items);
  };

  const handleDeleteBlurry = async (id: number) => {
    setDeletingIds(prev => new Set(prev).add(id));
    await deleteBlurryMedia([id]);
    setBlurryItems(prev => prev ? prev.filter(item => item.id !== id) : null);
    setDeletingIds(prev => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  };

  const handleDuplicateBatchDelete = async () => {
    if (!duplicatePairs) return;
    const selectedIds = duplicateSelection.selectedIds;
    if (selectedIds.size === 0) return;
    if (!confirm(`确定删除这 ${selectedIds.size} 张重复照片？此操作不可恢复。`)) return;

    for (const pair of duplicatePairs) {
      const deleteIds = pair
        .map((m: MediaItem) => m.id)
        .filter((id: number) => selectedIds.has(id));
      if (deleteIds.length > 0 && deleteIds.length < pair.length) {
        const keepId = pair.find((m: MediaItem) => !selectedIds.has(m.id))?.id;
        if (keepId) {
          try {
            await api.deleteDuplicateMedia(keepId, deleteIds);
          } catch {}
        }
      }
    }
    duplicateSelection.exitSelectMode();
    const fresh = await fetchDuplicatePairs();
    setDuplicatePairs(fresh);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-6">设置</h1>

      {/* 一键处理 */}
      <Section title="一键处理">
        <div className="space-y-2">
          <p className="text-xs text-text-light">按顺序自动执行：扫描 → Embedding → 人脸检测 → 人脸聚类 → 事件生成</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={scanPath}
              onChange={(e) => setScanPath(e.target.value)}
              placeholder="输入扫描路径，留空使用默认目录"
              className="flex-1 px-3 py-2.5 rounded-btn bg-misty/30 text-sm text-text placeholder:text-text-light/60 border border-misty focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <ActionButton label="一键处理全部" onClick={() => startProcessAll(scanPath || undefined)} />
          {jobStatus && (
            <div className="glass-card rounded-card p-3 text-sm">
              <div className="flex justify-between text-text-light mb-1">
                <span>
                  {jobStatus.status === 'running'
                    ? (jobStatus as any).message || '处理中...'
                    : jobStatus.status === 'completed'
                    ? '全部完成'
                    : jobStatus.status === 'failed'
                    ? '处理失败'
                    : jobStatus.status}
                </span>
                <span>{jobStatus.progress.toFixed(0)}%</span>
              </div>
              <div className="w-full h-1.5 bg-misty rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${jobStatus.progress}%` }}
                />
              </div>
              {(jobStatus as any).stage && (jobStatus as any).stage !== 'done' && (
                <p className="text-xs text-primary mt-1">步骤 {(jobStatus as any).step}/{(jobStatus as any).total_steps || 5}: {(jobStatus as any).message}</p>
              )}
              {jobStatus.status === 'failed' && (
                <p className="text-xs text-red-400 mt-1">{(jobStatus as any).error}</p>
              )}
              {jobStatus.status === 'completed' && (
                <p className="text-xs text-text-light mt-1">全部 5 步处理完成，可刷新统计查看结果</p>
              )}
            </div>
          )}
        </div>
      </Section>

      {/* 媒体管理 */}
      <Section title="媒体管理">
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={scanPath}
              onChange={(e) => setScanPath(e.target.value)}
              placeholder="输入扫描路径，留空使用默认目录"
              className="flex-1 px-3 py-2.5 rounded-btn bg-misty/30 text-sm text-text placeholder:text-text-light/60 border border-misty focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <ActionButton label="扫描目录" onClick={() => startScan(scanPath || undefined)} />
          {jobStatus && (
            <div className="glass-card rounded-card p-3 text-sm">
              <div className="flex justify-between text-text-light mb-1">
                <span>{jobStatus.status === 'running' ? '扫描中...' : jobStatus.status}</span>
                <span>{jobStatus.progress.toFixed(0)}%</span>
              </div>
              <div className="w-full h-1.5 bg-misty rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${jobStatus.progress}%` }}
                />
              </div>
              {jobStatus.status === 'completed' && (
                <p className="text-xs text-text-light mt-1">完成 — 点击下方刷新按钮查看统计</p>
              )}
            </div>
          )}
        </div>
      </Section>

      {/* AI 处理 */}
      <Section title="AI 处理">
        <div className="space-y-2">
          <ActionButton label="生成 Embeddings" onClick={generateEmbeddings} />
          <ActionButton label="人脸检测" onClick={startFaceDetection} />
          <ActionButton label="人脸聚类" onClick={() => startClustering(false)} />
        </div>
      </Section>

      {/* 清理工具 */}
      <Section title="清理工具">
        <div className="space-y-3">
          {/* Blur detection */}
          <div>
            <ActionButton label="检测模糊照片" onClick={startBlurCheck} />
            <div className="mt-2">
              <SmallButton label={showBlurry ? '隐藏结果' : '查看结果'} onClick={handleViewBlurry} />
            </div>
            {showBlurry && blurryItems !== null && (
              <div className="mt-3">
                <p className="text-sm text-text-light mb-2">
                  {blurryItems.length === 0 ? '没有检测到模糊照片' : `找到 ${blurryItems.length} 张模糊照片`}
                </p>
                {blurryItems.length > 0 && (
                  <div>
                    <button
                      onClick={() => blurrySelection.enterSelectMode()}
                      className="text-xs text-primary mb-2 hover:underline"
                    >
                      批量选择删除
                    </button>
                    {blurrySelection.selectMode && (
                      <>
                        <SelectionBar
                          count={blurrySelection.selectedCount}
                          onSelectAll={() => blurrySelection.selectAll(blurryItems.map(item => item.id))}
                          onClearAll={() => blurrySelection.selectAll([])}
                          onExit={blurrySelection.exitSelectMode}
                        />
                        <div className="flex justify-center gap-4 my-3">
                          <button
                            onClick={handleBlurryBatchDelete}
                            disabled={blurrySelection.selectedCount === 0}
                            className="px-4 py-1.5 bg-red-500 text-white rounded-btn text-sm disabled:opacity-50"
                          >
                            删除选中 ({blurrySelection.selectedCount})
                          </button>
                        </div>
                      </>
                    )}
                    <PhotoGrid
                      items={blurryItems}
                      onItemClick={(id) => navigate(`/photo/${id}`, { state: { from: '/settings' } })}
                      selection={blurrySelection}
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Duplicate detection */}
          <div>
            <ActionButton label="检测重复照片" onClick={startDuplicateCheck} />
            <div className="mt-2">
              <SmallButton label={showDuplicates ? '隐藏结果' : '查看结果'} onClick={handleViewDuplicates} />
            </div>
            {showDuplicates && duplicatePairs !== null && (
              <div className="mt-3">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-text-light">
                    {duplicatePairs.length === 0 ? '没有检测到重复照片' : `找到 ${duplicatePairs.length} 组重复照片`}
                  </p>
                  {duplicatePairs.length > 0 && !duplicateSelection.selectMode && (
                    <button
                      onClick={() => duplicateSelection.enterSelectMode()}
                      className="text-xs text-primary border border-primary px-2 py-0.5 rounded-btn hover:bg-primary hover:text-white transition-colors"
                    >
                      批量选择
                    </button>
                  )}
                </div>

                {duplicateSelection.selectMode && (
                  <SelectionBar
                    count={duplicateSelection.selectedCount}
                    onSelectAll={() => duplicateSelection.selectAll(duplicatePairs.flat().map(m => m.id))}
                    onClearAll={() => duplicateSelection.selectAll([])}
                    onExit={duplicateSelection.exitSelectMode}
                  />
                )}

                {duplicatePairs.length > 0 && (
                  <div className="space-y-3">
                    {duplicatePairs.map((pair, i) => {
                      return (
                        <div key={i} className="glass-card rounded-card p-2">
                          <p className="text-xs text-text-light mb-1">重复组 {i + 1}</p>
                          <div className="grid grid-cols-2 gap-2">
                            {pair.map((item: MediaItem) => {
                              const isSel = duplicateSelection.isSelected(item.id);
                              return (
                                <div
                                  key={item.id}
                                  className={`relative rounded-lg overflow-hidden bg-misty/50 cursor-pointer transition-all ${
                                    duplicateSelection.selectMode
                                      ? isSel
                                        ? 'ring-2 ring-red-400 ring-offset-1 opacity-60'
                                        : 'hover:ring-2 hover:ring-green-400/50'
                                      : ''
                                  }`}
                                  onClick={() => {
                                    if (duplicateSelection.selectMode) {
                                      duplicateSelection.toggleItem(item.id);
                                    }
                                  }}
                                  onPointerDown={() => duplicateSelection.onPointerDown(item.id)}
                                  onPointerUp={duplicateSelection.onPointerUp}
                                >
                                  <ThumbTile item={item} api={api} />
                                  {duplicateSelection.selectMode && (
                                    <div className={`absolute top-1.5 left-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                                      isSel ? 'bg-red-400 border-red-400 text-white' : 'bg-black/30 border-white'
                                    }`}>
                                      {isSel && <span className="text-[10px] leading-none">✓</span>}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {duplicateSelection.selectMode && (
                  <div className="fixed bottom-14 left-0 right-0 z-[60] flex justify-center items-center py-3 px-4 bg-white/95 backdrop-blur-md border-t border-misty md:ml-14">
                    <button
                      onClick={handleDuplicateBatchDelete}
                      disabled={duplicateSelection.selectedIds.size === 0}
                      className="flex flex-col items-center gap-1 text-sm text-text hover:text-red-500 transition-colors disabled:opacity-30"
                    >
                      <span className="text-xl">🗑️</span>
                      <span className="text-[10px]">删除选中 ({duplicateSelection.selectedIds.size})</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* 局域网访问 */}
      <Section title="局域网访问">
        <div className="flex flex-col items-center gap-3">
          <QrCode url={frontendUrl} size={180} />
          <div className="flex items-center gap-2">
            <span className="text-sm text-text break-all max-w-[240px]">{frontendUrl}</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(frontendUrl).then(() => {
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }).catch(() => {});
              }}
              className="shrink-0 px-2 py-1 text-xs text-primary border border-primary rounded-btn hover:bg-primary hover:text-white transition-colors"
            >
              {copied ? '已复制' : '复制地址'}
            </button>
          </div>
          <p className="text-xs text-text-light text-center leading-relaxed max-w-[280px]">
            用相机或浏览器扫码直接打开；微信扫码请点击右上角"在浏览器中打开"
          </p>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${serverInfo && isLan(serverInfo.lan_ip) ? 'bg-green-400' : 'bg-yellow-400'}`} />
            <span className="text-xs text-text-light">
              {serverInfo && isLan(serverInfo.lan_ip)
                ? '当前已连接局域网'
                : serverInfo
                  ? '未检测到局域网地址'
                  : '检测中...'}
            </span>
          </div>
        </div>
      </Section>

      {/* 系统信息 */}
      <Section title="系统信息">
        {statsLoading ? (
          <div className="flex justify-center py-6">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : stats ? (
          <div className="glass-card rounded-card p-3">
            <StatRow label="总媒体数" value={String(stats.media_count)} />
            <StatRow label="图片" value={String(stats.image_count)} />
            <StatRow label="视频" value={String(stats.video_count)} />
            <StatRow label="数据库大小" value={formatBytes(stats.db_size_bytes)} />
            <StatRow label="上次扫描" value={stats.last_scan_time?.slice(0, 10) || '从未'} />
            {serverInfo?.gpu && (
              <>
                <div className="border-t border-misty my-2" />
                <div className="flex items-center gap-2 py-1">
                  <span className={`w-2 h-2 rounded-full ${serverInfo.gpu.cuda_available ? 'bg-green-400' : 'bg-yellow-400'}`} />
                  <span className="text-sm text-text">
                    {serverInfo.gpu.cuda_available
                      ? `GPU: ${serverInfo.gpu.device_name || 'CUDA 可用'}`
                      : 'GPU: 不可用 (CPU 模式)'}
                  </span>
                </div>
                {serverInfo.gpu.cuda_available && serverInfo.gpu.memory_total_gb && (
                  <StatRow
                    label="显存"
                    value={`${serverInfo.gpu.memory_used_gb ?? 0} GB / ${serverInfo.gpu.memory_total_gb} GB`}
                  />
                )}
                {serverInfo.models.clip_loaded && (
                  <StatRow label="Chinese-CLIP" value={`${serverInfo.models.clip_device} 模式`} />
                )}
              </>
            )}
          </div>
        ) : (
          <p className="text-text-light text-sm">无法加载系统信息</p>
        )}
        <button onClick={refreshStats} className="mt-2 text-sm text-primary hover:underline">
          刷新统计
        </button>
      </Section>
    </div>
  );
}
