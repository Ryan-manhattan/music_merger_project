import React from 'react';
import { ArrowUpRight, Play, BookOpen, Music, Radio, Disc } from 'lucide-react';
import ActivityChart from './ActivityChart';

const Dashboard: React.FC = () => {
  return (
    <div className="p-4 md:p-8 lg:p-12 max-w-7xl mx-auto space-y-8 animate-[fadeIn_0.5s_ease-out]">
      
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-sm border border-border bg-surface/50 p-8 md:p-12">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-6 backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
            Now Trending
          </div>
          <h2 className="text-4xl md:text-6xl font-black text-white tracking-tighter mb-6 leading-[0.9]">
            DIGITAL<br/>
            <span className="text-zinc-600">NOSTALGIA.</span>
          </h2>
          <p className="text-zinc-400 max-w-lg mb-8 text-sm leading-relaxed border-l-2 border-zinc-800 pl-4">
            Welcome to the archive. A curated collection of sonic landscapes and written memories. Dive into the community stream.
          </p>
          <div className="flex flex-wrap gap-4">
            <button className="bg-white text-black px-8 py-3 text-xs font-bold uppercase tracking-widest hover:bg-zinc-200 transition-colors flex items-center gap-2 group">
              Explore Archive
              <ArrowUpRight size={14} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </button>
            <button className="border border-zinc-700 text-white px-8 py-3 text-xs font-bold uppercase tracking-widest hover:border-white transition-colors">
              Write Entry
            </button>
          </div>
        </div>
        
        {/* Abstract background element */}
        <div className="absolute right-0 top-0 h-full w-1/2 opacity-10 pointer-events-none bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white via-transparent to-transparent"></div>
        <div className="absolute -bottom-10 -right-10 opacity-20 rotate-12">
            <Disc size={300} strokeWidth={0.5} />
        </div>
      </section>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
        
        {/* Featured Playlist - Large Card */}
        <div className="col-span-1 md:col-span-8 group relative overflow-hidden bg-zinc-900 border border-zinc-800 hover:border-zinc-600 transition-all duration-500">
           <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent z-10"></div>
           <img 
            src="https://picsum.photos/800/600?grayscale&blur=2" 
            alt="Featured" 
            className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:scale-105 transition-transform duration-700"
           />
           <div className="relative z-20 p-6 h-full flex flex-col justify-end">
             <div className="flex justify-between items-end">
                <div>
                   <p className="text-[10px] text-blue-400 font-mono mb-2 uppercase tracking-widest">Featured Playlist</p>
                   <h3 className="text-2xl md:text-3xl font-bold text-white mb-1">Midnight City Jazz</h3>
                   <p className="text-sm text-zinc-300">Curated by @jazz_cat</p>
                </div>
                <button className="w-12 h-12 rounded-full bg-white text-black flex items-center justify-center hover:scale-110 transition-transform">
                    <Play size={20} fill="currentColor" />
                </button>
             </div>
           </div>
        </div>

        {/* Quick Stats / Activity - Tall Card */}
        <div className="col-span-1 md:col-span-4 bg-zinc-900 border border-zinc-800 p-6 flex flex-col">
            <ActivityChart />
        </div>

        {/* Recent Diary Entries - Medium */}
        <div className="col-span-1 md:col-span-4 bg-zinc-900 border border-zinc-800 p-6 hover:bg-zinc-800/50 transition-colors cursor-pointer group">
            <div className="flex justify-between items-start mb-6">
                <BookOpen size={24} className="text-zinc-600 group-hover:text-white transition-colors" />
                <span className="text-[10px] font-mono text-zinc-600">UPDATED 2M AGO</span>
            </div>
            <h4 className="text-lg font-bold text-white mb-2 group-hover:underline decoration-1 underline-offset-4">The rain never stops</h4>
            <p className="text-xs text-zinc-400 leading-relaxed line-clamp-3">
                Sitting by the window, watching the neon lights reflect off the wet pavement. There's a certain comfort in the sound of rain against glass...
            </p>
            <div className="mt-4 flex gap-2">
                <span className="px-2 py-1 bg-zinc-800 text-[9px] text-zinc-400 uppercase tracking-wider">Melancholy</span>
                <span className="px-2 py-1 bg-zinc-800 text-[9px] text-zinc-400 uppercase tracking-wider">Night</span>
            </div>
        </div>

        {/* Music Video / Visuals - Medium */}
        <div className="col-span-1 md:col-span-4 bg-zinc-900 border border-zinc-800 p-6 hover:bg-zinc-800/50 transition-colors cursor-pointer group">
            <div className="flex justify-between items-start mb-6">
                <Music size={24} className="text-zinc-600 group-hover:text-white transition-colors" />
                <span className="text-[10px] font-mono text-zinc-600">NEW RELEASE</span>
            </div>
            <div className="aspect-video w-full bg-zinc-800 mb-4 overflow-hidden relative">
                <img src="https://picsum.photos/400/225?grayscale" alt="Video thumb" className="w-full h-full object-cover opacity-70" />
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-8 h-8 rounded-full border border-white flex items-center justify-center backdrop-blur-sm">
                        <Play size={12} fill="white" />
                    </div>
                </div>
            </div>
            <h4 className="text-sm font-bold text-white mb-1">Lo-Fi Study Beats Vol. 4</h4>
            <p className="text-[10px] text-zinc-500 uppercase tracking-widest">Visual Studio</p>
        </div>

        {/* Live Status - Medium */}
        <div className="col-span-1 md:col-span-4 bg-gradient-to-br from-zinc-800 to-zinc-900 border border-zinc-700 p-6 relative overflow-hidden">
             <div className="absolute -right-4 -top-4 opacity-10">
                 <Radio size={100} />
             </div>
             <div className="relative z-10">
                 <div className="flex items-center gap-2 mb-2">
                     <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                    </span>
                    <span className="text-[10px] font-bold text-red-400 uppercase tracking-widest">Live On Air</span>
                 </div>
                 <h3 className="text-xl font-bold text-white mb-4">World Cup Voting</h3>
                 <div className="space-y-3">
                     <div className="flex justify-between text-xs text-zinc-300">
                         <span>Classic Rock</span>
                         <span className="font-mono">54%</span>
                     </div>
                     <div className="h-1 w-full bg-zinc-700 rounded-full overflow-hidden">
                         <div className="h-full bg-white w-[54%]"></div>
                     </div>
                     <div className="flex justify-between text-xs text-zinc-500">
                         <span>Modern Jazz</span>
                         <span className="font-mono">46%</span>
                     </div>
                     <div className="h-1 w-full bg-zinc-700 rounded-full overflow-hidden">
                         <div className="h-full bg-zinc-500 w-[46%]"></div>
                     </div>
                 </div>
                 <button className="mt-6 w-full py-2 bg-white/5 border border-white/10 text-xs font-bold uppercase text-white hover:bg-white hover:text-black transition-all">
                     Join Vote
                 </button>
             </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
