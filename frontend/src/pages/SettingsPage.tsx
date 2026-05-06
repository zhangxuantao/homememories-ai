import { useAdminStats, useJobStatus, useAdminActions } from '../hooks/useAdmin';

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

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-misty last:border-0">
      <span className="text-sm text-text">{label}</span>
      <span className="text-sm font-medium text-text">{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const { stats, loading: statsLoading, refresh: refreshStats } = useAdminStats();
  const { currentJobId, startScan, generateEmbeddings, startFaceDetection, startBlurCheck, startDuplicateCheck } = useAdminActions();
  const { status: jobStatus } = useJobStatus(currentJobId);

  const formatBytes = (bytes: number) => {
    if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    if (bytes > 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-6">设置</h1>

      {/* 媒体管理 */}
      <Section title="媒体管理">
        <div className="space-y-2">
          <ActionButton label="扫描目录" onClick={startScan} />
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
        </div>
      </Section>

      {/* 清理工具 */}
      <Section title="清理工具">
        <div className="space-y-2">
          <ActionButton label="检测模糊照片" onClick={startBlurCheck} />
          <ActionButton label="检测重复照片" onClick={startDuplicateCheck} />
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
