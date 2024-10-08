import * as React from "react";

import SessionComponent from "@/components/gpt/SessionComponent";
import NaviBar from "@/components/layout/NaviBar";

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-background border-b">
        <NaviBar />
      </header>
      <main className="flex-grow container mx-auto p-6">
        <SessionComponent />
      </main>
    </div>
  );
};

export default HomePage;
