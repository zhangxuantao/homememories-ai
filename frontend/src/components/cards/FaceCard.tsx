import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import type { FaceCluster } from '../../api/client';
import { api } from '../../api/client';

interface FaceCardProps {
  cluster: FaceCluster;
  index: number;
  onClick: () => void;
  onLabelChange?: (id: number, label: string) => Promise<void>;
}

export default function FaceCard({ cluster, index, onClick, onLabelChange }: FaceCardProps) {
  const faceThumb = api.faceThumbUrl(cluster.cover_thumbnail);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(cluster.label || '');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleLabelClick = (e: React.MouseEvent) => {
    if (!onLabelChange) return;
    e.stopPropagation();
    setEditValue(cluster.label || '');
    setIsEditing(true);
  };

  const handleSave = async () => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== cluster.label && onLabelChange) {
      await onLabelChange(cluster.id, trimmed);
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
    }
  };

  const handleInputClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.2 }}
      className="glass-card rounded-card p-5 text-center cursor-pointer hover:shadow-md transition-shadow group"
      onClick={onClick}
    >
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-misty mx-auto mb-3 flex items-center justify-center overflow-hidden">
        {faceThumb ? (
          <img src={faceThumb} alt={cluster.label || ''} className="w-full h-full object-cover" />
        ) : (
          <span className="text-2xl">👤</span>
        )}
      </div>
      {isEditing && onLabelChange ? (
        <input
          ref={inputRef}
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={handleSave}
          onKeyDown={handleKeyDown}
          onClick={handleInputClick}
          maxLength={50}
          className="text-sm font-semibold text-text text-center bg-misty/30 rounded-btn px-2 py-1 w-full outline-none border border-primary"
        />
      ) : (
        <h3
          className={`text-sm font-semibold text-text ${onLabelChange ? 'cursor-text hover:text-primary transition-colors' : ''}`}
          onClick={handleLabelClick}
          title={onLabelChange ? '点击编辑' : undefined}
        >
          {cluster.label || `人物 ${cluster.id}`}
          {onLabelChange && (
            <span className="inline-block ml-1 opacity-0 group-hover:opacity-100 transition-opacity text-text-light">✎</span>
          )}
        </h3>
      )}
      <span className="inline-block mt-1.5 px-3 py-0.5 rounded-pill bg-misty text-text-light text-xs">
        {cluster.photo_count} 张
      </span>
    </motion.div>
  );
}
