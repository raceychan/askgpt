import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import {
  Link,
  RouterProvider,
  createRouter,
  createRootRoute,
  createRoute,
} from "@tanstack/react-router";
import ReactDOM from "react-dom/client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "@/app/App.tsx";
import HomePage from "@/pages/HomePage.tsx";
import AuthenticationPage from "@/pages/AuthentificationPage.tsx";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";

// import ErrorPage from "@/pages/ErrorPage.tsx";
import "@/index.css";

const queryClient = new QueryClient();

const rootRoute = createRootRoute({
  component: () => (
    <>
      <div className="p-2 flex gap-2">
        <Link to="/" className="[&.active]:font-bold">
          Home
        </Link>
        <Link to="/login" className="[&.active]:font-bold">
          Login
        </Link>
      </div>
      <hr />
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
  component: AuthenticationPage,
});

// Create the router
const routeTree = rootRoute.addChildren([homeRoute, loginRoute]);
const router = createRouter({ routeTree });
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Render the application
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
