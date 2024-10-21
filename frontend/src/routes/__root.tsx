import {
  createRootRoute,
  Link,
  ErrorComponentProps,
} from "@tanstack/react-router";
import App from "@/app/app";

import React from "react";

import { Button } from "@/components/ui/button";
const ErrorPrompt: React.FC<ErrorComponentProps> = ({ error }) => {
  return (
    <div
      id="error-page"
      className="flex flex-col items-center justify-center min-h-screen text-center"
    >
      <h1 className="text-4xl font-bold mb-4">Oops!</h1>
      <p className="mb-2">Sorry, an unexpected error has occurred.</p>
      <p className="mb-6">
        <i>{error && error.message}</i>
      </p>
      <Button asChild className="w-50 border-2 border-primary">
        <Link to="/">Go to Home</Link>
      </Button>
    </div>
  );
};

// Provide a global layout for the app
export const Route = createRootRoute({
  component: App,
  errorComponent: ErrorPrompt,
  notFoundComponent: ErrorPrompt,
});
