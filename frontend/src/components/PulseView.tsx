import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPulse } from '../api';
import { X, Zap, UserPlus, TrendingUp, Sparkles, Clock, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface PulseViewProps {
    isOpen: boolean;
    onClose: () => void;
}

const timeAgo = (date: string) => {
    const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000);
    if (seconds < 60) return 'hace momentos';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `hace ${minutes}m`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `hace ${hours}h`;
    return new Date(date).toLocaleDateString();
};

export const PulseView: React.FC<PulseViewProps> = ({ isOpen, onClose }) => {
    const navigate = useNavigate();
    const { data: activities, isLoading } = useQuery({
        queryKey: ['pulseFeed'],
        queryFn: getPulse,
        enabled: isOpen,
        refetchInterval: 1000 * 30 // 30 seconds
    });

    if (!isOpen) return null;

    const activityIcons: Record<string, any> = {
        profile_creation: <UserPlus className="text-emerald-400" />,
        link_trending: <TrendingUp className="text-blue-400" />,
        vip_boost: <Sparkles className="text-yellow-400" />,
        new_favorite: <Zap className="text-purple-400" />,
    };

    return (
        <div className="fixed inset-0 z-50 flex flex-col bg-[#0a0a0b] animate-in fade-in slide-in-from-bottom-4 duration-300">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-white/5 bg-black/40 backdrop-blur-xl">
                <div>
                   <h2 className="text-2xl font-black flex items-center gap-3">
                      Comunidad <span className="bg-blue-600 text-white text-[10px] px-2 py-0.5 rounded-full uppercase tracking-widest animate-pulse">Pulse</span>
                   </h2>
                   <p className="text-white/20 text-[10px] font-bold uppercase tracking-widest mt-1">Actividad en tiempo real</p>
                </div>
                <button onClick={onClose} className="p-3 bg-white/5 rounded-2xl text-white/40"><X size={20} /></button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 opacity-20">
                        <Zap className="w-10 h-10 animate-pulse" />
                        <p className="font-black text-xs uppercase tracking-widest">Sincronizando...</p>
                    </div>
                ) : activities?.length === 0 ? (
                    <div className="text-center py-20 opacity-20">
                        <Clock size={40} className="mx-auto mb-4" />
                        <p className="font-bold">Todo está tranquilo por ahora...</p>
                    </div>
                ) : (
                    activities?.map((a: any) => (
                        <div 
                            key={a.id} 
                            onClick={() => {
                                if (a.target_type === 'profile') navigate(`/p/${a.target_id}`);
                                if (a.target_type === 'link') navigate(`/explore`);
                                onClose();
                            }}
                            className="bg-white/5 border border-white/5 rounded-[28px] p-5 flex gap-4 active:scale-95 transition-all group cursor-pointer hover:bg-white/10"
                        >
                            <div className="w-12 h-12 bg-black/40 rounded-2xl flex items-center justify-center shrink-0 shadow-inner">
                                {activityIcons[a.type] || <Zap className="text-blue-400" />}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-bold text-white leading-relaxed mb-2 line-clamp-2">
                                    {a.message}
                                </p>
                                <div className="flex items-center gap-2 text-white/20 text-[10px] font-black uppercase tracking-tighter">
                                    <span>{timeAgo(a.created_at)}</span>
                                    {a.target_id && (
                                        <>
                                            <span className="w-1 h-1 bg-white/10 rounded-full" />
                                            <span className="text-blue-500/50 flex items-center gap-1 group-hover:text-blue-400">Ver más <ChevronRight size={10} /></span>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Bottom Info */}
            <div className="p-6 text-center border-t border-white/5 bg-black/20">
                <p className="text-[9px] font-black text-white/10 uppercase tracking-[0.4em]">Actualizando cada 30 seg</p>
            </div>
        </div>
    );
};
