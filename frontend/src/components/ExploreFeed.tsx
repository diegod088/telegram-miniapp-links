import React, { useState, useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { getFeed } from '../api';
import { LinkCard } from './LinkCard';
import { useInView } from 'react-intersection-observer';
import { Loader2, Sparkles, Search, X, TrendingUp, Clock, Filter, BarChart } from 'lucide-react';
import { cn } from '../utils/cn';
import { useNavigate } from 'react-router-dom';


const CATEGORIES = ["ALL", "Educación", "Tecnología", "Entretenimiento", "Finanzas", "Salud", "Arte", "Otros"];

type FeedMode = 'trending' | 'new' | 'top';

export const ExploreFeed: React.FC = () => {
  const [mode, setMode] = useState<FeedMode>('trending');
  const [category, setCategory] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const { ref, inView } = useInView();
  const navigate = useNavigate();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ['feed', mode, category, debouncedQuery],
    queryFn: ({ pageParam }) => {
        // Hybrid pagination logic
        const params: any = { mode, category, q: debouncedQuery };
        if (mode === 'new') {
            params.cursor = pageParam as unknown as string;
        } else {
            params.page = pageParam as number;
        }
        return getFeed(mode, category, params.cursor, params.page, debouncedQuery);
    },
    getNextPageParam: (lastPage) => {
        if (mode === 'new') return lastPage.next_cursor;
        return lastPage.next_page;
    },
    initialPageParam: mode === 'new' ? undefined : 1,
  });

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  const modeIcons = {
    trending: <TrendingUp className="w-4 h-4" />,
    new: <Clock className="w-4 h-4" />,
    top: <BarChart className="w-4 h-4" />
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white p-4 pb-32">
      {/* Premium Header */}
      <header className="flex flex-col gap-6 pt-8 pb-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black tracking-tighter flex items-center gap-2">
              Explore <Sparkles className="text-blue-500 w-8 h-8 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]" />
            </h1>
            <p className="text-white/30 text-xs font-bold uppercase tracking-widest mt-1">Global Discovery Hub</p>
          </div>
          <div className="relative">
             <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-purple-600 animate-pulse opacity-20 blur-xl absolute inset-0" />
             <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center backdrop-blur-md relative">
                <Filter className="w-5 h-5 text-white/40" />
             </div>
          </div>
        </div>

        {/* Persistent Search Bar */}
        <div className="relative group">
          <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none">
            <Search className="w-5 h-5 text-white/10 group-focus-within:text-blue-500 transition-colors" />
          </div>
          <input 
            type="text"
            placeholder="Search keywords, categories, bots..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-[24px] py-5 pl-14 pr-14 text-sm font-medium focus:outline-none focus:border-blue-500/30 focus:bg-white/10 focus:ring-4 focus:ring-blue-500/5 transition-all placeholder:text-white/10"
          />
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery("")}
              className="absolute inset-y-0 right-5 flex items-center text-white/20 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* View Mode Switcher */}
        <div className="flex bg-white/5 p-1.5 rounded-2xl border border-white/5 backdrop-blur-md">
            {(['trending', 'new', 'top'] as FeedMode[]).map((m) => (
                <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={cn(
                        "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-black uppercase tracking-tighter transition-all",
                        mode === m 
                            ? "bg-white text-black shadow-xl scale-100" 
                            : "text-white/40 hover:text-white/60 hover:bg-white/5 scale-95"
                    )}
                >
                    {modeIcons[m]}
                    {m}
                </button>
            ))}
        </div>

        {/* Sub-Categories Horizontal Scroll */}
        <div className="flex gap-2 overflow-x-auto pb-4 -mx-4 px-4 scrollbar-hide no-scrollbar">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={cn(
                "px-5 py-2.5 rounded-full text-[10px] font-black transition-all whitespace-nowrap border uppercase tracking-widest",
                category === cat 
                  ? "bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-600/20" 
                  : "bg-white/5 text-white/30 border-white/5 hover:border-white/10"
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </header>

      {/* Dynamic Feed Grid */}
      {status === 'pending' ? (
        <div className="flex flex-col items-center justify-center py-32 gap-6">
          <div className="relative">
             <div className="w-20 h-20 rounded-full border-4 border-blue-500/10 border-t-blue-500 animate-spin" />
             <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-blue-500 animate-pulse" />
             </div>
          </div>
          <p className="text-white/20 font-black text-xs uppercase tracking-[0.3em] animate-pulse">Syncing Network</p>
        </div>
      ) : status === 'error' ? (
        <div className="bg-red-500/5 border border-red-500/10 p-10 rounded-3xl text-center backdrop-blur-md">
          <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <X className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-xl font-bold mb-2">Connection Lost</h3>
          <p className="text-white/40 text-sm">We couldn't reach the matrix. Try again in a moment.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5">
          {data?.pages.map((page, i) => (
            <React.Fragment key={i}>
              {page.items.map((link: any) => (
                <LinkCard 
                  key={link.id} 
                  id={link.id}
                  title={link.title}
                  url={link.url}
                  category={link.category}
                  likes={link.likes}
                  dislikes={link.dislikes}
                  clicks={link.clicks}
                  isVerified={link.is_verified}
                  isSponsored={link.is_sponsored}
                  isFeatured={link.is_featured}
                  username={link.username}
                  first_name={link.first_name}
                  onRedirect={(id) => navigate(`/r/${id}`)}
                />
              ))}
            </React.Fragment>
          ))}
          
          {/* Empty state */}
          {data?.pages[0].items.length === 0 && (
            <div className="text-center py-20 opacity-20">
                <Search className="w-12 h-12 mx-auto mb-4" />
                <p className="font-bold">No results found in {mode}</p>
            </div>
          )}
        </div>
      )}

      {/* Infinite Scroll Trigger */}
      <div ref={ref} className="h-32 flex items-center justify-center">
        {isFetchingNextPage && (
            <div className="flex items-center gap-2 px-6 py-3 bg-white/5 rounded-full border border-white/5 backdrop-blur-md">
                <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                <span className="text-[10px] font-black uppercase tracking-widest text-white/40">Loading more</span>
            </div>
        )}
      </div>
    </div>
  );
};
