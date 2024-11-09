import React from "react";
import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import SessionComponent from "@/app/gpt/session-page";
import useAuth from "@/contexts/auth-context";

const HomePage: React.FC = () => {
  const { user } = useAuth();

  const landing_page = (
    <main>
      <section className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
        <div className="container mx-auto px-6 py-16">
          <div className="flex flex-col md:flex-row items-center">
            <div className="md:w-1/2 mb-8 md:mb-0">
              <h1 className="text-4xl md:text-6xl font-bold mb-4">
                Welcome to AI Chat
              </h1>
              <p className="text-xl mb-6">
                Experience the power of AI-driven conversations with our
                cutting-edge chat application.
              </p>
              <Button asChild>
                <Link
                  to="/login"
                  className="bg-black text-blue-500 hover:bg-blue-100"
                >
                  Start Chatting
                </Link>
              </Button>
            </div>
            {/* <div className="md:w-1/2">
              <img
                src="/ai-chat-illustration.png"
                alt="AI Chat Illustration"
                className="rounded-lg shadow-lg w-full h-auto"
              />
            </div> */}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-100 py-16">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-8">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              title="AI-Powered Conversations"
              description="Engage in intelligent discussions with our advanced AI model."
              icon="🤖"
            />
            <FeatureCard
              title="Multi-Language Support"
              description="Chat in multiple languages with seamless translation."
              icon="🌍"
            />
            <FeatureCard
              title="Customizable Interface"
              description="Personalize your chat experience with customizable themes and settings."
              icon="🎨"
            />
          </div>
        </div>
      </section>
    </main>
  );

  const session_page = (
    <main className="flex-grow container mx-auto p-6">
      <SessionComponent />
    </main>
  );

  return (
    <div className="min-h-screen flex flex-col">
      {user ? session_page : landing_page}
    </div>
  );
};

const FeatureCard: React.FC<{
  title: string;
  description: string;
  icon: string;
}> = ({ title, description, icon }) => (
  <div className="bg-white p-6 rounded-lg shadow-md">
    <div className="text-4xl mb-4">{icon}</div>
    <h3 className="text-xl font-semibold mb-2">{title}</h3>
    <p className="text-gray-600">{description}</p>
  </div>
);

export default HomePage;
