import React from "react";

import Profile from "./bar-items/Profile";
import Features from "./bar-items/Feature";

const NaviBar: React.FC = () => {
  return (
    <div className="container mx-auto py-4 px-6 flex justify-between items-center">
      <div className="flex items-center">
        <Features />
      </div>
      <div className="flex items-center">
        <Profile />
      </div>
    </div>
  );
};

export default NaviBar;
