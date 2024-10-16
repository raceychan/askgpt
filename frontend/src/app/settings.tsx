import { AuthService } from "@/lib/api/services.gen";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { useNavigate, useRouter } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const formSchema = z.object({
  apiKey: z.string().min(1, { message: "API Key is required" }),
});

const APIKeyForm: React.FC = () => {
  const { history } = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const createNewKeyMutation = useMutation({
    mutationFn: async (newApiKey: string) => {
      const resp = await AuthService.createNewKey({
        body: { api_key: newApiKey, api_type: "openai" },
      });
      return resp.data;
    },
    onSuccess: (newKey) => {
      toast({
        title: "API Key Added",
        description: "Your new API key has been successfully added.",
      });
      queryClient.setQueryData(["apiKeys"], (oldData: string[] | undefined) => {
        return oldData ? [...oldData, newKey] : [newKey];
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: `Failed to add API key: ${error.message}`,
        variant: "destructive",
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
  });
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      apiKey: "",
    },
  });

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    createNewKeyMutation.mutate(values.apiKey);
    form.reset(); // Reset the form after submission
  };
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <div className="grid w-full items-center gap-4">
          <FormField
            control={form.control}
            name="apiKey"
            render={({ field }) => (
              <FormItem>
                <FormLabel>OpenAI API Key</FormLabel>
                <FormControl>
                  <Input placeholder="Enter your OpenAI API key" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <CardFooter className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => history.go(-1)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createNewKeyMutation.isPending}>
              {createNewKeyMutation.isPending ? "Adding..." : "Add API Key"}
            </Button>
          </CardFooter>
        </div>
      </form>
    </Form>
  );
};

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();

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
        <CardContent className="flex flex-col gap-4">
          <APIKeyForm />
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
