import React from "react";
import {
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";

const FeatureMenuItem: React.FC = () => {
  return (
    <NavigationMenuItem>
      <NavigationMenuTrigger>Features</NavigationMenuTrigger>
      <NavigationMenuContent className="bg-white">
        <ul className="grid gap-3 p-6 md:w-[400px] lg:w-[500px]">
          <NavigationMenuLink asChild>
            <a
              className="flex h-full w-full select-none flex-col justify-end rounded-md bg-gradient-to-b from-muted/50 to-muted p-6 no-underline outline-none focus:shadow-md"
              href="/"
            >
              <div className="mb-2 mt-4 text-lg font-medium">AI Chat</div>
              <p className="text-sm leading-tight text-muted-foreground">
                Start a conversation with our AI assistant.
              </p>
            </a>
          </NavigationMenuLink>
        </ul>
      </NavigationMenuContent>
    </NavigationMenuItem>
  );
};

export default FeatureMenuItem;