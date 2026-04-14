import React, { useState, useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { getExploreFeed } from '../api';
import { LinkCard } from './LinkCard';
import { useInView } from 'react-intersection-observer';
import { Loader2, Sparkles, Search, X } from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';

const CATEGORIES = ["ALL", "COURSE", "AI_TOOL", "DEAL", "CRYPTO", "OTHER"];

export const ExploreFeed: React.FC = () => {
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
    queryKey: ['explore', category, debouncedQuery],
    queryFn: ({ pageParam }) => getExploreFeed(category, pageParam as any, debouncedQuery),
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    initialPageParam: undefined,
  });

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white p-4 pb-24">
      {/* Header */}
      <header className="flex flex-col gap-6 pt-6 pb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold flex items-center gap-2">
              Explore <Sparkles className="text-yellow-400 w-6 h-6 fill-current" />
            </h1>
            <p className="text-white/40 text-sm font-medium mt-1">Discover the best Telegram links</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 blur-lg opacity-50 animate-pulse" />
        </div>

        {/* Search Bar */}
        <div className="relative group">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <Search className="w-5 h-5 text-white/20 group-focus-within:text-blue-400 transition-colors" />
          </div>
          <input 
            type="text"
            placeholder="Buscar por nombre o contenido..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-12 text-sm focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all placeholder:text-white/20"
          />
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery("")}
              className="absolute inset-y-0 right-4 flex items-center text-white/20 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Categories Bar */}
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide no-scrollbar">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={clsx(
                "px-4 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap border capitalize",
                category === cat 
                  ? "bg-white text-black border-white" 
                  : "bg-white/5 text-white/60 border-white/10 hover:border-white/20"
              )}
            >
              {cat === 'ALL' ? '🔥 Trending' : cat.toLowerCase().replace('_', ' ')}
            </button>
          ))}
        </div>
      </header>

      {/* Grid */}
      {status === 'pending' ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-white/40 font-medium heartbeat">Loading amazing links...</p>
        </div>
      ) : status === 'error' ? (
        <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-2xl text-center">
          <p className="text-red-400">Error loading feed. Please check your connection.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.pages.map((page, i) => (
            <React.Fragment key={i}>
              {page.items.map((link: any) => (
                <LinkCard 
                  key={link.id} 
                  {...link} 
                  onRedirect={(id) => navigate(`/r/${id}`)}
                />
              ))}
            </React.Fragment>
          ))}
        </div>
      )}

      {/* Observer for infinite scroll */}
      <div ref={ref} className="h-10 flex items-center justify-center mt-8">
        {isFetchingNextPage && <Loader2 className="w-6 h-6 text-white/20 animate-spin" />}
      </div>
    </div>
  );
};
