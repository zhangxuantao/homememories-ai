import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import UploadPanel from '../../UploadPanel';

const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export default function MobileNav() {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <>
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 grid grid-cols-5 items-end h-14 bg-white/90 backdrop-blur-xl border-t border-misty pb-1 relative">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 text-[10px] transition-colors ${
                isActive ? 'text-primary font-semibold' : 'text-text-light'
              }`
            }
          >
            <span className="text-lg">{tab.icon}</span>
            <span>{tab.label}</span>
          </NavLink>
        ))}

        {/* Upload button — centered, elevated above the bar */}
        <button
          onClick={() => setUploadOpen(true)}
          className="absolute left-1/2 -translate-x-1/2 -top-5 flex flex-col items-center text-[10px] text-text-light"
        >
          <span className="w-12 h-12 bg-primary text-white rounded-full flex items-center justify-center text-2xl shadow-lg shadow-primary/40">
            +
          </span>
          <span className="mt-0.5">上传</span>
        </button>
      </nav>

      <UploadPanel open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </>
  );
}
