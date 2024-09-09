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
  user: PublicUserInfo;
  isLoading: boolean;
}
const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const { data: user, isLoading } = useQuery<PublicUserInfo, Error>({
    queryKey: ["currentUser"],
    queryFn: async (): Promise<PublicUserInfo> => {
      const response = await UserService.getPublicUser() as { data: PublicUserInfo };;
      return response.data; // Ensure this returns PublicUserInfo
    },
    enabled: isLoggedIn(),
  }) as { data: PublicUserInfo; isLoading: boolean };

  const login = async (email: string, password: string) => {
    // Shortcut for predefined credentials
    if (email === "john@gmail.com" && password === "111") {
      // Set a dummy token for the shortcut
      localStorage.setItem("access_token", "dummy_access_token");
      navigate({ to: "/" }); // Redirect after successful login
      return;
    }

    const response = await AuthService.login({
      body: { username: email, password: password },
    });

    // Check if response.data is defined before accessing access_token
    if (response.data) {
      localStorage.setItem("access_token", response.data.access_token);
    } else {
      // Handle the case where response.data is undefined
      setError("Login failed: No access token received.");
    }
  };

  const loginMutation = useMutation<void, LoginError, { email: string; password: string }>({
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

  return (
    <AuthContext.Provider
      value={{ login, loginWithGoogle, logout, user, isLoading }}
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
