import React, { useEffect } from "react";
import { AuthProvider } from "@/contexts/AuthContext";
import { Outlet } from "@tanstack/react-router";
// import { initializeClient } from "@/config/config";

const App: React.FC = () => {
  // useEffect(() => {
  //   // Initialize the client when the component mounts
  //   initializeClient();
  // }, []); // Empty dependency array means this runs only once when AppContent mounts

  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const AppContent: React.FC = () => {
  return <Outlet />;
};

export default App;
