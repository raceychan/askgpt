import { createFileRoute } from "@tanstack/react-router";
// import LoginPage from '@/pages/LoginPage'
import React, { useEffect } from "react";
import Login from "@/components/auth/Login";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "@tanstack/react-router";

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
      <Login />
    </div>
  );
};

export const Route = createFileRoute("/login")({
  component: LoginPage,
});
