import { motion } from 'framer-motion';
import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface MemoryCardProps {
  item: MediaItem;
  title?: string;
  subtitle?: string;
  variant?: 'hero' | 'default';
  index?: number;
  onClick?: () => void;
}

export default function MemoryCard({ item, title, subtitle, variant = 'default', index = 0, onClick }: MemoryCardProps) {
  const thumbUrl = api.thumbUrl(item.thumbnail_path);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className={`glass-card rounded-card overflow-hidden cursor-pointer hover:shadow-lg transition-shadow ${
        variant === 'hero' ? 'col-span-full' : ''
      }`}
      style={{ borderLeft: variant === 'hero' ? '3px solid var(--color-primary)' : undefined }}
      onClick={onClick}
    >
      <div
        className={`w-full bg-gradient-to-br from-subtle to-misty flex items-center justify-center ${
          variant === 'hero' ? 'h-48 md:h-64' : 'h-40'
        }`}
      >
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={item.filename}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <span className="text-4xl">🌸</span>
        )}
      </div>

      <div className="p-3.5" style={{ borderLeft: variant === 'hero' ? 'none' : '3px solid var(--color-primary)' }}>
        {title && (
          <div className="text-[15px] font-semibold text-text mb-1">{title}</div>
        )}
        {subtitle && (
          <div className="text-xs text-text-light">{subtitle}</div>
        )}
        {!title && !subtitle && (
          <>
            <div className="text-sm font-medium text-text truncate">{item.filename}</div>
            <div className="text-xs text-text-light mt-0.5">{item.date_taken?.slice(0, 10)}</div>
          </>
        )}
      </div>
    </motion.div>
  );
}
