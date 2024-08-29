import React from 'react';
import { AuthProvider } from '@/contexts/AuthContext';
import { Outlet } from 'react-router-dom';


const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const AppContent: React.FC = () => {
  return (
    <Outlet />
  );
};



export default App;