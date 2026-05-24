import { useState, useRef, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import UploadPanel from '../../UploadPanel';

const ITEMS = [
  { type: 'tab', to: '/', label: '首页', icon: '🏠' },
  { type: 'tab', to: '/timeline', label: '时间线', icon: '📅' },
  { type: 'tab', to: '/search', label: '搜索', icon: '🔍' },
  { type: 'tab', to: '/people', label: '人物', icon: '👤' },
  { type: 'tab', to: '/settings', label: '设置', icon: '⚙️' },
  { type: 'upload' },
];

export default function MobileNav() {
  const [uploadOpen, setUploadOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to center the "+" button on mount
  useEffect(() => {
    if (scrollRef.current) {
      const container = scrollRef.current;
      const middle = (container.scrollWidth - container.clientWidth) / 2;
      container.scrollLeft = middle;
    }
  }, []);

  return (
    <>
      <nav
        ref={scrollRef}
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex overflow-x-auto snap-x snap-mandatory scrollbar-none h-16 bg-white/90 backdrop-blur-xl border-t border-misty"
      >
        {ITEMS.map((item, i) =>
          item.type === 'upload' ? (
            <button
              key="upload"
              onClick={() => setUploadOpen(true)}
              className="flex-shrink-0 w-[20vw] snap-center flex flex-col items-center justify-center gap-0.5 text-[10px] text-text-light"
            >
              <span className="w-11 h-11 bg-primary text-white rounded-full flex items-center justify-center text-xl shadow-lg shadow-primary/30">
                +
              </span>
              <span>上传</span>
            </button>
          ) : (
            <NavLink
              key={item.to}
              to={item.to!}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex-shrink-0 w-[20vw] snap-center flex flex-col items-center justify-center gap-0.5 text-[10px] transition-colors ${
                  isActive ? 'text-primary font-semibold' : 'text-text-light'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          )
        )}
      </nav>

      <UploadPanel open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </>
  );
}
