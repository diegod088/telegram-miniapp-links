import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getPublicProfile } from '../api';
import { 
    Loader2, Link as LinkIcon, Share, Heart, Eye, 
    ShieldCheck, MousePointerClick, ChevronRight,
    AlertCircle, MessageSquare
} from 'lucide-react';
import WebApp from '@twa-dev/sdk';

export const PublicProfilePage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ['publicProfile', slug],
    queryFn: () => getPublicProfile(slug!),
    enabled: !!slug,
    retry: 1
  });

  if (isLoading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#0a0a0b] gap-4">
        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
        <p className="text-white/20 font-black text-[10px] uppercase tracking-[0.3em]">Cargando Enlaces</p>
    </div>
  );

  if (isError || !profile) return (
    <div className="min-h-screen bg-[#0a0a0b] px-6 flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mb-6">
            <AlertCircle className="w-10 h-10 text-red-500" />
        </div>
        <h1 className="text-2xl font-black text-white mb-2">Perfil no encontrado</h1>
        <p className="text-white/40 text-sm mb-10 leading-relaxed">Este usuario no existe o ha desactivado su perfil público.</p>
        <button 
            onClick={() => navigate('/explore')}
            className="px-8 py-4 bg-white text-black font-black rounded-2xl active:scale-95 transition-all"
        >
            Volver al Inicio
        </button>
    </div>
  );

  const stats = {
      views: profile.total_views || 0,
      links: profile.links?.length || 0,
      likes: profile.links?.reduce((sum: number, l: any) => sum + (l.likes || 0), 0) || 0,
      clicks: profile.links?.reduce((sum: number, l: any) => sum + (l.clicks || 0), 0) || 0,
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white px-4 pt-16 pb-32">
       {/* Profile Header Card */}
       <div className="relative bg-white/5 rounded-[40px] border border-white/5 p-8 mb-8 overflow-hidden backdrop-blur-2xl">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/10 blur-[60px] rounded-full translate-x-10 -translate-y-10" />
          
          <div className="flex justify-between items-start mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-[30px] flex items-center justify-center text-3xl font-black text-white shadow-2xl border-4 border-[#0a0a0b]">
                {profile.display_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex gap-2">
                  {profile.contact_username && (
                    <button 
                      onClick={() => WebApp.openTelegramLink(`https://t.me/${profile.contact_username}`)}
                      className="flex items-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black text-xs transition-all active:scale-95 shadow-lg shadow-blue-600/20"
                    >
                      <MessageSquare size={16} />
                      Contactar
                    </button>
                  )}
                  <button 
                    onClick={() => {
                        const url = `https://t.me/TuBot/app?startapp=profile_${profile.slug}`;
                        WebApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(`Mira el perfil de @${profile.slug} en TGLinktree`)}`);
                    }}
                    className="p-3 bg-white/5 rounded-2xl text-white/40 hover:text-white transition-all"
                  >
                    <Share size={20} />
                  </button>
              </div>
          </div>

          <div className="mb-8">
              <div className="flex items-center gap-2 mb-1">
                  <h1 className="text-2xl font-black">{profile.display_name}</h1>
                  <ShieldCheck className="w-5 h-5 text-blue-400" />
              </div>
              <p className="text-blue-500 font-black text-xs uppercase tracking-widest">@{profile.slug}</p>
              {profile.bio && <p className="mt-4 text-white/40 text-sm leading-relaxed">{profile.bio}</p>}
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-black/40 rounded-[20px] p-3 border border-white/5 text-center">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-widest mb-1">Vistas</p>
                <div className="flex items-center justify-center gap-1">
                    <Eye size={12} className="text-blue-400" />
                    <span className="font-black text-sm">{stats.views}</span>
                </div>
            </div>
            <div className="bg-black/40 rounded-[20px] p-3 border border-white/5 text-center">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-widest mb-1">Likes</p>
                <div className="flex items-center justify-center gap-1">
                    <Heart size={12} className="text-pink-500" />
                    <span className="font-black text-sm">{stats.likes}</span>
                </div>
            </div>
            <div className="bg-black/40 rounded-[20px] p-3 border border-white/5 text-center">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-widest mb-1">Links</p>
                <div className="flex items-center justify-center gap-1">
                    <LinkIcon size={12} className="text-emerald-400" />
                    <span className="font-black text-sm">{stats.links}</span>
                </div>
            </div>
          </div>
       </div>

       {/* Links List */}
       <div className="space-y-4">
          <h2 className="text-[10px] font-black text-white/20 uppercase tracking-[0.3em] ml-2 mb-2">Enlaces Publicados</h2>
          {profile.links?.map((link: any) => (
            <button 
              key={link.id}
              onClick={() => navigate(`/r/${link.id}`)}
              className="w-full bg-white/5 border border-white/5 p-5 rounded-[30px] flex items-center gap-4 group hover:bg-white/10 active:scale-[0.98] transition-all text-left"
            >
              <div className="w-14 h-14 bg-black/40 rounded-2xl flex items-center justify-center shrink-0 text-white/20 group-hover:text-blue-500 transition-colors">
                <LinkIcon size={24} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-white font-black text-sm truncate uppercase tracking-tight mb-1">{link.title || 'Enlace'}</h3>
                <div className="flex items-center gap-3 text-white/20 text-[10px] font-black">
                   <span className="flex items-center gap-1"><MousePointerClick size={10} /> {link.clicks}</span>
                   <span className="flex items-center gap-1"><Heart size={10} /> {link.likes}</span>
                </div>
              </div>
              <ChevronRight className="text-white/10 group-hover:text-white transition-colors" />
            </button>
          ))}

          {profile.links?.length === 0 && (
             <div className="py-20 text-center opacity-20">
                <LinkIcon className="mx-auto mb-4 w-12 h-12" />
                <p className="font-black uppercase text-xs tracking-widest">No hay links públicos</p>
             </div>
          )}
       </div>
    </div>
  );
};
