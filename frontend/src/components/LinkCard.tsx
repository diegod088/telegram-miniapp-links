import React, { useState } from 'react';
import { Heart, ExternalLink, ShieldCheck, TrendingUp } from 'lucide-react';
import { upvoteLink } from '../api';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: any[]) {
  return twMerge(clsx(inputs));
}

interface LinkCardProps {
  id: number;
  title: string;
  url: string;
  category: string;
  upvotes: number;
  views: number;
  isVerified: boolean;
  isSponsored: boolean;
  username?: string;
  onRedirect: (id: number) => void;
}

export const LinkCard: React.FC<LinkCardProps> = ({
  id,
  title,
  category,
  upvotes: initialUpvotes,
  views,
  isVerified,
  isSponsored,
  username,
  onRedirect,
}) => {
  const [upvotes, setUpvotes] = useState(initialUpvotes);
  const [isUpvoted, setIsUpvoted] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const handleUpvote = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsAnimating(true);
    // Optimistic update
    const newUpvoted = !isUpvoted;
    setIsUpvoted(newUpvoted);
    setUpvotes(prev => newUpvoted ? prev + 1 : prev - 1);
    
    try {
      await upvoteLink(id);
    } catch (err) {
      // Rollback
      setIsUpvoted(!newUpvoted);
      setUpvotes(prev => !newUpvoted ? prev + 1 : prev - 1);
    } finally {
      setTimeout(() => setIsAnimating(false), 500);
    }
  };

  return (
    <div 
      onClick={() => onRedirect(id)}
      className={cn(
        "relative group bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-4 transition-all hover:bg-white/10 hover:border-white/20 active:scale-[0.98] cursor-pointer",
        isSponsored && "border-yellow-500/30 bg-yellow-500/5"
      )}
    >
      {isSponsored && (
        <div className="absolute -top-3 left-4 bg-yellow-500 text-black text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
          Sponsored
        </div>
      )}
      
      <div className="flex justify-between items-start gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">{category}</span>
            {isVerified && <ShieldCheck className="w-3 h-3 text-blue-400" />}
          </div>
          <h3 className="text-white font-medium text-lg leading-snug line-clamp-2 group-hover:text-blue-400 transition-colors">
            {title}
          </h3>
          <p className="text-white/40 text-xs mt-1">@{username || 'anonymous'}</p>
        </div>
        
        <button 
          onClick={handleUpvote}
          className={cn(
            "flex flex-col items-center gap-1 p-2 rounded-xl transition-all",
            isUpvoted ? "bg-red-500/20 text-red-500" : "bg-white/5 text-white/60 hover:text-white"
          )}
        >
          <Heart className={cn("w-5 h-5 transition-transform", isAnimating && "scale-125", isUpvoted && "fill-current")} />
          <span className="text-xs font-bold">{upvotes}</span>
        </button>
      </div>

      <div className="mt-4 flex items-center justify-between pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 text-white/40 text-[10px] font-medium">
          <div className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            <span>{views} views</span>
          </div>
        </div>
        <div className="text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
          <ExternalLink className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
};
