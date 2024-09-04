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
  AuthLoginError,
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

  const { data: user, isLoading } = useQuery<PublicUserInfo | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UserService.userGetPublicUser,
    enabled: isLoggedIn(),
  });

  const login = async (email: string, password: string) => {
    const response = await AuthService.authLogin({
      body: { username: email, password: password },
    });
    localStorage.setItem("access_token", response.data.access_token);
  };

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" });
    },
    onError: (error: AuthLoginError) => {
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
