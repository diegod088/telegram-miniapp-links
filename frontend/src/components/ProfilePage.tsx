import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { twMerge } from 'tailwind-merge';
import { clsx, type ClassValue } from 'clsx';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

import { getMyProfile, createProfile, updateProfile, addLink, deleteLink, boostLink, getFavorites } from '../api';
import WebApp from '@twa-dev/sdk';
import { 
    Loader2, Link as LinkIcon, Trash2, PlusCircle, 
    Share, Gem, ArrowUpCircle, Heart, Eye,
    ShieldCheck, MousePointerClick, BarChart3, Bookmark
} from 'lucide-react';
import PaymentModal from './PaymentModal';

const CATEGORIES = ["Educación", "Tecnología", "Entretenimiento", "Finanzas", "Salud", "Arte", "Otros"];

export const ProfilePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  // Profile Form States
  const [slug, setSlug] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [contactUsername, setContactUsername] = useState('');
  const [bio, setBio] = useState('');
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [activeTab, setActiveTab] = useState<'my_links' | 'favorites'>('my_links');

  // Link Form States
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Otros');
  const [description, setDescription] = useState('');

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ['myProfile'],
    queryFn: getMyProfile,
    retry: false
  });

  const { data: favorites, isLoading: isLoadingFavs } = useQuery({
    queryKey: ['favorites'],
    queryFn: getFavorites,
    enabled: activeTab === 'favorites'
  });

  const createProfileMutation = useMutation({
    mutationFn: createProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      WebApp.HapticFeedback.notificationOccurred('success');
    },
    onError: (err: any) => {
        const msg = err?.response?.data?.detail || 'Error creating profile';
        WebApp.showAlert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  });

  const updateProfileMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      WebApp.HapticFeedback.notificationOccurred('success');
      setShowEditProfile(false);
    },
    onError: (err: any) => {
        const msg = err?.response?.data?.detail || 'Error updating profile';
        WebApp.showAlert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  });

  const addLinkMutation = useMutation({
    mutationFn: addLink,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      WebApp.HapticFeedback.notificationOccurred('success');
      setShowAddForm(false);
      setUrl(''); setTitle(''); setDescription('');
    }
  });

  const deleteLinkMutation = useMutation({
    mutationFn: deleteLink,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      WebApp.HapticFeedback.impactOccurred('medium');
    }
  });

  const boostLinkMutation = useMutation({
    mutationFn: boostLink,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      WebApp.HapticFeedback.notificationOccurred('success');
    }
  });

  const stats = useMemo(() => {
    if (!profile) return { links: 0, clicks: 0, likes: 0, views: 0 };
    const links = profile.links || [];
    return {
      links: links.length,
      clicks: links.reduce((sum: number, l: any) => sum + (l.clicks || 0), 0),
      likes: links.reduce((sum: number, l: any) => sum + (l.likes || 0), 0),
      views: profile.total_views || 0,
    };
  }, [profile]);

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0b]">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
    </div>
  );

  if (isError || !profile) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] px-6 pt-16 pb-32">
        <div className="mb-10 text-center relative">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-blue-500/20 blur-[60px] rounded-full" />
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-[28px] flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-blue-500/30 relative">
                <LinkIcon className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-4xl font-black text-white tracking-tighter mb-3 relative">Tu Hub Digital</h1>
            <p className="text-white/40 text-sm font-medium leading-relaxed max-w-[280px] mx-auto relative">
                El lugar definitivo para compartir todos tus canales, redes sociales y grupos exclusivos.
            </p>
        </div>

        <div className="space-y-3 mb-10">
            <div className="bg-white/5 border border-white/5 rounded-3xl p-4 flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-400 shrink-0">
                    <Share size={20} />
                </div>
                <div>
                    <h3 className="font-black text-white text-sm tracking-tight mb-0.5">Centraliza tu audiencia</h3>
                    <p className="text-white/30 text-xs font-medium">Comparte un único enlace en todas partes.</p>
                </div>
            </div>
            <div className="bg-white/5 border border-white/5 rounded-3xl p-4 flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-pink-500/10 flex items-center justify-center text-pink-400 shrink-0">
                    <Heart size={20} />
                </div>
                <div>
                    <h3 className="font-black text-white text-sm tracking-tight mb-0.5">Compite en el Ranking</h3>
                    <p className="text-white/30 text-xs font-medium">Gana likes y destaca en top descubrimientos.</p>
                </div>
            </div>
            <div className="bg-white/5 border border-white/5 rounded-3xl p-4 flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 shrink-0">
                    <BarChart3 size={20} />
                </div>
                <div>
                    <h3 className="font-black text-white text-sm tracking-tight mb-0.5">Mide tu impacto</h3>
                    <p className="text-white/30 text-xs font-medium">Estadísticas detalladas de clics y visitas.</p>
                </div>
            </div>
        </div>
        
        <form onSubmit={(e) => {
            e.preventDefault();
            createProfileMutation.mutate({ slug, display_name: displayName });
        }} className="space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] font-black text-white/30 uppercase tracking-widest ml-1">Nombre Público</label>
            <input 
              required
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              placeholder="Ej: Mi Canal VIP"
              className="w-full bg-white/5 border border-white/10 text-white rounded-2xl px-5 py-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-black text-white/30 uppercase tracking-widest ml-1">ID (Slug)</label>
            <div className="relative group">
               <span className="absolute left-5 top-1/2 -translate-y-1/2 text-white/20 text-sm">@</span>
               <input 
                required
                value={slug}
                onChange={e => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ''))}
                placeholder="usuario"
                className="w-full bg-white/5 border border-white/10 text-white rounded-2xl px-10 py-4 focus:outline-none focus:border-blue-500/50 transition-all placeholder:text-white/10"
              />
            </div>
          </div>
          
          <button 
            type="submit"
            disabled={createProfileMutation.isPending}
            className="w-full bg-white text-black font-black py-5 rounded-2xl active:scale-95 transition-all shadow-xl shadow-white/5 flex items-center justify-center gap-3"
          >
            {createProfileMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Confirmar Registro'}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white px-4 pt-12 pb-40">
      <div className="relative bg-white/5 rounded-[40px] border border-white/5 p-8 mb-8 overflow-hidden backdrop-blur-2xl">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/10 blur-[60px] rounded-full translate-x-10 -translate-y-10" />
          
          <div className="flex justify-between items-start mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-[30px] flex items-center justify-center text-3xl font-black text-white shadow-2xl shadow-blue-500/20 border-4 border-[#0a0a0b]">
                {profile.display_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex gap-2">
                  <button onClick={() => {
                        setDisplayName(profile.display_name);
                        setContactUsername(profile.contact_username || '');
                        setBio(profile.bio || '');
                        setShowEditProfile(!showEditProfile);
                  }} className="p-3 bg-white/5 rounded-2xl hover:bg-white/10 text-white/40 hover:text-white transition-all">
                      {showEditProfile ? 'Cerrar' : 'Editar'}
                  </button>
                  <button onClick={() => {
                        const url = `https://t.me/TuBot/app?startapp=profile_${profile.slug}`;
                        WebApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(`Mira mis links en @${profile.slug}`)}`);
                  }} className="p-3 bg-white/5 rounded-2xl hover:bg-white/10 text-white/40 hover:text-white transition-all"><Share size={20} /></button>
              </div>
          </div>

          <div className="mb-8">
              <div className="flex items-center gap-2 mb-1">
                  <h1 className="text-2xl font-black">{profile.display_name}</h1>
                  {profile.is_verified && <ShieldCheck className="w-5 h-5 text-blue-400" />}
              </div>
              <p className="text-blue-500 font-black text-xs uppercase tracking-widest">@{profile.slug}</p>
          </div>

          {showEditProfile && (
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                updateProfileMutation.mutate({ 
                  display_name: displayName, 
                  contact_username: contactUsername,
                  bio: bio 
                });
              }}
              className="mb-8 space-y-4 bg-black/20 p-6 rounded-3xl border border-white/5 animate-in slide-in-from-top-2 duration-300"
            >
               <div className="space-y-1">
                  <label className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] ml-1">Nombre para mostrar</label>
                  <input 
                    value={displayName} 
                    onChange={e => setDisplayName(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-blue-500/50 outline-none transition-all"
                  />
               </div>
               <div className="space-y-1">
                  <label className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] ml-1">Telegram (@usuario)</label>
                  <input 
                    value={contactUsername} 
                    onChange={e => setContactUsername(e.target.value.replace('@', ''))}
                    placeholder="usuario (sin @)"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-blue-500/50 outline-none transition-all"
                  />
               </div>
               <div className="space-y-1">
                  <label className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] ml-1">Biografía</label>
                  <textarea 
                    value={bio} 
                    onChange={e => setBio(e.target.value)}
                    rows={2}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-blue-500/50 outline-none transition-all resize-none"
                  />
               </div>
               <button 
                  type="submit"
                  disabled={updateProfileMutation.isPending}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-black rounded-xl text-xs flex items-center justify-center gap-2 transition-all active:scale-95"
               >
                  {updateProfileMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : 'Guardar Cambios'}
               </button>
            </form>
          )}

          <div className="grid grid-cols-2 gap-3">
              <div className="bg-black/40 rounded-[24px] p-4 border border-white/5 text-center flex flex-col items-center justify-center">
                  <p className="text-[9px] font-black text-white/20 uppercase tracking-widest mb-1">Vistas Perfil</p>
                  <div className="flex items-center justify-center gap-1.5">
                      <Eye size={16} className="text-blue-400" />
                      <span className="font-black text-xl">{stats.views}</span>
                  </div>
              </div>
              <div className="bg-black/40 rounded-[24px] p-4 border border-white/5 text-center flex flex-col items-center justify-center">
                  <p className="text-[9px] font-black text-white/20 uppercase tracking-widest mb-1">Clics Totales</p>
                  <div className="flex items-center justify-center gap-1.5">
                      <MousePointerClick size={16} className="text-purple-400" />
                      <span className="font-black text-xl">{stats.clicks}</span>
                  </div>
              </div>
              <div className="bg-black/40 rounded-[24px] p-4 border border-white/5 text-center flex flex-col items-center justify-center">
                  <p className="text-[9px] font-black text-white/20 uppercase tracking-widest mb-1">Me Gusta</p>
                  <div className="flex items-center justify-center gap-1.5">
                      <Heart size={16} className="text-pink-500" />
                      <span className="font-black text-xl">{stats.likes}</span>
                  </div>
              </div>
              <button 
                onClick={() => setShowPaymentModal(true)}
                className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[24px] p-4 text-center active:scale-95 transition-all group flex flex-col items-center justify-center"
              >
                  <p className="text-[9px] font-black text-white/40 uppercase tracking-widest mb-1 group-hover:text-white/60 transition-colors">Plan</p>
                  <div className="flex items-center justify-center gap-1.5">
                      <Gem size={16} className="text-white" />
                      <span className="font-black text-xl uppercase">{profile.plan}</span>
                  </div>
              </button>
          </div>
      </div>

      <PaymentModal 
          isOpen={showPaymentModal} 
          onClose={() => setShowPaymentModal(false)} 
          currentPlan={profile.plan} 
      />

      <div className="flex border-b border-white/5 mb-8">
          <button 
            onClick={() => setActiveTab('my_links')}
            className={cn(
                "flex-1 pb-4 text-sm font-black transition-all border-b-2",
                activeTab === 'my_links' ? "border-blue-500 text-white" : "border-transparent text-white/20"
            )}
          >
              MIS ENLACES
          </button>
          <button 
            onClick={() => setActiveTab('favorites')}
            className={cn(
                "flex-1 pb-4 text-sm font-black transition-all border-b-2",
                activeTab === 'favorites' ? "border-blue-500 text-white" : "border-transparent text-white/20"
            )}
          >
              GUARDADOS
          </button>
      </div>

      {activeTab === 'my_links' ? (
        <>
          <div className="flex items-center justify-between mb-6 px-2">
              <h2 className="text-xl font-black tracking-tight">Mis Enlaces <span className="text-white/20 ml-1">{stats.links}</span></h2>
              <button 
                onClick={() => setShowAddForm(!showAddForm)}
                className="bg-blue-600 text-white font-black text-xs px-5 py-3 rounded-2xl flex items-center gap-2 shadow-lg shadow-blue-600/20 active:scale-95 transition-all"
              >
                {showAddForm ? 'Cerrar' : <><PlusCircle size={16} /> Nuevo</>}
              </button>
          </div>

          {showAddForm && (
              <form onSubmit={(e) => {
                  e.preventDefault();
                  addLinkMutation.mutate({ url, title, category, description });
              }} className="bg-white/5 border border-blue-500/20 p-6 rounded-[32px] mb-8 space-y-5 animate-in slide-in-from-top-4 fade-in duration-300">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-1">URL</label>
                  <input required value={url} onChange={e => setUrl(e.target.value)} placeholder="https://..." className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-1">Título</label>
                  <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Título..." className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-1">Categoría</label>
                    <select value={category} onChange={e => setCategory(e.target.value)} className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-xs focus:outline-none focus:border-blue-500">
                      {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px) font-black text-white/20 uppercase tracking-widest ml-1">Descr.</label>
                    <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Breve..." className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500" />
                  </div>
                </div>
                <button type="submit" disabled={addLinkMutation.isPending} className="w-full bg-blue-600 text-white font-black py-4 rounded-xl text-sm active:scale-95 transition-all">
                  {addLinkMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : 'Publicar'}
                </button>
              </form>
          )}

          <div className="space-y-4">
              {profile.links?.map((link: any) => (
                <div key={link.id} className="bg-white/5 border border-white/5 p-5 rounded-[30px] flex items-center gap-4 group hover:bg-white/10 transition-all">
                  <div className="w-14 h-14 bg-black/40 rounded-2xl flex items-center justify-center flex-shrink-0 text-white/20 group-hover:text-blue-500 transition-colors">
                    <LinkIcon size={24} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-white font-black text-sm truncate uppercase tracking-tight mb-1">{link.title || link.url}</h3>
                    <div className="flex items-center gap-3 text-white/20 text-[10px] font-black">
                       <span className="flex items-center gap-1"><MousePointerClick size={10} /> {link.clicks}</span>
                       <span className="flex items-center gap-1"><Heart size={10} /> {link.likes}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => {
                            if(confirm('¿Seguro?')) deleteLinkMutation.mutate(link.id);
                      }}
                      className="p-3 text-white/20 hover:text-red-500 rounded-xl hover:bg-red-500/10 transition-all active:scale-90"
                    >
                      <Trash2 size={18} />
                    </button>
                    <button 
                      onClick={() => boostLinkMutation.mutate(link.id)}
                      className={cn(
                            "p-3 rounded-xl transition-all active:scale-90",
                            link.boosted_until && new Date(link.boosted_until) > new Date() ? "text-yellow-500 bg-yellow-500/10" : "text-white/20 hover:text-blue-400"
                      )}
                    >
                      <ArrowUpCircle size={18} />
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </>
      ) : (
        <div className="space-y-4">
            {isLoadingFavs ? (
                <div className="flex justify-center p-12">
                    <Loader2 className="w-6 h-6 animate-spin text-white/20" />
                </div>
            ) : favorites?.length === 0 ? (
                <div className="text-center p-12 bg-white/5 rounded-[32px] border border-dashed border-white/10">
                    <Bookmark className="w-8 h-8 text-white/10 mx-auto mb-3" />
                    <p className="text-white/20 text-sm font-medium">No has guardado ningún enlace todavía.</p>
                </div>
            ) : (
                favorites?.map((fav: any) => (
                    <div key={fav.id} className="bg-white/5 border border-white/5 p-5 rounded-[30px] flex items-center gap-4 group hover:bg-white/10 transition-all">
                        <div className="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center flex-shrink-0 text-blue-500">
                            <Bookmark size={24} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <h3 className="text-white font-black text-sm truncate uppercase tracking-tight mb-1">{fav.title || fav.url}</h3>
                            <p className="text-white/30 text-[10px] uppercase font-black tracking-widest">por @{fav.username}</p>
                        </div>
                        <button 
                            onClick={() => window.open(fav.url, '_blank')}
                            className="p-3 bg-white/5 rounded-xl hover:bg-white/10 transition-all"
                        >
                            <LinkIcon size={18} />
                        </button>
                    </div>
                ))
            )}
        </div>
      )}
    </div>
  );
};
