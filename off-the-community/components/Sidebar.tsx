import React from 'react';
import { NavItem } from '../types';
import { LogOut, User as UserIcon, ChevronRight } from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  activeTab: string;
  navItems: NavItem[];
  onNavigate: (id: string) => void;
  onClose: () => void;
  currentUser?: { username: string } | null;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  activeTab, 
  navItems, 
  onNavigate, 
  onClose,
  currentUser 
}) => {
  return (
    <>
      {/* Mobile Overlay */}
      <div 
        className={`fixed inset-0 bg-black/80 backdrop-blur-sm z-40 transition-opacity duration-300 md:hidden ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      />

      {/* Sidebar Container */}
      <aside 
        className={`fixed top-0 left-0 h-full w-[280px] bg-background border-r border-border z-50 transform transition-transform duration-500 cubic-bezier(0.22, 1, 0.36, 1) flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Header */}
        <div className="p-8 border-b border-dashed border-border group cursor-pointer">
          <div className="flex items-center gap-2 mb-4 opacity-50">
             <div className="w-1.5 h-1.5 bg-primary animate-pulse"></div>
             <span className="text-[10px] font-mono tracking-[0.2em] uppercase">System_Online</span>
          </div>
          <h1 className="text-3xl font-black tracking-tighter leading-[0.85] text-white group-hover:text-secondary transition-colors duration-300">
            OFF THE<br />COMMUNITY
          </h1>
          <p className="mt-3 text-[10px] text-secondary font-mono tracking-widest uppercase border-l-2 border-border pl-3">
            Sentimental Archive
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-6 space-y-1 overflow-y-auto">
          <div className="text-[10px] text-zinc-600 font-mono mb-4 px-2 uppercase tracking-widest">Directory</div>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            const Icon = item.icon;
            
            return (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id);
                  if (window.innerWidth < 768) onClose();
                }}
                className={`w-full group flex items-center justify-between p-3 rounded-none transition-all duration-300 border-l-2 ${
                  isActive 
                    ? 'bg-white/5 border-primary text-primary' 
                    : 'border-transparent text-secondary hover:text-white hover:bg-white/[0.02]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={16} className={isActive ? 'opacity-100' : 'opacity-60'} />
                  <span className="text-xs font-bold tracking-widest uppercase">{item.label}</span>
                </div>
                {item.isNew && (
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                )}
                {isActive && (
                   <ChevronRight size={14} className="animate-pulse" />
                )}
              </button>
            );
          })}
        </nav>

        {/* User Status / Footer */}
        <div className="p-6 border-t border-border bg-zinc-950/50">
          {currentUser ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-zinc-900 border border-zinc-800">
                <div className="w-8 h-8 bg-zinc-800 flex items-center justify-center">
                   <UserIcon size={14} className="text-zinc-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[9px] uppercase text-zinc-500 tracking-wider">Logged In As</div>
                  <div className="text-xs font-bold truncate text-white">{currentUser.username}</div>
                </div>
              </div>
              <button className="w-full py-3 border border-zinc-700 hover:bg-white hover:text-black hover:border-white transition-all duration-300 text-[10px] font-bold tracking-[0.2em] flex items-center justify-center gap-2">
                <LogOut size={12} />
                DISCONNECT
              </button>
            </div>
          ) : (
             <button className="w-full py-4 bg-white text-black hover:bg-zinc-200 transition-colors duration-300 text-xs font-black tracking-[0.2em]">
                ACCESS SYSTEM
              </button>
          )}
          
          <div className="mt-6 flex justify-between items-end text-[9px] text-zinc-600 font-mono">
             <span>V.2.0.4</span>
             <span>© 2025</span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
