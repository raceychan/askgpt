import { createFileRoute, Outlet } from "@tanstack/react-router";

const ChatRoot = () => {
  return (
    <>
      <div>
        <Outlet />{" "}
      </div>
    </>
  );
};

export const Route = createFileRoute("/chat/")({
  component: ChatRoot,
});
