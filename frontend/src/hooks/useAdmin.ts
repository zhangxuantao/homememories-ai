import { useState, useEffect, useCallback } from 'react';
import { api, SystemStats, JobStatus, ScanStatus, MediaItem } from '../api/client';

export function useAdminStats() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(() => {
    setLoading(true);
    api.get<SystemStats>('/api/admin/stats')
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  return { stats, loading, refresh: fetch };
}

export function useJobStatus(jobId: string | null, pollInterval: number = 2000) {
  const [status, setStatus] = useState<JobStatus | ScanStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);

    const poll = () => {
      api.get<JobStatus>(`/api/admin/job/${jobId}/status`)
        .then((s) => {
          setStatus(s);
          setLoading(false);
          if (s.status === 'completed' || s.status === 'failed') return;
        })
        .catch(() => setLoading(false));
    };

    poll();
    const interval = setInterval(poll, pollInterval);
    return () => clearInterval(interval);
  }, [jobId, pollInterval]);

  return { status, loading };
}

export function useAdminActions() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const startScan = useCallback(async (scanPath?: string) => {
    const res = await api.post<{ job_id: string }>('/api/admin/scan', undefined, scanPath ? { path: scanPath } : undefined);
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const generateEmbeddings = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/embeddings/generate');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startFaceDetection = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/faces/detect');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startBlurCheck = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/cleanup/blurry/check');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startDuplicateCheck = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/cleanup/duplicates/check');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startProcessAll = useCallback(async (scanPath?: string) => {
    const res = await api.post<{ job_id: string }>('/api/admin/process-all', undefined, scanPath ? { path: scanPath } : undefined);
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startClustering = useCallback(async (reset: boolean = false) => {
    const res = await api.post<{ job_id: string }>(`/api/admin/faces/cluster?reset=${reset}`);
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const fetchBlurryMedia = useCallback(async (threshold: number = 100, limit: number = 50) => {
    const res = await api.get<MediaItem[]>('/api/admin/cleanup/blurry', { threshold, limit });
    return res;
  }, []);

  const fetchDuplicatePairs = useCallback(async () => {
    const res = await api.get<MediaItem[][]>('/api/admin/cleanup/duplicates');
    return res;
  }, []);

  const deleteBlurryMedia = useCallback(async (ids: number[]) => {
    const res = await api.delete<{ deleted: { id: number; deleted: boolean }[] }>('/api/admin/cleanup/blurry', ids);
    return res.deleted;
  }, []);

  return { currentJobId, startScan, generateEmbeddings, startFaceDetection, startProcessAll, startBlurCheck, startDuplicateCheck, startClustering, fetchBlurryMedia, fetchDuplicatePairs, deleteBlurryMedia };
}
