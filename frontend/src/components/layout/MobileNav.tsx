import { NavLink } from 'react-router-dom';

const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export default function MobileNav() {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex justify-around items-center h-14 bg-white/90 backdrop-blur-xl border-t border-misty px-2 pb-1">
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
    </nav>
  );
}
