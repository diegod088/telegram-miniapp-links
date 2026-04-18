import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, ExternalLink, ShieldCheck, TrendingUp, ThumbsDown, Star, Sparkles, Bookmark } from 'lucide-react';
import { toggleLike, toggleDislike, toggleFavorite } from '../api';
import { cn } from '../utils/cn';

interface LinkCardProps {
  id: number;
  title: string;
  url: string;
  category: string;
  likes: number;
  dislikes: number;
  clicks: number;
  isVerified: boolean;
  isSponsored: boolean;
  isFeatured: boolean;
  username?: string;
  first_name?: string;
  profileSlug?: string;
  rank?: number;
  thumbnail_url?: string;
  onRedirect: (id: number) => void;
}

export const LinkCard: React.FC<LinkCardProps> = ({
  id,
  title,
  category,
  likes: initialLikes,
  dislikes: initialDislikes,
  clicks,
  isVerified,
  isSponsored,
  isFeatured,
  username,
  first_name,
  profileSlug,
  rank,
  thumbnail_url,
  onRedirect,
}) => {
  const navigate = useNavigate();
  const [likes, setLikes] = useState(initialLikes);
  const [dislikes, setDislikes] = useState(initialDislikes);
  const [isLiked, setIsLiked] = useState(false);
  const [isDisliked, setIsDisliked] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);
  const [isAnimating, setIsAnimating] = useState<string | null>(null);

  const handleAction = async (e: React.MouseEvent, action: 'like' | 'dislike') => {
    e.stopPropagation();
    setIsAnimating(action);
    
    if (action === 'like') {
      const active = !isLiked;
      setIsLiked(active);
      if (isDisliked) {
        setIsDisliked(false);
        setDislikes(prev => prev - 1);
      }
      setLikes(prev => active ? prev + 1 : prev - 1);
      try { await toggleLike(id); } catch { /* Rollback ignored for brevity in MVP */ }
    } else {
      const active = !isDisliked;
      setIsDisliked(active);
      if (isLiked) {
        setIsLiked(false);
        setLikes(prev => prev - 1);
      }
      setDislikes(prev => active ? prev + 1 : prev - 1);
      try { await toggleDislike(id); } catch { }
    }
    
    setTimeout(() => setIsAnimating(null), 500);
  };

  const handleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsAnimating('fav');
    const newState = !isFavorited;
    setIsFavorited(newState);
    try {
      console.log(`Sending toggleFavorite for link ${id}`);
      const res = await toggleFavorite(id);
      console.log(`Favorite response:`, res);
      const twa = (window as any).Telegram?.WebApp;
      if (twa) {
        twa.HapticFeedback.notificationOccurred('success');
      }
    } catch (err: any) {
      console.error('Favorite failed:', err);
      setIsFavorited(!newState); // Rollback
      const errMsg = err.response?.data?.detail || 'Error al guardar. Intenta de nuevo.';
      const twa = (window as any).Telegram?.WebApp;
      if (twa) {
        twa.showAlert(errMsg);
      } else {
        alert(errMsg);
      }
    }
    setTimeout(() => setIsAnimating(null), 500);
  };

  return (
    <div 
      onClick={() => onRedirect(id)}
      className={cn(
        "relative group bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-5 transition-all duration-300 hover:bg-white/10 hover:border-white/20 active:scale-[0.98] cursor-pointer shadow-lg",
        isSponsored && "border-yellow-500/30 bg-yellow-500/5 ring-1 ring-yellow-500/20",
        isFeatured && "border-blue-500/30 bg-blue-500/5"
      )}
    >
      {/* Badges */}
      <div className="flex gap-2 mb-3">
        {isSponsored && (
          <div className="bg-yellow-500 text-black text-[9px] font-black px-2 py-0.5 rounded-md uppercase tracking-tighter flex items-center gap-1 shadow-lg shadow-yellow-500/10">
            <Star className="w-2 h-2 fill-current" /> Promocionado
          </div>
        )}
        {isFeatured && (
          <div className="bg-blue-500 text-white text-[9px] font-black px-2 py-0.5 rounded-md uppercase tracking-tighter flex items-center gap-1 shadow-lg shadow-blue-500/10">
            <Sparkles className="w-2 h-2 fill-current" /> Destacado
          </div>
        )}
        {rank && rank <= 3 && (
          <div className={cn(
            "text-[14px] font-bold px-2 py-0.5 rounded-md shadow-lg",
            rank === 1 ? "bg-yellow-400 text-black" : 
            rank === 2 ? "bg-gray-300 text-black" : 
            "bg-orange-400 text-black"
          )}>
            {rank === 1 ? '🥇 #1' : rank === 2 ? '🥈 #2' : '🥉 #3'}
          </div>
        )}
        {rank && rank > 3 && rank <= 20 && (
          <div className="text-white/20 text-[10px] font-black uppercase tracking-widest flex items-center">
            #{rank}
          </div>
        )}
      </div>
      
      <div className="flex justify-between items-start gap-4">
        <div className="flex items-center gap-4 flex-1">
          {thumbnail_url ? (
            <img 
              src={thumbnail_url} 
              alt={title} 
              className="w-12 h-12 rounded-xl object-cover shrink-0 border border-white/10"
              onError={(e) => {
                (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(title)}&background=random`;
              }}
            />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
               <span className="text-xl font-black text-white/20">{title.charAt(0)}</span>
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="text-[10px] font-black text-white/30 uppercase tracking-widest leading-none">{category}</span>
              {isVerified && <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />}
            </div>
            <h3 className="text-white font-bold text-lg leading-tight line-clamp-2 group-hover:text-blue-400 transition-colors">
              {title}
            </h3>
            <p 
              onClick={(e) => {
                e.stopPropagation();
                if (profileSlug) {
                  navigate(`/${profileSlug}`);
                }
              }}
              className="text-white/30 text-xs mt-2 font-medium cursor-pointer hover:text-white transition-colors"
            >
              por <span className="text-white/50">{first_name || `@${username}` || 'Anónimo'}</span>
            </p>
          </div>
        </div>
        
        {/* Interaction Group */}
        <div className="flex flex-col gap-2">
            <button 
                onClick={(e) => handleAction(e, 'like')}
                className={cn(
                    "flex flex-col items-center justify-center w-12 h-12 rounded-2xl transition-all shadow-lg",
                    isLiked ? "bg-pink-600 text-white shadow-pink-600/20" : "bg-white/5 text-white/40 hover:text-white"
                )}
            >
                <Heart className={cn("w-5 h-5 transition-transform duration-300", isAnimating === 'like' && "scale-125", isLiked && "fill-current")} />
                <span className="text-[10px] font-black mt-0.5">{likes}</span>
            </button>

            <button 
                onClick={(e) => handleAction(e, 'dislike')}
                className={cn(
                    "flex flex-col items-center justify-center w-12 h-12 rounded-2xl transition-all shadow-lg",
                    isDisliked ? "bg-gray-700 text-white" : "bg-white/5 text-white/40 hover:text-white"
                )}
            >
                <ThumbsDown className={cn("w-4 h-4 transition-transform duration-300", isAnimating === 'dislike' && "scale-125", isDisliked && "fill-current")} />
                <span className="text-[10px] font-black mt-0.5">{dislikes}</span>
            </button>

            <button 
                onClick={handleFavorite}
                className={cn(
                    "flex flex-col items-center justify-center w-12 h-12 rounded-2xl transition-all shadow-lg",
                    isFavorited ? "bg-blue-600 text-white shadow-blue-600/20" : "bg-white/5 text-white/40 hover:text-white"
                )}
            >
                <Bookmark className={cn("w-5 h-5 transition-transform duration-300", isAnimating === 'fav' && "scale-125", isFavorited && "fill-current")} />
            </button>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between pt-4 border-t border-white/5">
        <div className="flex items-center gap-3 text-white/20 text-[11px] font-bold">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-green-500/50" />
            <span>{clicks.toLocaleString()} clicks</span>
          </div>
        </div>
        <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400 opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-0 translate-x-2">
          <ExternalLink className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
};
