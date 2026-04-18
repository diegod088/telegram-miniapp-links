import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';

export const BackButtonHandler: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // List of "Top Level" routes where the Back Button should be hidden
    const topLevelRoutes = ['/explore', '/ranking', '/myprofile'];
    const isTopLevel = topLevelRoutes.includes(location.pathname);

    if (isTopLevel) {
      WebApp.BackButton.hide();
    } else {
      WebApp.BackButton.show();
    }

    const handleBack = () => {
      navigate(-1);
    };

    WebApp.BackButton.onClick(handleBack);

    return () => {
      WebApp.BackButton.offClick(handleBack);
    };
  }, [location.pathname, navigate]);

  return <>{children}</>;
};
