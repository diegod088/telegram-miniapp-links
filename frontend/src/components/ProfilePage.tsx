import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

import { getMyProfile, createProfile, addLink, deleteLink, boostLink, updateProfile } from '../api';
import WebApp from '@twa-dev/sdk';
import { 
    Loader2, Link as LinkIcon, Trash2, PlusCircle, UserPlus, 
    Share, Gem, ArrowUpCircle, Heart, ThumbsDown, Eye, Settings, 
    ExternalLink, Sparkles, ShieldCheck
} from 'lucide-react';
import PaymentModal from './PaymentModal';

const CATEGORIES = ["Educación", "Tecnología", "Entretenimiento", "Finanzas", "Salud", "Arte", "Otros"];

export const ProfilePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Profile Form States
  const [slug, setSlug] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');

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
      setShowSettings(false);
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

  const stats = useMemo(() => {
    if (!profile) return { links: 0, clicks: 0, likes: 0, dislikes: 0 };
    return {
      links: profile.links?.length || 0,
      clicks: profile.total_clicks || 0,
      likes: profile.total_likes || 0,
      dislikes: profile.links?.reduce((acc: number, l: any) => acc + (l.dislikes || 0), 0) || 0
    };
  }, [profile]);

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0b]">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
    </div>
  );

  if (isError || !profile) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] px-6 pt-20 pb-32">
        <div className="w-20 h-20 bg-blue-500/10 rounded-[32px] flex items-center justify-center mb-8 border border-blue-500/20">
          <UserPlus className="w-10 h-10 text-blue-500" />
        </div>
        <h1 className="text-4xl font-black text-white tracking-tighter mb-4">Empezar ahora</h1>
        <p className="text-white/30 text-sm font-medium leading-relaxed mb-10">Crea tu identidad digital única para empezar a compartir y monetizar tus enlaces en Telegram.</p>
        
        <form onSubmit={(e) => {
            e.preventDefault();
            createProfileMutation.mutate({ slug, display_name: displayName, bio });
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
            <label className="text-[10px] font-black text-white/30 uppercase tracking-widest ml-1">ID de Perfil (Slug)</label>
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
      {/* Header Profile Dashboard */}
      <div className="relative bg-white/5 rounded-[40px] border border-white/5 p-8 mb-8 overflow-hidden backdrop-blur-2xl">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/10 blur-[60px] rounded-full translate-x-10 -translate-y-10" />
          
          <div className="flex justify-between items-start mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-[30px] flex items-center justify-center text-3xl font-black text-white shadow-2xl shadow-blue-500/20 border-4 border-[#0a0a0b]">
                {profile.display_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex gap-2">
                  <button onClick={() => setShowSettings(true)} className="p-3 bg-white/5 rounded-2xl hover:bg-white/10 text-white/40 hover:text-white transition-all"><Settings size={20} /></button>
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
              {profile.bio && <p className="text-white/40 text-sm mt-3 leading-relaxed">{profile.bio}</p>}
          </div>

          {/* Atomic Stats Grid */}
          <div className="grid grid-cols-3 gap-3">
              <div className="bg-black/40 rounded-[24px] p-4 border border-white/5 text-center">
                  <p className="text-[9px] font-black text-white/20 uppercase tracking-widest mb-1">Impacto</p>
                  <div className="flex items-center justify-center gap-1.5">
                      <Eye size={12} className="text-blue-400" />
                      <span className="font-black text-lg">{stats.clicks}</span>
                  </div>
              </div>
              <div className="bg-black/40 rounded-[24px] p-4 border border-white/5 text-center">
                  <p className="text-[9px] font-black text-white/20 uppercase tracking-widest mb-1">Popular</p>
                  <div className="flex items-center justify-center gap-1.5">
                      <Heart size={12} className="text-pink-500" />
                      <span className="font-black text-lg">{stats.likes}</span>
                  </div>
              </div>
              <button 
                onClick={() => setShowPaymentModal(true)}
                className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[24px] p-4 text-center active:scale-95 transition-all group"
              >
                  <p className="text-[9px] font-black text-white/40 uppercase tracking-widest mb-1 group-hover:text-white/60 transition-colors">Plan</p>
                  <div className="flex items-center justify-center gap-1.5">
                      <Gem size={12} className="text-white" />
                      <span className="font-black text-lg uppercase">{profile.plan}</span>
                  </div>
              </button>
          </div>
      </div>

      <PaymentModal 
          isOpen={showPaymentModal} 
          onClose={() => setShowPaymentModal(false)} 
          currentPlan={profile.plan} 
      />

      {/* Main Actions */}
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
          }} className="bg-white/5 border border-blue-500/20 shadow-2xl p-6 rounded-[32px] mb-8 space-y-5 animate-in slide-in-from-top-4 fade-in duration-300">
            <div className="space-y-2">
              <label className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-1">URL de Destino</label>
              <input required value={url} onChange={e => setUrl(e.target.value)} placeholder="https://t.me/ejemplo" className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-1">Título Visual</label>
              <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Auto-detectar..." className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-1">Categoría</label>
                <select value={category} onChange={e => setCategory(e.target.value)} className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-xs focus:outline-none focus:border-blue-500 appearance-none">
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-1">Descripción</label>
                <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Opcional..." className="w-full bg-black/50 border border-white/10 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500" />
              </div>
            </div>
            <button type="submit" disabled={addLinkMutation.isPending} className="w-full bg-blue-600 text-white font-black py-4 rounded-xl text-sm shadow-xl shadow-blue-600/10 active:scale-95 transition-all">
              {addLinkMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : 'Publicar'}
            </button>
          </form>
      )}

      {/* Link Inventory */}
      <div className="space-y-4">
          {stats.links === 0 && !showAddForm && (
            <div className="text-center py-20 bg-white/5 rounded-[40px] border border-white/5 border-dashed">
              <LinkIcon className="w-12 h-12 text-white/10 mx-auto mb-4" />
              <p className="text-white/20 font-black text-xs uppercase tracking-widest">El inventario está vacío</p>
            </div>
          )}
          
          {profile.links?.map((link: any) => (
            <div key={link.id} className="bg-white/5 border border-white/5 p-5 rounded-[30px] flex items-center gap-4 group hover:bg-white/10 transition-all">
              <div className="w-14 h-14 bg-black/40 rounded-2xl flex items-center justify-center flex-shrink-0 text-white/20 group-hover:text-blue-500 transition-colors">
                <LinkIcon size={24} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                   <h3 className="text-white font-black text-sm truncate uppercase tracking-tight">{link.title || 'Enlace sin título'}</h3>
                   {link.is_sponsored && <span className="bg-yellow-500 text-black text-[8px] font-black px-1.5 py-0.5 rounded-sm">AD</span>}
                </div>
                <div className="flex items-center gap-3 text-white/20 text-[10px] font-black">
                   <span className="flex items-center gap-1"><Eye size={10} /> {link.clicks}</span>
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
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};
