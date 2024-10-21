import React from "react";
import { useAuth } from "@/contexts/auth-context";
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
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const formSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z
    .string()
    .min(6, { message: "Password must be at least 8 characters" }),
});

const Signup: React.FC = () => {
  const { signup, isLoading, authError } = useAuth();
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    signup(values.email, values.password);
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle>Sign Up</CardTitle>
          <CardDescription>Create an account to get started</CardDescription>
        </CardHeader>
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
              {authError && (
                <Alert variant="destructive" className="mb-2">
                  <AlertTitle className="text-red-600">
                    Signup Failed
                  </AlertTitle>
                  <AlertDescription className="text-red-600">
                    {authError.detail}
                  </AlertDescription>
                </Alert>
              )}
              <Button
                type="submit"
                className="w-full border-2 border-primary"
                disabled={isLoading}
              >
                {isLoading ? "Signing up..." : "Sign Up"}
              </Button>
              <Separator className="flex-grow bg-black" />
              <span className="px-2 text-sm text-gray-500">
                Already have an account?
              </span>
              <Button
                type="button"
                className="w-full border-2 border-secondary"
                onClick={() => (window.location.href = "/login")}
              >
                Log In
              </Button>
            </CardFooter>
          </form>
        </Form>
      </Card>
    </div>
  );
};

const SignupPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white flex justify-center items-center">
      <Signup />
    </div>
  );
};

export default SignupPage;
