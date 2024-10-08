import React from "react";
import {
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";
import { useAuth } from "@/contexts/AuthContext";
import ListItem from "./ListItem";

const ProfileMenuItem: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <NavigationMenuItem>
      <NavigationMenuTrigger>Profile</NavigationMenuTrigger>
      <NavigationMenuContent className="bg-white">
        {user && (
          <NavigationMenuLink asChild>
            <a
              className="flex h-full w-full select-none flex-col justify-end rounded-md bg-gradient-to-b from-muted/50 to-muted p-6 no-underline outline-none focus:shadow-md"
              href="/"
            >
              <div className="mb-2 mt-4 text-lg font-medium">
                {user && user.email}
              </div>
            </a>
          </NavigationMenuLink>
        )}

        <ul className="grid gap-4 p-6 md:w-[400px] lg:w-[500px] lg:grid-cols-[.75fr_1fr]">
          {user ? (
            <>
              <ListItem
                title="Logout"
                onClick={(e) => {
                  e.preventDefault();
                  logout();
                }}
              >
                Click here to log out of your account
              </ListItem>
            </>
          ) : (
            <>
              <ListItem href="/login" title="Login">
                Sign in to your account
              </ListItem>
              <ListItem href="/signup" title="Sign Up">
                Create a new account
              </ListItem>
            </>
          )}
        </ul>
      </NavigationMenuContent>
    </NavigationMenuItem>
  );
};

export default ProfileMenuItem;
