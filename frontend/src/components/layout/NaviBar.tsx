import React from "react";
import { Link } from "@tanstack/react-router";

import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import ProfileMenuItem from "./ProfileMenuItem";

const NaviBar: React.FC = () => {
  return (
    <div className="container mx-auto py-4 px-6 flex justify-between items-center">
      <NavigationMenu>
        <NavigationMenuList>
          <NavigationMenuItem>
            <Link to="/" className={navigationMenuTriggerStyle()}>
              <span className="text-2xl font-bold">AskGPT</span>
            </Link>
          </NavigationMenuItem>

          <NavigationMenuItem>
            <NavigationMenuTrigger>Features</NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul className="grid gap-3 p-6 md:w-[400px] lg:w-[500px]">
                <li className="row-span-3">
                  <NavigationMenuLink asChild>
                    <a
                      className="flex h-full w-full select-none flex-col justify-end rounded-md bg-gradient-to-b from-muted/50 to-muted p-6 no-underline outline-none focus:shadow-md"
                      href="/"
                    >
                      <div className="mb-2 mt-4 text-lg font-medium">
                        AI Chat
                      </div>
                      <p className="text-sm leading-tight text-muted-foreground">
                        Start a conversation with our AI assistant.
                      </p>
                    </a>
                  </NavigationMenuLink>
                </li>
                {/* Add more menu items as needed */}
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
          <ProfileMenuItem></ProfileMenuItem>
        </NavigationMenuList>
      </NavigationMenu>
    </div>
  );
};

export default NaviBar;
