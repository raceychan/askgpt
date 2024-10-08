import React from "react";
import { Link } from "@tanstack/react-router";

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";

import ProfileMenuItem from "./bar-items/ProfileMenuItem";
import FeatureMenuItem from "./bar-items/FeatureMenuItem";

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

          <FeatureMenuItem></FeatureMenuItem>
          <ProfileMenuItem></ProfileMenuItem>
        </NavigationMenuList>
      </NavigationMenu>
    </div>
  );
};

export default NaviBar;
