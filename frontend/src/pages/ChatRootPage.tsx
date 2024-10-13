import { Outlet } from "@tanstack/react-router";

// ChatRoot should act as a layout, rendering nothing or rendering shared UI elements
const ChatRoot = () => {
  return (
    <>
      <div>
        <Outlet />{" "}
      </div>
    </>
  );
};

export default ChatRoot;
