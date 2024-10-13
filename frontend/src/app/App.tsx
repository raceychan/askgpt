import React from "react";
import { AuthProvider } from "@/contexts/AuthContext";
import { Outlet } from "@tanstack/react-router";
import NaviBar from "@/components/layout/NaviBar";

const Header: React.FC = () => {
  return (
    <header>
      <NaviBar />
    </header>
  );
};

const Footer: React.FC = () => {
  return (
    <div className="z-[3] flex flex-col items-center justify-end mt-auto pb-[30px] md:px-0 lg:flex-row">
      <p className="mb-4 text-center text-sm font-medium text-zinc-500 dark:text-zinc-400 sm:!mb-0 md:text-lg">
        <span className="mb-4 text-center text-sm text-zinc-500 dark:text-zinc-400 sm:!mb-0 md:text-sm">
          ©{new Date().getFullYear()} Askgpt AI Platform. All Rights Reserved.
        </span>
      </p>
    </div>
  );
};
const APPLayout: React.FC = () => {
  return (
    <div>
      <Header />
      <Outlet />
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
