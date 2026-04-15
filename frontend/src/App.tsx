import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WebApp from '@twa-dev/sdk';
import { ExploreFeed } from './components/ExploreFeed';
import { RedirectPage } from './components/RedirectPage';
import { ProfilePage } from './components/ProfilePage';
import { Navigation } from './components/Navigation';

const queryClient = new QueryClient();

function AgeVerification({ onAccept }: { onAccept: () => void }) {
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
      <div className="bg-white/10 p-8 rounded-3xl border border-white/20 text-center max-w-sm w-full shadow-2xl">
        <div className="text-6xl mb-4">🔞</div>
        <h2 className="text-2xl font-bold mb-4 text-white">Verificación de Edad</h2>
        <p className="text-white/70 mb-8 leading-relaxed">
          Esta aplicación puede contener contenido para adultos. Para continuar, debes confirmar que eres mayor de 18 años.
        </p>
        <button
          onClick={onAccept}
          className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-bold transition-all transform active:scale-95 shadow-lg shadow-blue-600/20"
        >
          Soy mayor de 18 años
        </button>
      </div>
    </div>
  );
}

function App() {
  const [isAdult, setIsAdult] = useState(() => {
    return localStorage.getItem('age_verified') === 'true';
  });

  useEffect(() => {
    // Notify Telegram that the Mini App is ready
    WebApp.ready();
    WebApp.expand();
    
    // Set theme colors
    const colors = WebApp.themeParams;
    if (colors.bg_color) {
      document.body.style.backgroundColor = colors.bg_color;
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('age_verified', 'true');
    setIsAdult(true);
  };

  return (
    <QueryClientProvider client={queryClient}>
      {!isAdult && <AgeVerification onAccept={handleAccept} />}
      <Router>
        <div className="max-w-xl mx-auto min-h-screen shadow-2xl shadow-black/50 relative">
          <Routes>
            <Route path="/explore" element={<ExploreFeed />} />
            <Route path="/myprofile" element={<ProfilePage />} />
            <Route path="/r/:id" element={<RedirectPage />} />
            <Route path="*" element={<Navigate to="/explore" replace />} />
          </Routes>
          
          <Routes>
            <Route path="/explore" element={<Navigation />} />
            <Route path="/myprofile" element={<Navigation />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
