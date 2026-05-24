import { useState, useCallback, useRef } from 'react';

export function useSelection() {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectMode, setSelectMode] = useState(false);
  const longPressRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const enterSelectMode = useCallback((initialId?: number) => {
    setSelectMode(true);
    if (initialId !== undefined) {
      setSelectedIds(new Set([initialId]));
    }
  }, []);

  const exitSelectMode = useCallback(() => {
    setSelectMode(false);
    setSelectedIds(new Set());
  }, []);

  const toggleItem = useCallback((id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback((allIds: number[]) => {
    setSelectedIds(new Set(allIds));
  }, []);

  const isSelected = useCallback((id: number) => selectedIds.has(id), [selectedIds]);

  // Long press handler for mobile (300ms)
  const onPointerDown = useCallback((id: number) => {
    longPressRef.current = setTimeout(() => {
      enterSelectMode(id);
      try { navigator.vibrate(15); } catch {}
    }, 300);
  }, [enterSelectMode]);

  const onPointerUp = useCallback(() => {
    if (longPressRef.current) {
      clearTimeout(longPressRef.current);
      longPressRef.current = null;
    }
  }, []);

  const handleItemClick = useCallback((id: number, normalClick: () => void) => {
    if (selectMode) {
      toggleItem(id);
    } else {
      normalClick();
    }
  }, [selectMode, toggleItem]);

  return {
    selectedIds,
    selectMode,
    selectedCount: selectedIds.size,
    enterSelectMode,
    exitSelectMode,
    toggleItem,
    selectAll,
    isSelected,
    onPointerDown,
    onPointerUp,
    handleItemClick,
  };
}
