import React from "react";
import { Link } from "@tanstack/react-router";
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
} from "@/components/ui/navigation-menu";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import ListItem from "./listitem";

type UserMenuProps = {
  user: { email: string } | null;
  logout: () => void;
};

const UserMenu: React.FC<UserMenuProps> = ({ user, logout }) => {
  const { toast } = useToast();
  return (
    <>
      <NavigationMenuTrigger>{user && user.email}</NavigationMenuTrigger>
      <NavigationMenuContent>
        <ul className="grid gap-3 p-4 md:w-[200px] lg:w-[300px] justify-left">
          <ListItem className="text-lg" href="/settings" title="Settings" />

          <ListItem
            className="flex items-center"
            title="Log Out"
            onClick={(e) => {
              e.preventDefault();
              logout();
              toast({
                title: "Logged out",
                description: "You have been logged out",
              });
            }}
          />
        </ul>
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
