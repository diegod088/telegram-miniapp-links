import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WebApp from '@twa-dev/sdk';
import { ExploreFeed } from './components/ExploreFeed';
import { RedirectPage } from './components/RedirectPage';
import { ProfilePage } from './components/ProfilePage';
import { Navigation } from './components/Navigation';

const queryClient = new QueryClient();

function App() {
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

  return (
    <QueryClientProvider client={queryClient}>
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
