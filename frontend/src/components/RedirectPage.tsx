import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRedirectInfo } from '../api';
import { Loader2, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
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
  const [data, setData] = useState<{ affiliate_url: string; title: string, is_monetized?: boolean } | null>(null);
  const [countdown, setCountdown] = useState(3);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getRedirectInfo(Number(id));
        setData(result);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch redirect info.');
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  useEffect(() => {
    if (!loading && data && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown, loading, data]);

  const handleContinue = () => {
    if (data) {
      if (data.is_monetized) {
        // Enlaces monetizados: fuerza redirección (Linkvertise lo necesita)
        window.location.href = data.affiliate_url;
      } else {
        // Enlaces directos VIP: se mantienen dentro de Telegram (in-app browser)
        WebApp.openLink(data.affiliate_url);
        navigate(-1); // Regresamos atras en la mini app despues de abrir el popup inside Telegram
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-6" />
        <h2 className="text-xl font-bold text-white">Preparing your link...</h2>
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

  return (
    <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-between p-6 overflow-hidden">
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
