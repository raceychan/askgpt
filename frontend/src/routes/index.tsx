import { createFileRoute } from '@tanstack/react-router'
import React from "react";

import SessionComponent from "@/components/gpt/SessionComponent";

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


export const Route = createFileRoute('/')({
  component: HomePage,
})
