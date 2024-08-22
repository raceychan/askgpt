import React from 'react';
import Login from '../components/auth/Login';

const AuthenticationPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white flex justify-center items-center">
      <Login />
    </div>
  );
};

export default AuthenticationPage;