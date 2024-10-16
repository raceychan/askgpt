import { Outlet } from "@tanstack/react-router";

const ChatRootPage = () => {
  return (
    <>
      <div>
        <Outlet />
      </div>
    </>
  );
};

export default ChatRootPage;
