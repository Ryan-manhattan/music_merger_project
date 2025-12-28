import React from 'react';

const StatusBar: React.FC = () => {
  return (
    <footer className="fixed bottom-0 left-0 md:left-[280px] right-0 h-[40px] bg-zinc-900/90 backdrop-blur border-t border-zinc-800 flex items-center justify-between px-6 z-30 text-[10px] text-zinc-500 font-mono uppercase tracking-widest">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
            <span className="hidden sm:inline">System_Synced</span>
            <span className="sm:hidden">Ready</span>
        </div>
        <div className="h-3 w-[1px] bg-zinc-700"></div>
        <span className="hidden sm:inline">Latency: 12ms</span>
      </div>
      
      <div className="flex items-center gap-4">
         <span className="opacity-50 hover:opacity-100 cursor-pointer transition-opacity">Terms</span>
         <span className="opacity-50 hover:opacity-100 cursor-pointer transition-opacity">Privacy</span>
         <div className="h-3 w-[1px] bg-zinc-700"></div>
         <span>Node: Archive-01</span>
      </div>
    </footer>
  );
};

export default StatusBar;