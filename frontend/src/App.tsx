import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthenticationPage from './pages/AuthentificationPage';
import HomePage from './pages/HomePage';


const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();
  return user ? <HomePage /> : <AuthenticationPage />;
};



export default App;