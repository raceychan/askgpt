import React, { useEffect } from "react";
import { useAuth } from "@/contexts/auth-context";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { useNavigate } from "@tanstack/react-router";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Separator } from "@/components/ui/separator";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

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

const formSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(1, { message: "Password is required" }),
});

const LoginForm: React.FC = () => {
  const { toast } = useToast();
  const { loginMutation, isLoading } = useAuth();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      await loginMutation.mutateAsync(values);
      toast({
        title: "Login Successful",
        description: `Welcome Back`,
      });
    } catch (error) {
      console.log(error);
      toast({
        title: "Login Failed",
        description: "Please check your credentials and try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent>
          <div className="grid w-full items-center gap-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter your email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder="Enter your password"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          {form.formState.errors.root && (
            <Alert variant="destructive" className="mb-2">
              <AlertTitle className="text-red-600">Login Failed</AlertTitle>
              <AlertDescription className="text-red-600">
                {form.formState.errors.root.message}
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
          {/* <OAuthLogin /> */}
        </CardFooter>
      </form>
    </Form>
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
const LoginPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    if (user) {
      navigate({ to: "/" });
    }
  }, [user, navigate]);

  if (user) {
    return (
      <div className="min-h-screen bg-white flex justify-center items-center">
        <p className="text-lg font-semibold">
          welcome back! You are being redirected to the homepage...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex justify-center items-center">
      <LoginComponent />
    </div>
  );
};

export default LoginPage;
