import React, { createContext, useContext } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Config } from "@/config/config";
import { useNavigate } from "@tanstack/react-router";
import { AxiosError } from "axios";
import { useState } from "react";

import {
  AuthService,
  UserService,
  PublicUserInfo,
  LoginError,
} from "@/lib/api";

interface AuthContextType {
  login: (email: string, password: string) => void;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
  signup: (email: string, password: string, userName?: string) => void;
  user: PublicUserInfo;
  isLoading: boolean;
}
const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// type Status = "idle" | "loading" | "error" | "success";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const { data: user, isLoading } = useQuery<PublicUserInfo, Error>({
    queryKey: ["user"],
    queryFn: async (): Promise<PublicUserInfo> => {
      const response = (await UserService.getPublicUser()) as {
        data: PublicUserInfo;
      };
      return response.data; // Ensure this returns PublicUserInfo
    },
    enabled: isLoggedIn(),
  }) as { data: PublicUserInfo; isLoading: boolean };

  const login = async (email: string, password: string) => {
    const response = await AuthService.login({
      body: { username: email, password: password },
    });

    // Check if response.data is defined before accessing access_token
    if (response.data) {
      console.log("Login successful");
      localStorage.setItem("access_token", response.data.access_token);
      navigate({ to: "/" });
    } else {
      // Handle the case where response.data is undefined
      setError("Login failed: No access token received.");
    }
  };

  const loginMutation = useMutation<
    void,
    LoginError,
    { email: string; password: string }
  >({
    mutationFn: ({ email, password }) => login(email, password),
    onSuccess: () => {
      navigate({ to: "/" });
    },
    onError: (error: LoginError) => {
      let errDetail = error.detail as any;

      if (error instanceof AxiosError) {
        errDetail = error.message;
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong";
      }

      setError(errDetail);
    },
  });

  const loginWithGoogle = async (): Promise<void> => {
    window.location.href = `${Config.API_AUTH_URL}/google`;
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    navigate({ to: "/login" });
  };

  const signup = async (email: string, password: string, userName?: string) => {
    try {
      const response = await AuthService.signup({
        body: { user_name: userName, email: email, password: password },
      });
      console.log("Signup successful", response);
      navigate({ to: "/" }); // Redirect after successful signup
    } catch (error) {
      setError("Signup failed: " + (error as AxiosError).message);
    }
  };

  return (
    <AuthContext.Provider
      value={{ login, loginWithGoogle, logout, signup, user, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
