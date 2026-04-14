import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMyProfile, createProfile, addLink, deleteLink } from '../api';
import WebApp from '@twa-dev/sdk';
import { Loader2, Link as LinkIcon, Trash2, PlusCircle, UserPlus, Share, Gem, ArrowUpCircle } from 'lucide-react';
import { isAffiliateDomain } from '../utils/affiliates';
import PaymentModal from './PaymentModal';

const CATEGORY_SCOPES = [
  { id: 'OTHER', name: 'General' },
  { id: 'COURSE', name: 'Cursos & Ed.' },
  { id: 'AI_TOOL', name: 'Herramientas AI' },
  { id: 'DEAL', name: 'Ofertas' },
  { id: 'CRYPTO', name: 'Crypto/Web3' },
];

export const ProfilePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  // Profile Form States
  const [slug, setSlug] = useState('');
  const [displayName, setDisplayName] = useState('');

  // Link Form States
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('OTHER');
  const [description, setDescription] = useState('');

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ['myProfile'],
    queryFn: getMyProfile,
    retry: false // Don't retry continuously on 404
  });

  const createProfileMutation = useMutation({
    mutationFn: createProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      try { WebApp.HapticFeedback.notificationOccurred('success'); } catch(_) {}
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const msg = Array.isArray(detail) 
        ? detail.map((d: any) => d.msg || d).join(', ') 
        : (detail || `Error ${err?.response?.status || ''}: ${err?.message || 'Error creando perfil.'}`);
      try { WebApp.showAlert(msg); } catch(_) { alert(msg); }
    }
  });

  const addLinkMutation = useMutation({
    mutationFn: addLink,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      WebApp.HapticFeedback.notificationOccurred('success');
      setShowAddForm(false);
      setUrl('');
      setTitle('');
      setDescription('');
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((d: any) => d.msg || d).join(', ')
        : (detail || 'Error añadiendo enlace.');
      try { WebApp.showAlert(msg); } catch(_) { alert(msg); }
    }
  });

  const deleteLinkMutation = useMutation({
    mutationFn: deleteLink,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      WebApp.HapticFeedback.impactOccurred('medium');
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((d: any) => d.msg || d).join(', ')
        : (detail || 'Error eliminando enlace.');
      try { WebApp.showAlert(msg); } catch(_) { alert(msg); }
    }
  });

  const handleCreateProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (!slug || !displayName) return;
    createProfileMutation.mutate({ slug, display_name: displayName });
  };

  const handleAddLink = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    addLinkMutation.mutate({ url, title, category, description });
  };

  const stats = useMemo(() => {
    const linkViews = profile?.links?.reduce((acc: number, link: any) => acc + (Number(link.views) || 0), 0) || 0;
    return {
      links: profile?.links?.length || 0,
      views: (profile?.total_views || 0) + linkViews,
      upvotes: profile?.links?.reduce((acc: number, link: any) => acc + (Number(link.upvotes) || 0), 0) || 0
    };
  }, [profile]);

  const handleShare = () => {
    const shareText = `🗂️ Mira mi Bóveda de Links en Telegram. Tengo las mejores herramientas y ofertas que he encontrado. ¿Tienes alguna buena? ¡Compártela en mi perfil!`;
    const shareUrl = `https://t.me/TuBot/app?startapp=profile_${profile?.slug || ''}`;
    WebApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen pt-20 flex flex-col items-center justify-center pb-32">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  // Si no tiene perfil o dio error 404 al buscarlo
  if (isError || !profile) {
    return (
      <div className="min-h-screen px-6 pt-10 pb-32 flex flex-col">
        <div className="w-16 h-16 bg-blue-500/20 text-blue-400 rounded-3xl flex items-center justify-center mb-6">
          <UserPlus className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-black text-white mb-2">Crea tu Perfil</h1>
        <p className="text-white/60 mb-8">Elige un nombre y un identificador único (slug) para comenzar a compartir enlaces en la red.</p>
        
        <form onSubmit={handleCreateProfile} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-white/40 uppercase mb-2">Nombre para mostrar</label>
            <input 
              required
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              placeholder="Ej: Canal de Ofertas"
              className="w-full bg-[#1a1b1e] border border-white/10 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-white/40 uppercase mb-2">Enlace único (slug)</label>
            <div className="flex items-center">
              <span className="bg-[#1a1b1e] border border-r-0 border-white/10 text-white/40 rounded-l-xl px-4 py-3">t.me/bot?start=</span>
              <input 
                required
                value={slug}
                onChange={e => {
                  const val = e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/-+/g, '-');
                  setSlug(val);
                }}
                placeholder="mis-ofertas"
                className="w-full bg-[#1a1b1e] border border-white/10 text-white rounded-r-xl px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <p className="text-xs text-white/30 mt-2">Sólo minúsculas, números y guiones. Mínimo 3 caracteres.</p>
          </div>
          
          <button 
            type="submit"
            disabled={createProfileMutation.isPending}
            className="w-full mt-6 bg-blue-600 text-white font-bold py-4 rounded-xl active:scale-95 transition-transform flex items-center justify-center"
          >
            {createProfileMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Registrar Perfil'}
          </button>
        </form>
      </div>
    );
  }

  // Perfil Existente (Con Modo Seguro)
  try {
    return (
      <div className="min-h-screen px-4 pt-10 pb-32">
        {/* Header Bio */}
        <div className="bg-[#1a1b1e]/50 border border-white/5 rounded-3xl p-6 mb-6 text-center backdrop-blur-sm relative overflow-hidden">
          <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-blue-500 to-purple-500" />
          <button 
             onClick={handleShare}
             className="absolute top-4 right-4 bg-white/10 hover:bg-white/20 p-2 rounded-full text-white/70 hover:text-white transition-colors"
          >
             <Share className="w-5 h-5" />
          </button>
          <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full mx-auto mb-4 border-4 border-black flex items-center justify-center text-2xl font-black text-white shadow-2xl shadow-blue-500/20">
            {(profile?.display_name || profile?.slug || '?').charAt(0).toUpperCase()}
          </div>
          <h1 className="text-xl font-black text-white">{profile?.display_name || 'Sin nombre'}</h1>
          <p className="text-blue-400 font-medium text-sm mb-4">@{profile?.slug || 'perfil'}</p>
          <div className="flex items-center gap-2 justify-center text-white/40 text-xs font-bold uppercase">
            <span className="bg-white/5 px-3 py-1 rounded-full">{profile?.category || 'Categoría'}</span>
            <span className="bg-white/5 px-3 py-1 rounded-full">{profile?.total_views || 0} Visitas Gen.</span>
          </div>
        </div>

        {/* Profile Stats */}
        <div className="grid grid-cols-4 gap-2 mb-8">
          <div className="bg-[#1a1b1e]/60 border border-white/5 rounded-2xl p-4 text-center">
            <p className="text-white/40 text-xs font-bold uppercase mb-1">🔗</p>
            <p className="text-white font-black text-xl">{stats.links}</p>
          </div>
          <div className="bg-[#1a1b1e]/60 border border-white/5 rounded-2xl p-4 text-center">
            <p className="text-white/40 text-xs font-bold uppercase mb-1">👀</p>
            <p className="text-white font-black text-xl">{stats.views}</p>
          </div>
          <div className="bg-[#1a1b1e]/60 border border-white/5 rounded-2xl p-4 text-center">
            <p className="text-white/40 text-xs font-bold uppercase mb-1">❤️</p>
            <p className="text-white font-black text-xl">{stats.upvotes}</p>
          </div>
          <button 
            onClick={() => setShowPaymentModal(true)}
            className={`rounded-2xl p-4 text-center border transition-all active:scale-95 ${
              profile?.plan === 'free' 
                ? 'bg-gradient-to-br from-blue-600 to-blue-800 border-blue-400/30' 
                : profile?.plan === 'pro'
                  ? 'bg-gradient-to-br from-purple-600 to-indigo-800 border-purple-400/30'
                  : 'bg-gradient-to-br from-amber-500 to-orange-700 border-amber-400/30'
            }`}
          >
            <p className="text-white/70 text-[10px] font-bold uppercase mb-1 flex items-center justify-center gap-1">
              {profile?.plan === 'free' ? <Gem size={10} /> : <ArrowUpCircle size={10} />}
            </p>
            <p className="text-white font-black text-sm">Plan</p>
          </button>
        </div>

        {/* Payment Modal */}
        <PaymentModal 
          isOpen={showPaymentModal} 
          onClose={() => setShowPaymentModal(false)} 
          currentPlan={profile?.plan || 'free'} 
        />

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-black text-white">Mis Enlaces</h2>
          <button 
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-white/10 hover:bg-white/20 text-white font-bold text-sm px-4 py-2 rounded-full flex items-center gap-2 transition-colors"
          >
            {showAddForm ? 'Cancelar' : <><PlusCircle className="w-4 h-4" /> Añadir</>}
          </button>
        </div>

        {showAddForm && (
          <form onSubmit={handleAddLink} className="bg-[#1a1b1e] border border-blue-500/30 shadow-lg shadow-blue-500/5 p-5 rounded-2xl mb-6 space-y-4 animate-in slide-in-from-top-4 fade-in">
            <div>
              <label className="block text-xs font-bold text-white/40 uppercase mb-2">URL del enlace</label>
              <input 
                required
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://..."
                className="w-full bg-black/50 border border-white/10 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-white/40 uppercase mb-2">Título (opcional)</label>
              <input 
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Deja vacío para auto-detectar"
                className="w-full bg-black/50 border border-white/10 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-white/40 uppercase mb-2">Categoría</label>
                <select 
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 appearance-none"
                >
                  {CATEGORY_SCOPES.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-white/40 uppercase mb-2">Descripción</label>
                <input 
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Corto detalle"
                  className="w-full bg-black/50 border border-white/10 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
            <button 
              type="submit"
              disabled={addLinkMutation.isPending}
              className="w-full mt-2 bg-blue-600 text-white font-bold py-3 rounded-lg text-sm flex items-center justify-center gap-2 active:scale-95 transition-transform"
            >
              {addLinkMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Publicar Enlace'}
            </button>
          </form>
        )}

        {/* Lista de enlaces */}
        <div className="space-y-3">
          {(!profile.links || profile.links.length === 0) && !showAddForm && (
            <div className="text-center py-10 bg-white/5 rounded-2xl border border-white/5 border-dashed">
              <LinkIcon className="w-10 h-10 text-white/20 mx-auto mb-3" />
              <p className="text-white/40 text-sm font-medium">Aún no has añadido ningún enlace.</p>
            </div>
          )}
          
          {profile.links?.map((link: any) => (
            <div key={link.id} className="bg-[#1a1b1e]/80 border border-white/10 p-4 rounded-2xl flex items-center gap-4 group hover:bg-[#25262b]/80 transition-colors">
              <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center flex-shrink-0 text-white/50">
                <LinkIcon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-white font-bold text-sm flex items-center gap-2 truncate">
                  <span className="truncate">{link.title || link.url}</span>
                  {isAffiliateDomain(link.url) && (
                    <span title="Afiliado potencial" className="inline-flex items-center gap-1 bg-yellow-500/20 text-yellow-400 text-[10px] px-2 py-0.5 rounded-full font-black border border-yellow-500/10 flex-shrink-0">
                      💰 Afiliado
                    </span>
                  )}
                </h3>
                <p className="text-white/40 text-xs truncate">{link.url}</p>
              </div>
              <button 
                onClick={() => {
                  if(window.confirm('¿Eliminar este enlace?')) deleteLinkMutation.mutate(link.id);
                }}
                className="p-2 text-white/20 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors flex-shrink-0"
                disabled={deleteLinkMutation.isPending}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  } catch (err: any) {
    console.error("Safe Mode caught error:", err);
    return (
      <div className="min-h-screen pt-20 flex flex-col items-center justify-center px-6 text-center">
        <div className="w-16 h-16 bg-red-500/20 text-red-400 rounded-3xl flex items-center justify-center mb-6">
          <Trash2 className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-black text-white mb-2">Error de Visualización</h1>
        <p className="text-white/60 text-sm mb-8">
          La aplicación encontró un error al renderizar tu perfil.<br/>
          <span className="text-red-400/80 font-mono text-xs break-all">{err.message}</span>
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="bg-white text-black font-bold px-8 py-3 rounded-full active:scale-95 transition-transform"
        >
          Reiniciar App
        </button>
      </div>
    );
  }
};
