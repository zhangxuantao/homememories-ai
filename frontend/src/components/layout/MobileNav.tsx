import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import UploadPanel from '../../UploadPanel';

const ITEMS = [
  { type: 'tab', to: '/', label: '首页', icon: '🏠' },
  { type: 'tab', to: '/timeline', label: '时间线', icon: '📅' },
  { type: 'tab', to: '/search', label: '搜索', icon: '🔍' },
  { type: 'tab', to: '/people', label: '人物', icon: '👤' },
  { type: 'tab', to: '/settings', label: '设置', icon: '⚙️' },
];

export default function MobileNav() {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <>
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-xl border-t border-misty">
        <div className="flex overflow-x-auto scrollbar-none snap-x snap-mandatory">
          {ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to!}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex-shrink-0 w-1/5 snap-center flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] transition-colors ${
                  isActive ? 'text-primary font-semibold' : 'text-text-light'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}

          {/* Upload button */}
          <button
            onClick={() => setUploadOpen(true)}
            className="flex-shrink-0 w-1/5 snap-center flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] text-text-light"
          >
            <span className="w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center text-xl shadow-md shadow-primary/30">
              +
            </span>
            <span>上传</span>
          </button>
        </div>
      </div>

      <UploadPanel open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </>
  );
}
