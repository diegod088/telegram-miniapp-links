import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getFeaturedProfiles } from '../api';
import { Sparkles, ShieldCheck, ChevronRight } from 'lucide-react';
import { cn } from '../utils/cn';
import { useNavigate } from 'react-router-dom';

export const FeaturedCarousel: React.FC = () => {
    const navigate = useNavigate();
    const { data: profiles, isLoading } = useQuery({
        queryKey: ['featuredProfiles'],
        queryFn: getFeaturedProfiles,
        staleTime: 1000 * 60 * 5 // 5 minutes
    });

    if (isLoading) return (
        <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide no-scrollbar -mx-4 px-4">
            {[1, 2, 3].map(i => (
                <div key={i} className="min-w-[160px] h-[210px] bg-white/5 rounded-[32px] animate-pulse border border-white/5" />
            ))}
        </div>
    );

    if (!profiles || profiles.length === 0) return null;

    return (
        <div className="space-y-4 mb-8">
            <div className="flex items-center justify-between px-2">
                <h2 className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em] flex items-center gap-2">
                    <Sparkles size={12} className="text-yellow-500" />
                    VIP Showcase
                </h2>
            </div>
            
            <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide no-scrollbar -mx-4 px-4 snap-x snap-mandatory">
                {profiles.map((p: any) => (
                    <div 
                        key={p.slug}
                        onClick={() => navigate(`/p/${p.slug}`)}
                        className={cn(
                            "relative min-w-[160px] h-[210px] bg-gradient-to-b from-white/10 to-transparent rounded-[32px] p-5 border border-white/10 transition-all active:scale-95 snap-center flex flex-col items-center justify-center text-center group cursor-pointer",
                            p.plan === 'business' ? "border-yellow-500/30 ring-1 ring-yellow-500/10" : "border-blue-500/20"
                        )}
                    >
                        {/* Status Badge */}
                        <div className="absolute top-4 right-4">
                            {p.plan === 'business' ? (
                                <div className="w-6 h-6 rounded-lg bg-yellow-500/10 flex items-center justify-center text-yellow-500">
                                    <Sparkles size={12} />
                                </div>
                            ) : (
                                <div className="w-6 h-6 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500">
                                    <ShieldCheck size={12} />
                                </div>
                            )}
                        </div>

                        {/* Avatar / Initial */}
                        <div className="w-16 h-16 rounded-[24px] bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-2xl font-black mb-4 shadow-xl border-4 border-white/5 group-hover:scale-110 transition-transform">
                            {p.display_name.charAt(0).toUpperCase()}
                        </div>

                        <h3 className="text-sm font-black text-white line-clamp-1 mb-1">{p.display_name}</h3>
                        <p className="text-[9px] font-black text-white/20 uppercase tracking-widest mb-4">@{p.slug}</p>
                        
                        <div className="mt-auto px-4 py-1.5 bg-white/10 rounded-full text-[8px] font-black text-white/40 group-hover:bg-blue-600 group-hover:text-white transition-all flex items-center gap-1">
                            VER PERFIL <ChevronRight size={10} />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
