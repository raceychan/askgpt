import React from "react";
import { AuthProvider } from "@/contexts/auth-context";
import { Outlet } from "@tanstack/react-router";
import NaviBar from "@/components/layout/navi-bar";
import { Toaster } from "@/components/ui/toaster";

const Header: React.FC = () => {
  return (
    <header>
      <NaviBar />
    </header>
  );
};

const Footer: React.FC = () => {
  return (
    <footer className="mt-auto py-4">
      <p className="text-center text-sm text-zinc-500 dark:text-zinc-400">
        ©{new Date().getFullYear()} Askgpt AI Platform. All Rights Reserved.
      </p>
    </footer>
  );
};

const APPLayout: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow">
        <Outlet />
      </main>
      <Toaster />
      <Footer />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <APPLayout />
    </AuthProvider>
  );
};
export default App;
