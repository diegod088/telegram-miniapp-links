import React, { useState, useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { getProfileRanking } from '../api';
import { useInView } from 'react-intersection-observer';
import { Loader2, Sparkles, Trophy, Heart, Eye, Crown, ExternalLink } from 'lucide-react';
import { cn } from '../utils/cn';
import { useNavigate } from 'react-router-dom';

const CATEGORIES = ["ALL", "Educación", "Tecnología", "Entretenimiento", "Finanzas", "Salud", "Arte", "Otros"];

type SortMode = 'likes' | 'views';

interface RankingProfile {
  slug: string;
  display_name: string;
  bio?: string;
  avatar_url?: string;
  plan: string;
  link_count: number;
  total_views: number;
  total_likes: number;
  category?: string;
}

const slugToColor = (slug: string) => {
  let hash = 0;
  for (let i = 0; i < slug.length; i++) hash = slug.charCodeAt(i) + ((hash << 5) - hash);
  return `hsl(${Math.abs(hash) % 360}, 70%, 50%)`;
};

const slugToGradient = (slug: string) => {
  let hash = 0;
  for (let i = 0; i < slug.length; i++) hash = slug.charCodeAt(i) + ((hash << 5) - hash);
  const h1 = Math.abs(hash) % 360;
  const h2 = (h1 + 40) % 360;
  return `linear-gradient(135deg, hsl(${h1}, 70%, 50%), hsl(${h2}, 80%, 40%))`;
};

const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(w => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();
};

const formatNumber = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
};

const LIMIT = 20;

