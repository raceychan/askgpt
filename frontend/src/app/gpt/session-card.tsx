import React, { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import useAuth from "@/contexts/auth-context";
import { Link } from "@tanstack/react-router";
import { Input } from "@/components/ui/input";
import { Pencil, Trash2 } from "lucide-react";
import { useMutation, QueryClient } from "@tanstack/react-query";
import { GptService } from "@/lib/api";

type Session = {
  session_id: string;
  session_name: string;
};

type GPTSessionCardProps = {
  status: "pending" | "error" | "success";
  sessions: Session[] | undefined;
  queryClient: QueryClient;
};

// GPTSessionsCardContent component
const GPTSessionsCardContent: React.FC<GPTSessionCardProps> = ({
  status,
  sessions,
  queryClient,
}) => {
  const { user } = useAuth();
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [newSessionName, setNewSessionName] = useState("");

  const addSessionMutation = useMutation({
    mutationFn: async () => {
      const resp = await GptService.createSession();
      if (!resp.data) {
        throw Error(`Failed to create session ${resp.error}`);
      }
      return resp.data;
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["userSessions"] });
    },
  });

  const renameSessionMutation = useMutation({
    mutationFn: async (params: { sessionId: string; newName: string }) => {
      const resp = await GptService.renameSession({
        path: { session_id: params.sessionId },
        body: { name: params.newName },
      });
      if (!resp.data) {
        throw Error(`Failed to rename session ${resp.error}`);
      }
      return resp.data;
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["userSessions"] });
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const resp = await GptService.deleteSession({
        path: { session_id: sessionId },
      });
      if (resp.status && resp.status >= 300) {
        throw Error(`Failed to delete session ${resp.status}`);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["userSessions"] });
    },
  });

  const formatSessionName = (session: Session) => {
    const truncatedId = session.session_id.slice(0, 8);
    return `${session.session_name} (${truncatedId})`;
  };

  let content: React.ReactNode;

  if (!user) {
    content = (
      <p>
        <Button asChild variant="link">
          <Link to="/login">Login</Link>
        </Button>{" "}
        to see your sessions
      </p>
    );
  } else if (status === "pending") {
    content = <p>Loading sessions...</p>;
  } else if (status === "error") {
    content = <p>Error loading sessions. Please try again later.</p>;
  } else if (sessions && sessions.length > 0) {
    content = (
      <ul className="space-y-2">
        {sessions.map((session) => (
          <li key={session.session_id} className="flex items-center space-x-2">
            {editingSessionId === session.session_id ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  renameSessionMutation.mutate({
                    sessionId: session.session_id,
                    newName: newSessionName,
                  });
                  setEditingSessionId(null);
                }}
                className="flex-grow flex items-center space-x-2"
              >
                <Input
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  className="flex-grow"
                />
                <Button type="submit" size="sm">
                  Save
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => setEditingSessionId(null)}
                >
                  Cancel
                </Button>
              </form>
            ) : (
              <>
                <Button
                  asChild
                  variant="outline"
                  className="flex-grow text-left justify-start bg-white text-black hover:bg-gray-200"
                >
                  <Link to={`/chat/${session.session_id}`}>
                    {formatSessionName(session)}
                  </Link>
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => {
                    setEditingSessionId(session.session_id);
                    setNewSessionName(session.session_name);
                  }}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() =>
                    deleteSessionMutation.mutate(session.session_id)
                  }
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </li>
        ))}
      </ul>
    );
  } else {
    content = <p>No sessions found</p>;
  }

  return (
    <>
      <CardContent>{content}</CardContent>
      <CardFooter className="flex justify-end">
        <Button
          onClick={() => addSessionMutation.mutate()}
          className="bg-blue-500 text-white font-bold py-2 px-4 rounded border-2 border-black hover:bg-blue-600 transition-colors duration-200"
        >
          Create New Session
        </Button>
      </CardFooter>
    </>
  );
};

// Main GPTSessionsCard component
const GPTSessionsCard: React.FC<GPTSessionCardProps> = ({
  status,
  sessions,
  queryClient,
}) => {
  return (
    <Card className="flex flex-col w-3/4 justify-center ">
      <CardHeader>
        <CardTitle>Your GPT Sessions</CardTitle>
      </CardHeader>
      <GPTSessionsCardContent
        status={status}
        sessions={sessions}
        queryClient={queryClient}
      />
    </Card>
  );
};

export default GPTSessionsCard;
