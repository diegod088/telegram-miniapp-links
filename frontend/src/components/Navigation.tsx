import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Compass, User } from 'lucide-react';
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
    <div className="fixed bottom-0 left-0 right-0 p-4 pb-6 bg-gradient-to-t from-black via-black/90 to-transparent pointer-events-none flex justify-center z-50">
      <div className="bg-[#1a1b1e]/90 backdrop-blur-xl border border-white/10 rounded-full p-1 flex items-center gap-2 pointer-events-auto shadow-2xl">
        {tabs.map((tab) => {
          const isActive = location.pathname.startsWith(tab.path);
          const Icon = tab.icon;
          
          return (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={cn(
                "flex items-center gap-2 px-6 py-3 rounded-full transition-all text-sm font-bold",
                isActive 
                  ? "bg-white/10 text-white shadow-inner" 
                  : "text-white/40 hover:text-white/70 hover:bg-white/5 active:scale-95"
              )}
            >
              <Icon className={cn("w-5 h-5", isActive ? "text-blue-400" : "text-white/40")} />
              {tab.name}
            </button>
          );
        })}
      </div>
    </div>
  );
};
