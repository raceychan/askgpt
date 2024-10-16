import { createFileRoute } from "@tanstack/react-router";
import { AuthService } from "@/lib/api/services.gen";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
import { useNavigate } from "@tanstack/react-router";

const UserSettings: React.FC = () => {
  const [apiKey, setApiKey] = useState("");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["apiKeys"],
    queryFn: async () => {
      const resp = await AuthService.listKeys({
        query: {
          api_type: "openai",
          as_secret: true,
        },
      });
      if (!resp.data) {
        throw Error(`Failed to fetch API keys: ${resp.error}`);
      }
      return resp.data;
    },
  });

  const createNewKeyMutation = useMutation({
    mutationFn: async (body: CreateNewKey) => {
      const resp = await AuthService.createNewKey({
        body: { api_key: body.api_key, api_type: body.api_type },
      });
      return resp.data;
    },
    onSuccess: () => {
      toast({
        title: "API Key Updated",
        description: "Your API key has been successfully updated.",
      });
      setApiKey("");
      // Invalidate and refetch the apiKeys query
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: `Failed to update API key: ${error.message}`,
        variant: "destructive",
      });
    },
  });
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createNewKeyMutation.mutate({ api_key: apiKey, api_type: "openai" });
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <Button
        variant="ghost"
        onClick={() => navigate({ to: "/" })}
        className="self-start mb-4"
      >
        ← Back to Home
      </Button>
      <Card className="w-[450px] mb-4">
        <CardHeader>
          <CardTitle>Your API Keys</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p>Loading API keys...</p>
          ) : apiKeys && apiKeys.length > 0 ? (
            <ul className="list-disc pl-5">
              {apiKeys.map((key, index) => (
                <li key={index} className="mb-2">
                  API Key: {key}
                </li>
              ))}
            </ul>
          ) : (
            <p>No API keys found.</p>
          )}
        </CardContent>
      </Card>
      <Card className="w-[450px]">
        <CardHeader>
          <CardTitle>Add New API Key</CardTitle>
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
          <Button variant="outline" onClick={() => navigate({ to: "/" })}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!apiKey || createNewKeyMutation.isPending}
          >
            {createNewKeyMutation.isPending ? "Adding..." : "Add API Key"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export const Route = createFileRoute("/settings")({
  component: UserSettings,
});
