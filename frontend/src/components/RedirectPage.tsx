import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRedirectInfo } from '../api';
import { Loader2, ArrowRight, ArrowLeft, ShieldCheck, Zap, Tv, Crown, Undo2 } from 'lucide-react';
import WebApp from '@twa-dev/sdk';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const RedirectPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{ affiliate_url: string; title: string; is_monetized?: boolean } | null>(null);
  const [countdown, setCountdown] = useState(3);
  const [showAdNotice, setShowAdNotice] = useState(false);
  const [redirected, setRedirected] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getRedirectInfo(Number(id));
        setData(result);
        setLoading(false);
        // Si es monetizado, mostrar aviso de anuncios
        if (result.is_monetized) {
          setShowAdNotice(true);
        }
      } catch (err) {
        setError('Failed to fetch redirect info.');
        setLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);

  useEffect(() => {
    // Solo iniciar countdown si NO se muestra el aviso de anuncios
    if (!loading && data && countdown > 0 && !showAdNotice) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown, loading, data, showAdNotice]);

  const handleOpenLink = (url: string, isMonetized: boolean) => {
    if (isMonetized) {
      // Estrategia 1: Intentar con WebApp.openLink (oficial)
      try {
        // Nota: El SDK estándar usa try_instant_view, pero pasamos el objeto por si acaso
        // @ts-ignore
        WebApp.openLink(url, { try_browser: 'chrome' });
      } catch (e) {
        console.warn('WebApp.openLink falló, usando fallbacks', e);
      }
      
      // Estrategia 2: Fallback con window.open (intenta abrir pestaña nueva fuera del iframe)
      const newWindow = window.open(url, '_blank', 'noopener,noreferrer');
      
      // Estrategia 3: Fallback final si los anteriores no dispararon navegación top-level
      if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
        window.location.href = url;
      }
    } else {
      // Para VIP o enlaces no monetizados, comportamiento estándar
      WebApp.openLink(url);
    }
    setRedirected(true);
  };

  const handleAcceptAds = () => {
    setShowAdNotice(false);
    if (data) {
      handleOpenLink(data.affiliate_url, true);
    }
  };

  const handleContinue = () => {
    if (data) {
      handleOpenLink(data.affiliate_url, !!data.is_monetized);
      if (!data.is_monetized) {
        navigate(-1);
      }
    }
  };

  if (redirected) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center mb-6">
          <ShieldCheck className="w-10 h-10 text-green-500" />
        </div>
        <h2 className="text-2xl font-black text-white mb-2">¡Enlace abierto!</h2>
        <p className="text-white/40 mb-10 text-sm">Ya puedes ver el contenido en tu navegador o Telegram.</p>
        <button 
          onClick={() => navigate(-1)}
          className="w-full max-w-xs py-4 bg-white text-black font-black rounded-2xl active:scale-95 transition-all shadow-xl shadow-white/5"
        >
          Volver a la App
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-6" />
        <h2 className="text-xl font-bold text-white">Preparando tu enlace...</h2>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center p-6 text-center">
        <div className="bg-red-500/10 border border-red-500/20 p-8 rounded-3xl">
          <h2 className="text-xl font-bold text-red-500 mb-2">Oops!</h2>
          <p className="text-white/60 mb-6">{error || 'Something went wrong.'}</p>
          <button 
            onClick={() => navigate(-1)}
            className="px-6 py-2 bg-white text-black rounded-xl font-bold"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Modal de aviso de anuncios para usuarios free
  if (showAdNotice) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center p-6 overflow-hidden relative">
        {/* Visible Back Button */}
        <button 
          onClick={() => navigate(-1)}
          className="absolute top-8 left-6 p-4 rounded-2xl bg-white/5 border border-white/10 text-white/50 hover:text-white hover:bg-white/10 transition-all active:scale-90 z-20"
          aria-label="Volver"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>

        <div className="w-full max-w-sm">
          {/* Glassmorphism Card */}
          <div className="relative bg-white/[0.06] backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
            {/* Glow effect */}
            <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-40 h-40 bg-[#0088cc]/30 rounded-full blur-3xl pointer-events-none" />
            
            {/* Icon */}
            <div className="relative flex justify-center mb-6">
              <div className="w-20 h-20 rounded-3xl bg-[#0088cc]/20 flex items-center justify-center border border-[#0088cc]/20">
                <Tv className="w-10 h-10 text-[#0088cc]" />
              </div>
            </div>

            {/* Title */}
            <h2 className="text-2xl font-black text-white text-center mb-3">
              Preparando tu enlace...
            </h2>

            {/* Message */}
            <p className="text-white/50 text-center text-sm leading-relaxed mb-8">
              Para ofrecerte este contenido gratis, necesitamos que veas{' '}
              <span className="text-[#0088cc] font-bold">2 anuncios breves</span>{' '}
              (menos de 10 segundos).
              <br />
              <span className="text-white/30 mt-2 block">¡Gracias por apoyar la comunidad! 💙</span>
            </p>

            {/* Destination preview */}
            <div className="bg-white/5 border border-white/5 rounded-2xl p-4 mb-6 text-center">
              <p className="text-white/30 text-[10px] uppercase tracking-widest font-bold mb-1">Destino</p>
              <p className="text-white font-bold text-sm truncate">{data.title}</p>
            </div>

            {/* CTA Button */}
            <button
              onClick={handleAcceptAds}
              className="w-full py-4 rounded-2xl font-bold text-base flex items-center justify-center gap-2 bg-[#0088cc] text-white shadow-xl shadow-[#0088cc]/20 active:scale-95 transition-all hover:bg-[#0099dd]"
            >
              Continuar y ver anuncios
              <ArrowRight className="w-5 h-5" />
            </button>

            <button
              onClick={() => navigate(-1)}
              className="w-full mt-4 py-2 text-sm font-medium text-white/30 hover:text-white/50 transition-colors active:scale-95 flex items-center justify-center gap-2"
            >
              <Undo2 className="w-4 h-4" />
              Cancelar y volver
            </button>

            {/* Browser tip */}
            <p className="mt-4 text-[10px] text-white/30 text-center px-4 leading-tight">
              Tip: Si el enlace no carga, asegúrate de activar el <span className="text-white/50">"Navegador Externo"</span> en los ajustes de Telegram o pulsa los 3 puntos y selecciona "Abrir en navegador".
            </p>

            {/* VIP upsell */}
            <div className="mt-6 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-2xl p-4 flex items-start gap-3">
              <Crown className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-white/70 text-xs leading-relaxed">
                  <span className="text-purple-400 font-bold">¿Quieres acceso directo?</span>{' '}
                  Hazte VIP y salta todos los anuncios.
                </p>
              </div>
            </div>
          </div>
        </div>

        <footer className="w-full text-center mt-10 pb-10">
          <p className="text-[10px] text-white/20 uppercase tracking-widest font-bold">
            Powered by TGLinktree Network
          </p>
        </footer>
      </div>
    );
  }

  // Pantalla normal de redirección (para VIP o después de aceptar anuncios)
  return (
    <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-between p-6 overflow-hidden relative">
      <button 
        onClick={() => navigate(-1)}
        className="absolute top-8 left-6 p-4 rounded-2xl bg-white/5 border border-white/10 text-white/50 hover:text-white hover:bg-white/10 transition-all active:scale-90 z-20"
      >
        <ArrowLeft className="w-5 h-5" />
      </button>

      <div className="w-full max-w-sm flex flex-col items-center mt-20">
        <div className="w-20 h-20 rounded-3xl bg-blue-500/20 flex items-center justify-center mb-8 relative">
          <div className="absolute inset-0 bg-blue-500 blur-2xl opacity-20 animate-pulse" />
          <Zap className="w-10 h-10 text-blue-500 fill-current" />
        </div>
        
        <h2 className="text-2xl font-black text-white mb-2">Almost there!</h2>
        <p className="text-white/40 text-center mb-10">
          You are being redirected to:<br/>
          <span className="text-blue-400 font-bold block mt-1">{data.title}</span>
        </p>

        <div className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 mb-8 text-center">
          <ShieldCheck className="w-8 h-8 text-green-500 mx-auto mb-3" />
          <h3 className="text-white font-bold mb-1">Safe Redirect</h3>
          <p className="text-white/40 text-xs">Link verified by TGLinktree Social Service</p>
        </div>

        <button 
          onClick={handleContinue}
          disabled={countdown > 0}
          className={cn(
            "w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 transition-all",
            countdown > 0 
              ? "bg-white/5 text-white/20 border border-white/10" 
              : "bg-blue-600 text-white shadow-xl shadow-blue-600/20 active:scale-95"
          )}
        >
          {countdown > 0 ? `Wait ${countdown}s` : 'Continue to Link'}
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>

      <footer className="w-full text-center pb-10">
        <p className="text-[10px] text-white/20 uppercase tracking-widest font-bold">
          Powered by TGLinktree Network
        </p>
      </footer>
    </div>
  );
};
