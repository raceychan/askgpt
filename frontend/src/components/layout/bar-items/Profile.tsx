import React from "react";
import { Link } from "@tanstack/react-router";
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";
// import { Card } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

const UserCenter = () => {
  const { user, logout } = useAuth();

  let panel;

  if (user) {
    panel = (
      <>
        <NavigationMenuTrigger>{user && user.email}</NavigationMenuTrigger>
        <NavigationMenuContent className="bg-white inline-block p-4">
          <Button
            onClick={(e) => {
              e.preventDefault();
              logout();
            }}
          >
            Log Out
          </Button>
        </NavigationMenuContent>
      </>
    );
  } else {
    panel = (
      <>
        <NavigationMenuList>
          <NavigationMenuItem>
            <Button variant="outline">
              <Link to="/login">
                <NavigationMenuLink>Log in</NavigationMenuLink>
              </Link>
            </Button>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <Button variant="outline" className="bg-black text-white">
              <Link to="/signup">
                <NavigationMenuLink>Sign Up</NavigationMenuLink>
              </Link>
            </Button>
          </NavigationMenuItem>
        </NavigationMenuList>
      </>
    );
  }

  return <NavigationMenuItem>{panel}</NavigationMenuItem>;
};

const Profile: React.FC = () => {
  return (
    <NavigationMenu>
      <NavigationMenuList>
        <UserCenter />
      </NavigationMenuList>
    </NavigationMenu>
  );
};

export default Profile;
