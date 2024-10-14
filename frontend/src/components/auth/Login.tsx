import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { FaGoogle } from "react-icons/fa";

const OAuthLogin: React.FC = () => {
  const { toast } = useToast();
  const { loginWithGoogle, isLoading } = useAuth();

  const handleOAuthLogin = async (provider: string) => {
    try {
      switch (provider) {
        case "google":
          await loginWithGoogle();
          break;
        // case "github":
        //   await loginWithGithub();
        //   break;
        // case "twitter":
        //   await loginWithTwitter();
        //   break;
        default:
          console.error("Unknown provider:", provider);
      }
    } catch (error) {
      console.error(`${provider} login failed:`, error);
      toast({
        title: `${provider} login failed`,
        description: (error as Error).message,
        variant: "destructive",
      });
    }
    toast({
      title: `${provider} login successful`,
      description: "You have been logged in",
    });
  };

  return (
    <div className="w-full">
      <Separator className="my-4" />
      <p className="text-center text-sm text-gray-500 mb-4">Or continue with</p>
      <div className="flex justify-center space-x-4">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="w-10 h-10"
          onClick={() => handleOAuthLogin("google")}
          disabled={isLoading}
        >
          <FaGoogle className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
};

const LoginForm: React.FC = () => {
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { loginMutation, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await loginMutation.mutateAsync({ email, password });
    } catch (error) {
      console.log(error);
      setError("Please check your credentials and try again.");
      toast({
        title: "Login Failed",
        description: "Please check your credentials and try again.",
        variant: "destructive",
      });
    }
    toast({
      title: "Login Successful",
      description: `Welcome Back`,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardContent>
        <div className="grid w-full items-center gap-4">
          <div className="flex flex-col space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex flex-col gap-4">
        {error && (
          <Alert variant="destructive" className="mb-2">
            <AlertTitle className="text-red-600">Login Failed</AlertTitle>
            <AlertDescription className="text-red-600">
              {error}
            </AlertDescription>
          </Alert>
        )}
        <Button
          type="submit"
          className="w-full border-2 border-primary"
          disabled={isLoading}
        >
          {isLoading ? "Logging in..." : "Log In"}
        </Button>
        <div className="text-center text-sm text-gray-500">
          Don't have an account?{" "}
          <Button
            type="button"
            variant="link"
            className="p-0 h-auto text-primary"
            onClick={() => (window.location.href = "/signup")}
          >
            Sign Up
          </Button>
        </div>
        <OAuthLogin />
      </CardFooter>
    </form>
  );
};

const LoginComponent: React.FC = () => {
  return (
    <div className="flex justify-center items-center h-screen">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle>Login</CardTitle>
          <CardDescription>
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>
        <LoginForm />
      </Card>
    </div>
  );
};

export default LoginComponent;
