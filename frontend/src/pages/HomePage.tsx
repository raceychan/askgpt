import { useAuth } from "../contexts/AuthContext";
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"


const HomePage: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-background border-b">
        <div className="container mx-auto py-4 px-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold">AskGPT</h1>
          <div className="flex items-center space-x-4">
            <span>Welcome, {user?.name}!</span>
            <Button onClick={logout} variant="outline">Logout</Button>
          </div>
        </div>
      </header>
      <main className="flex-grow container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>Your GPT Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Add components for managing and displaying GPT sessions */}
            <p>Session list and chat interface will go here.</p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default HomePage;