import React from "react";
import { AuthProvider } from "@/contexts/AuthContext";
import { Outlet } from "@tanstack/react-router";
import NaviBar from "@/components/layout/NaviBar";

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const AppContent: React.FC = () => {
  return (
    <div>
      <header className="border">
        <NaviBar />
      </header>
      <Outlet />
    </div>
  );
};

export default App;
