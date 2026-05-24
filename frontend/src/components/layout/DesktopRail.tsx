import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import UploadPanel from '../../UploadPanel';

const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/favorites', label: '收藏', icon: '❤️' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export default function DesktopRail() {
  const [expanded, setExpanded] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <>
      <nav
        className={`hidden md:flex flex-col fixed left-0 top-0 h-full bg-[#faf7f7] border-r border-misty z-50 transition-all duration-200 ${
          expanded ? 'w-[200px]' : 'w-14'
        }`}
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
      >
        <div className="flex items-center h-14 px-3 border-b border-misty">
          <span className="text-xl">🌸</span>
          {expanded && (
            <span className="ml-2 text-sm font-semibold text-text whitespace-nowrap overflow-hidden">
              HomeMemories
            </span>
          )}
        </div>

        <div className="flex flex-col gap-1 p-2 flex-1">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-btn transition-colors ${
                  isActive
                    ? 'bg-primary/20 text-primary font-semibold'
                    : 'text-text-light hover:bg-misty/50'
                }`
              }
            >
              <span className="text-lg flex-shrink-0">{tab.icon}</span>
              {expanded && (
                <span className="text-sm whitespace-nowrap overflow-hidden">{tab.label}</span>
              )}
            </NavLink>
          ))}
        </div>

        {/* Upload button */}
        <button
          onClick={() => setUploadOpen(true)}
          className="flex items-center gap-3 px-3 py-2.5 mx-2 mb-3 rounded-btn bg-primary text-white hover:opacity-90 transition-opacity"
        >
          <span className="text-lg flex-shrink-0">+</span>
          {expanded && <span className="text-sm whitespace-nowrap overflow-hidden">上传</span>}
        </button>
      </nav>

      <UploadPanel open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </>
  );
}
