import { StrictMode } from "react";
import {
  RouterProvider,
  createRouter,
  createRootRoute,
  createRoute,
} from "@tanstack/react-router";
import ReactDOM from "react-dom/client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "@/app/App.tsx";
import HomePage from "@/pages/HomePage.tsx";
import LoginPage from "@/pages/LoginPage.tsx";
import SignupPage from "@/pages/SignUpPage";
import ChatRoot from "@/pages/ChatRootPage";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";

import "@/index.css";
import ChatPage from "./pages/ChatPage";

const queryClient = new QueryClient();

const rootRoute = createRootRoute({
  component: () => (
    <>
      <App />
      <TanStackRouterDevtools />
    </>
  ),
});

// Define child routes
const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: HomePage,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});

const signupRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/signup",
  component: SignupPage,
});

const chatRootRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/chat",
  component: ChatRoot,
});

const chatRoute = createRoute({
  getParentRoute: () => chatRootRoute,
  path: "$chatId",
  component: ChatPage,
});

// Create the router
const routeTree = rootRoute.addChildren([
  homeRoute,
  loginRoute,
  signupRoute,
  chatRootRoute,
  chatRoute,
]);
const router = createRouter({ routeTree });
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const rootElement = document.getElementById("root")!;
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </StrictMode>
  );
}