export const RankingPage: React.FC = () => {
  const [sortBy, setSortBy] = useState<SortMode>('likes');
  const [category, setCategory] = useState("ALL");
  const { ref, inView } = useInView();
  const navigate = useNavigate();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ['ranking', sortBy, category],
    queryFn: ({ pageParam }) => {
      return getProfileRanking(sortBy, category, LIMIT, pageParam as number);
    },
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.has_more ? allPages.length * LIMIT : undefined;
    },
    initialPageParam: 0,
  });

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  const handleViewProfile = (slug: string) => {
    navigate(`/p/${slug}`);
  };

  // Flatten all profiles across pages with a global index
  const allProfiles: RankingProfile[] = data?.pages.flatMap(p => p.profiles) ?? [];

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white p-4 pb-32">
      {/* ═══════════ HEADER ═══════════ */}
      <header className="flex flex-col gap-6 pt-8 pb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black tracking-tighter flex items-center gap-2">
              Ranking <Trophy className="text-yellow-500 w-8 h-8 drop-shadow-[0_0_15px_rgba(234,179,8,0.5)]" />
            </h1>
            <p className="text-white/30 text-xs font-bold uppercase tracking-widest mt-1">Top Profiles</p>
          </div>
          <div className="relative">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-yellow-600 to-orange-600 animate-pulse opacity-20 blur-xl absolute inset-0" />
            <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center backdrop-blur-md relative">
              <Crown className="w-5 h-5 text-yellow-500/60" />
            </div>
          </div>
        </div>

        {/* ═══════════ SORT TOGGLE ═══════════ */}
        <div className="flex bg-white/5 p-1.5 rounded-2xl border border-white/5 backdrop-blur-md">
          <button
            onClick={() => setSortBy('likes')}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-black uppercase tracking-tighter transition-all",
              sortBy === 'likes'
                ? "bg-white text-black shadow-xl scale-100"
                : "text-white/40 hover:text-white/60 hover:bg-white/5 scale-95"
            )}
          >
            <Heart className="w-4 h-4" />
            Más Likes
          </button>
          <button
            onClick={() => setSortBy('views')}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-black uppercase tracking-tighter transition-all",
              sortBy === 'views'
                ? "bg-white text-black shadow-xl scale-100"
                : "text-white/40 hover:text-white/60 hover:bg-white/5 scale-95"
            )}
          >
            <Eye className="w-4 h-4" />
            Más Vistas
          </button>
        </div>

        {/* ═══════════ CATEGORY SCROLL ═══════════ */}
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

      {/* ═══════════ CONTENT ═══════════ */}
      {status === 'pending' ? (
        <div className="flex flex-col items-center justify-center py-32 gap-6">
          <div className="relative">
            <div className="w-20 h-20 rounded-full border-4 border-blue-500/10 border-t-blue-500 animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-blue-500 animate-pulse" />
            </div>
          </div>
          <p className="text-white/20 font-black text-xs uppercase tracking-[0.3em] animate-pulse">Loading Ranking</p>
        </div>
      ) : status === 'error' ? (
        <div className="bg-red-500/5 border border-red-500/10 p-10 rounded-3xl text-center backdrop-blur-md">
          <div className="text-5xl mb-4">⚠️</div>
          <h3 className="text-xl font-bold mb-2">Error al cargar</h3>
          <p className="text-white/40 text-sm">No pudimos cargar el ranking. Intenta de nuevo.</p>
        </div>
      ) : allProfiles.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <div className="text-6xl">🏜️</div>
          <p className="text-white/30 font-bold text-sm">No hay perfiles aún</p>
          <p className="text-white/15 text-xs">Sé el primero en aparecer en el ranking</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {allProfiles.map((profile, index) => {
            const position = index + 1;

            // Medal styles
            const medalColors: Record<number, { bg: string; border: string; text: string; glow: string }> = {
              1: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/40', text: 'text-yellow-400', glow: 'shadow-yellow-500/20' },
              2: { bg: 'bg-gray-300/15', border: 'border-gray-300/30', text: 'text-gray-300', glow: 'shadow-gray-300/10' },
              3: { bg: 'bg-amber-700/20', border: 'border-amber-700/40', text: 'text-amber-600', glow: 'shadow-amber-700/10' },
            };
            const medal = medalColors[position];
            const isTopThree = position <= 3;

            const primaryMetric = sortBy === 'likes' ? profile.total_likes : profile.total_views;
            const primaryLabel = sortBy === 'likes' ? 'likes' : 'vistas';
            const primaryIcon = sortBy === 'likes'
              ? <Heart className="w-3.5 h-3.5" />
              : <Eye className="w-3.5 h-3.5" />;

            const secondaryMetric = sortBy === 'likes' ? profile.total_views : profile.total_likes;
            const secondaryLabel = sortBy === 'likes' ? 'vistas' : 'likes';

            return (
              <div
                key={profile.slug}
                className={cn(
                  "relative group bg-white/[0.04] border rounded-3xl p-4 transition-all duration-300 hover:bg-white/[0.07]",
                  isTopThree
                    ? `${medal.border} ${medal.glow} shadow-lg`
                    : "border-white/[0.06]"
                )}
              >
                <div className="flex items-center gap-4">
                  {/* Position Badge */}
                  <div
                    className={cn(
                      "w-10 h-10 rounded-2xl flex items-center justify-center text-sm font-black shrink-0 border",
                      isTopThree
                        ? `${medal.bg} ${medal.border} ${medal.text}`
                        : "bg-white/5 border-white/10 text-white/30"
                    )}
                  >
                    {position <= 3 ? ['🥇', '🥈', '🥉'][position - 1] : `#${position}`}
                  </div>

                  {/* Avatar */}
                  <div className="w-12 h-12 rounded-2xl overflow-hidden shrink-0 border border-white/10 relative">
                    {profile.avatar_url ? (
                      <img
                        src={profile.avatar_url}
                        alt={profile.display_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div
                        className="w-full h-full flex items-center justify-center text-white font-black text-sm"
                        style={{ background: slugToGradient(profile.slug) }}
                      >
                        {getInitials(profile.display_name)}
                      </div>
                    )}
                    {/* Animated ring for top 3 */}
                    {isTopThree && (
                      <div
                        className="absolute inset-0 rounded-2xl border-2 animate-pulse"
                        style={{ borderColor: slugToColor(profile.slug) + '40' }}
                      />
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-bold text-sm text-white truncate">{profile.display_name}</span>
                      {profile.plan !== 'free' && (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-yellow-500/15 border border-yellow-500/25 text-yellow-400 text-[9px] font-black uppercase tracking-wider shrink-0">
                          <Crown className="w-2.5 h-2.5" />
                          VIP
                        </span>
                      )}
                    </div>
                    {profile.category && (
                      <span className="text-[10px] text-white/25 font-bold uppercase tracking-widest">{profile.category}</span>
                    )}
                  </div>

                  {/* Main Metric */}
                  <div className="text-right shrink-0">
                    <div className={cn(
                      "flex items-center gap-1.5 font-black text-lg",
                      isTopThree ? medal.text : "text-white"
                    )}>
                      {primaryIcon}
                      {formatNumber(primaryMetric)}
                    </div>
                    <p className="text-white/20 text-[10px] font-bold uppercase tracking-wider">{primaryLabel}</p>
                  </div>
                </div>

                {/* Bottom Row: secondary stat + view button */}
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/[0.04]">
                  <div className="flex items-center gap-4">
                    <span className="text-white/25 text-[10px] font-bold">
                      {formatNumber(secondaryMetric)} {secondaryLabel}
                    </span>
                    <span className="text-white/15 text-[10px]">•</span>
                    <span className="text-white/25 text-[10px] font-bold">
                      {profile.link_count} links
                    </span>
                  </div>
                  <button
                    onClick={() => handleViewProfile(profile.slug)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest bg-white/5 border border-white/10 text-white/50 hover:text-white hover:bg-white/10 active:scale-95 transition-all"
                  >
                    Ver Perfil
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ═══════════ INFINITE SCROLL TRIGGER ═══════════ */}
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
