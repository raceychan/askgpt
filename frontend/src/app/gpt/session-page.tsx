import React from "react";

import { GptService, ListSessionsResponse } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { isLoggedIn } from "@/contexts/auth-context";
import GPTSessionsCard from "./session-card";

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

  return (
    <div className="flex justify-center">
      <GPTSessionsCard
        status={status}
        sessions={sessions}
        queryClient={queryClient}
      />
    </div>
  );
};

export default SessionComponent;
