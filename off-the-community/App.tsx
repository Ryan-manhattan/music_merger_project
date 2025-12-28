import React, { useState, useEffect } from 'react';
import { 
  Disc, 
  BookOpen, 
  Trophy, 
  Music, 
  Film, 
  Menu 
} from 'lucide-react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import StatusBar from './components/StatusBar';
import { NavItem, User } from './types';

// Mock Data
const NAV_ITEMS: NavItem[] = [
  { id: 'archive', label: 'Song Archive', icon: Disc, path: '/playlists' },
  { id: 'diary', label: 'Diary Community', icon: BookOpen, path: '/diary' },
  { id: 'worldcup', label: 'World Cup', icon: Trophy, path: '/worldcup', isNew: true },
  { id: 'studio', label: 'Music Studio', icon: Music, path: '/music-studio' },
  { id: 'video', label: 'Video Studio', icon: Film, path: '/music-video' },
];

const MOCK_USER: User = {
  username: 'Pixel_Traveler',
  avatar: '',
  role: 'user'
};

const App: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('archive');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-background text-primary font-sans selection:bg-white selection:text-black">
      
      {/* Sidebar */}
      <Sidebar 
        isOpen={isSidebarOpen}
        activeTab={activeTab}
        navItems={NAV_ITEMS}
        onNavigate={setActiveTab}
        onClose={() => setIsSidebarOpen(false)}
        currentUser={MOCK_USER}
      />

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-background/80 backdrop-blur border-b border-border flex items-center justify-between px-4 z-30">
        <button 
            onClick={toggleSidebar}
            className="p-2 border border-zinc-700 hover:bg-white hover:text-black transition-colors"
        >
            <Menu size={20} />
        </button>
        <span className="text-sm font-bold tracking-widest">OFF THE COMMUNITY</span>
        <div className="w-8"></div> {/* Spacer for balance */}
      </div>

      {/* Main Content Area */}
      <main 
        className="transition-all duration-300 min-h-screen flex flex-col"
        style={{ 
            marginLeft: window.innerWidth >= 768 ? '280px' : '0',
            paddingTop: window.innerWidth >= 768 ? '0' : '64px',
            paddingBottom: '40px' // Space for StatusBar
        }}
      >
        {/* Breadcrumb / Top Bar (Desktop) */}
        <div className="hidden md:flex h-16 border-b border-border items-center justify-between px-8 bg-background/50 backdrop-blur sticky top-0 z-20">
           <div className="flex items-center gap-2 text-xs font-mono text-zinc-500 uppercase tracking-widest">
              <span>Home</span>
              <span>/</span>
              <span className="text-white">{NAV_ITEMS.find(i => i.id === activeTab)?.label || 'Dashboard'}</span>
           </div>
           <div className="flex items-center gap-4">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-[10px] font-mono text-zinc-400">SERVER STATUS: STABLE</span>
           </div>
        </div>

        {/* Dynamic Content */}
        <div className="flex-1">
             {/* For demo purposes, we mostly render the Dashboard which is the "Landing Page" redesign requested. 
                 In a real app, this would be a Switch/Router. */}
             <Dashboard />
        </div>
      </main>

      {/* Footer Status Bar */}
      <StatusBar />
      
    </div>
  );
};

export default App;
