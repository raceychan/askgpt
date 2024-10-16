import React from "react";

import SessionComponent from "@/app/gpt/session-page";

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow container mx-auto p-6">
        <SessionComponent />
      </main>
    </div>
  );
};

export default HomePage;
