import { createFileRoute } from "@tanstack/react-router";
import { UserService } from "@/lib/api/services.gen";
import { useMutation } from "@tanstack/react-query";
import { CreateNewKey } from "@/lib/api/types.gen";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

const UserSettings: React.FC = () => {
  const [apiKey, setApiKey] = useState("");
  const { toast } = useToast();
  const createNewKeyMutation = useMutation({
    mutationFn: async (body: CreateNewKey) => {
      const resp = await UserService.createNewKey({
        body: { api_key: body.api_key, api_type: body.api_type },
      });
      if (!resp.data) {
        throw Error(`Failed to create new key ${resp.error}`);
      }
      return resp.data;
    },
    onSuccess: () => {
      toast({
        title: "API Key Updated",
        description: "Your API key has been successfully updated.",
      });
      setApiKey("");
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: `Failed to update API key: ${error.message}`,
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createNewKeyMutation.mutate({ api_key: apiKey, api_type: "openai" });
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle>API Key Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="grid w-full items-center gap-4">
              <div className="flex flex-col space-y-1.5">
                <Label htmlFor="apiKey">OpenAI API Key</Label>
                <Input
                  id="apiKey"
                  placeholder="Enter your OpenAI API key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>
            </div>
          </form>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={() => setApiKey("")}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!apiKey || createNewKeyMutation.isPending}
          >
            {createNewKeyMutation.isPending ? "Updating..." : "Update API Key"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export const Route = createFileRoute("/settings")({
  component: UserSettings,
});
