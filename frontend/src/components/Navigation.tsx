import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Compass, User, Sparkles } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const tabs = [
    { name: 'Explorar', path: '/explore', icon: Compass },
    { name: 'Mi Perfil', path: '/myprofile', icon: User }
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 p-6 pb-10 bg-gradient-to-t from-[#0a0a0b] via-[#0a0a0b]/80 to-transparent pointer-events-none flex justify-center z-50">
      <div className="bg-[#1a1b1e]/80 backdrop-blur-2xl border border-white/10 rounded-[32px] p-2 flex items-center gap-1 pointer-events-auto shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
        {tabs.map((tab) => {
          const isActive = location.pathname.startsWith(tab.path);
          const Icon = tab.icon;
          
          return (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={cn(
                "group relative flex items-center gap-2 px-8 py-4 rounded-[24px] transition-all duration-300",
                isActive 
                  ? "bg-white text-black shadow-xl" 
                  : "text-white/30 hover:text-white/60 hover:bg-white/5 active:scale-95"
              )}
            >
              <Icon className={cn("w-5 h-5 transition-transform duration-300", isActive ? "scale-110" : "group-hover:scale-110")} />
              <span className="text-xs font-black uppercase tracking-widest">{tab.name}</span>
              
              {isActive && (
                 <div className="absolute -top-1 -right-1">
                    <Sparkles className="w-3 h-3 text-blue-500 animate-pulse" />
                 </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
