import React from "react";

import { GptService, ListSessionsResponse } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isLoggedIn } from "@/contexts/AuthContext";
import GPTSessionsCard from "./SessionCard";

const SessionComponent: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: sessions, status } = useQuery<ListSessionsResponse>({
    queryKey: ["userSessions"],
    queryFn: async () => {
      const resp = await GptService.listSessions();
      if (!resp.data) {
        throw Error(`Fail to get sessions ${resp.error}`);
      }
      return resp.data;
    },
    enabled: isLoggedIn,
  });

  const addSessionMutation = useMutation({
    mutationFn: async () => {
      const resp = await GptService.createSession();
      if (!resp.data) {
        throw Error(`Failed to create session ${resp.error}`);
      }
      return resp.data;
    },
    onSuccess: () => {
      console.log(`session data ${sessions}`);
      // Invalidate and refetch the sessions query to update the list
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["userSessions"] });
    },
  });

  return (
    <GPTSessionsCard
      status={status}
      sessions={sessions}
      addSessionMutation={addSessionMutation}
    ></GPTSessionsCard>
  );
};

export default SessionComponent;
