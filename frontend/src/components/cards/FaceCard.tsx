import { motion } from 'framer-motion';
import type { FaceCluster } from '../../api/client';

interface FaceCardProps {
  cluster: FaceCluster;
  index: number;
  onClick: () => void;
}

export default function FaceCard({ cluster, index, onClick }: FaceCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.2 }}
      className="glass-card rounded-card p-5 text-center cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-misty mx-auto mb-3 flex items-center justify-center">
        <span className="text-2xl">👤</span>
      </div>
      <h3 className="text-sm font-semibold text-text">{cluster.label || `人物 ${cluster.id}`}</h3>
      <span className="inline-block mt-1.5 px-3 py-0.5 rounded-pill bg-misty text-text-light text-xs">
        {cluster.photo_count} 张
      </span>
    </motion.div>
  );
}
