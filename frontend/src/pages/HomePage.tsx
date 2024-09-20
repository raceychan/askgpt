import { useAuth } from "../contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { useNavigate } from "@tanstack/react-router";
import SessionComponent from "@/components/gpt/SessionComponent"; // Import the new component

const HomePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Button variant="default" onClick={() => navigate({ to: "/login" })}>
          Welcome to the home page, please login to continue
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-background border-b">
        <div className="container mx-auto py-4 px-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold">AskGPT</h1>
          <div className="flex items-center space-x-4">
            <span>Welcome, {user?.email}!</span>
            <Button onClick={logout} variant="outline">
              Logout
            </Button>
          </div>
        </div>
      </header>
      <main className="flex-grow container mx-auto p-6">
        <SessionComponent /> {/* Use the new SessionComponent */}
      </main>
    </div>
  );
};

export default HomePage;
