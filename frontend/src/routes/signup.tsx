import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import Signup from "@/components/auth/Signup";

const SignupPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white flex justify-center items-center">
      <Signup />
    </div>
  );
};

export default SignupPage;

export const Route = createFileRoute("/signup")({
  component: SignupPage,
});
