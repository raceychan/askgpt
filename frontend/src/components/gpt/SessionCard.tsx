import React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Session = {
  session_id: string;
  session_name?: string;
};

type GPTSessionCardProps = {
  status: "pending" | "error" | "success";
  sessions: Session[] | undefined;
  addSessionMutation: {
    mutate: () => void;
  };
};
// GPTSessionsCardContent component
const GPTSessionsCardContent: React.FC<
  Pick<GPTSessionCardProps, "status" | "sessions">
> = ({ status, sessions }) => {
  if (status === "pending") {
    return (
      <CardContent>
        <p>Loading sessions...</p>
      </CardContent>
    );
  }

  if (status === "error") {
    return (
      <CardContent>
        <p>Error loading sessions. Please try again later.</p>
      </CardContent>
    );
  }

  if (sessions && sessions.length > 0) {
    return (
      <CardContent>
        <ul>
          {sessions.map((session) => (
            <li key={session.session_id}>
              {session.session_name + `(${session.session_id})`}
            </li>
          ))}
        </ul>
      </CardContent>
    );
  }

  return (
    <CardContent>
      <p>No sessions found.</p>
    </CardContent>
  );
};

// Main GPTSessionsCard component
const GPTSessionsCard: React.FC<GPTSessionCardProps> = ({
  status,
  sessions,
  addSessionMutation,
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Your GPT Sessions</CardTitle>
      </CardHeader>
      <GPTSessionsCardContent status={status} sessions={sessions} />
      <CardFooter className="bg-gray-100 p-4 flex">
        <Button
          onClick={() => {
            addSessionMutation.mutate();
          }}
          className="bg-blue-500 text-white font-bold py-2 px-4 rounded border-2 border-black hover:bg-blue-600 transition-colors duration-200"
        >
          Create New Session
        </Button>
      </CardFooter>
    </Card>
  );
};

export default GPTSessionsCard;
