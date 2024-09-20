import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const SessionComponent: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Your GPT Sessions</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Add components for managing and displaying GPT sessions */}
        <p>Session list and chat interface will go here.</p>
      </CardContent>
    </Card>
  );
};

export default SessionComponent;