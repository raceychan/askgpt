import React from "react";
import { Link } from "@tanstack/react-router";
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
} from "@/components/ui/navigation-menu";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
// import { Card } from "@/components/ui/card";

type UserMenuProps = {
  user: { email: string } | null;
  logout: () => void;
};

const UserMenu: React.FC<UserMenuProps> = ({ user, logout }) => {
  return (
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
};

const UserCenter = () => {
  const { user, logout } = useAuth();

  let panel;

  if (user) {
    panel = <UserMenu user={user} logout={logout} />;
  } else {
    panel = (
      <>
        <NavigationMenuList>
          <NavigationMenuItem>
            <Button variant="outline">
              <Link to="/login">Log In</Link>
            </Button>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <Button variant="outline" className="bg-black text-white">
              <Link to="/signup">Sign Up</Link>
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
