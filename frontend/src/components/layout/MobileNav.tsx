import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import UploadPanel from '../../UploadPanel';

const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
];

const TABS_AFTER = [
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export default function MobileNav() {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <>
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 grid grid-cols-6 items-end h-14 bg-white/90 backdrop-blur-xl border-t border-misty pb-1">
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

        {/* Upload button — centered, slightly elevated */}
        <button
          onClick={() => setUploadOpen(true)}
          className="flex flex-col items-center text-[10px] text-text-light"
        >
          <span className="w-11 h-11 -mt-3 bg-primary text-white rounded-full flex items-center justify-center text-xl shadow-lg shadow-primary/30">
            +
          </span>
          <span className="-mt-0.5">上传</span>
        </button>

        {TABS_AFTER.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
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
      </nav>

      <UploadPanel open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </>
  );
}
