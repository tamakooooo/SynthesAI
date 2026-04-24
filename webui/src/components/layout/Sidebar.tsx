import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navItems = [
  { path: '/link', label: '知识卡片', icon: '📚' },
  { path: '/vocabulary', label: '词汇学习', icon: '📝' },
  { path: '/video', label: '视频总结', icon: '🎬' },
  { path: '/history', label: '学习历史', icon: '📋' },
  { path: '/statistics', label: '学习统计', icon: '📊' },
  { path: '/settings', label: '设置', icon: '⚙️' },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-primary/20 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-60 bg-surface
                    border-r border-border transform transition-transform duration-300
                    ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Logo */}
        <div className="p-lg border-b border-border">
          <Link to="/" className="flex items-center gap-sm">
            <span className="text-2xl">🧠</span>
            <span className="text-h3 font-semibold text-primary">SynthesAI</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="p-md">
          <ul className="space-y-xs">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center gap-sm px-md py-sm rounded-md
                              transition-colors duration-150
                              ${
                                location.pathname === item.path
                                  ? 'bg-highlight-blue text-accent font-medium'
                                  : 'text-secondary hover:bg-surface hover:text-primary'
                              }`}
                  onClick={() => onClose()}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-md border-t border-border">
          <p className="text-sm text-secondary">v0.2.0</p>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;