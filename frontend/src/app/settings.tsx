import { AuthService } from "@/lib/api/services.gen";
import { CreateNewKey, PublicAPIKey } from "@/lib/api/types.gen";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { BackHomeButton } from "@/components/shared/back-home";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { toast, useToast } from "@/hooks/use-toast";
import { useRouter } from "@tanstack/react-router";
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
import { Trash2 } from "lucide-react";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Plus } from "lucide-react";

const formSchema = z.object({
  apiKey: z.string().min(1, { message: "API Key is required" }),
  keyName: z.string().min(1, { message: "Key Name is required" }),
  keyType: z.enum(["openai", "anthropic", "askgpt_test"]),
});


const APIKeyForm: React.FC<{ onSuccess?: () => void }> = ({ onSuccess }) => {
  const { history } = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const createNewKeyMutation = useMutation({
    mutationFn: async (newKey: CreateNewKey) => {
      const resp = await AuthService.createNewKey({
        body: newKey,
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
    const newKey: CreateNewKey = {
      key_name: values.keyName,
      api_key: values.apiKey,
      api_type: values.keyType,
    };
    createNewKeyMutation.mutate(newKey, {
      onSuccess: () => {
        form.reset();
        onSuccess?.(); // Close the dialog
      },
    });
  };
  return (
    <Card className="w-[450px]">
      <CardContent className="flex flex-col gap-4">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid w-full items-center gap-4">
              <FormField
                control={form.control}
                name="keyName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Key Name</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter a name for this key"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="keyType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Key Type</FormLabel>
                    <FormControl>
                      <select {...field} className="w-full p-2 border rounded">
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="askgpt_test">AskGPT Test</option>
                      </select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="apiKey"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>API Key</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your API key" {...field} />
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
                  {createNewKeyMutation.isPending ? "Adding..." : "Confirm"}
                </Button>
              </CardFooter>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};

// New component: APIKeyDisplay
const APIKeyDisplay: React.FC<{
  apiKeys: PublicAPIKey[] | undefined;
  isLoading: boolean;
  onRemoveKey: (keyName: string) => void;
  isRemoving: boolean;
  showSecrets: boolean;
  onToggleSecrets: () => void;
}> = ({
  apiKeys,
  isLoading,
  onRemoveKey,
  isRemoving,
  showSecrets,
  onToggleSecrets,
}) => {
  const queryClient = useQueryClient();

  return (
    <Card className="w-full mb-4">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Your API Keys</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-end mb-4">
          <label htmlFor="show-secrets" className="mr-2">
            Show full keys
          </label>
          <Switch
            id="show-secrets"
            checked={showSecrets}
            onCheckedChange={onToggleSecrets}
          />
        </div>
        {isLoading ? (
          <p>Loading API keys...</p>
        ) : apiKeys && apiKeys.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Key Type</TableHead>
                <TableHead>Key Name</TableHead>
                <TableHead>Key</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {apiKeys.map((key) => (
                <TableRow key={key.key_name}>
                  <TableCell>{key.key_type}</TableCell>
                  <TableCell>{key.key_name}</TableCell>
                  <TableCell>
                    {showSecrets
                      ? key.key
                      : `${key.key.slice(0, 3)}${"*".repeat(key.key.length - 3)}`}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onRemoveKey(key.key_name)}
                      disabled={isRemoving}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p>No API keys found.</p>
        )}
      </CardContent>
      <CardFooter className="flex justify-end">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline">
              <Plus className="mr-2 h-4 w-4" /> Add New Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <APIKeyForm
              onSuccess={() =>
                queryClient.invalidateQueries({ queryKey: ["apiKeys"] })
              }
            />
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  );
};

const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showSecrets, setShowSecrets] = useState(false);

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["apiKeys", showSecrets],
    queryFn: async () => {
      const resp = await AuthService.listKeys({
        query: {
          as_secret: !showSecrets,
        },
      });
      if (!resp.data) {
        throw Error(`Failed to fetch API keys: ${resp.error}`);
      }
      return resp.data;
    },
  });

  const removeKeyMutation = useMutation({
    mutationFn: async (keyNameToRemove: string) => {
      await AuthService.removeKey({ path: { key_name: keyNameToRemove } });
    },
    onSuccess: () => {
      toast({
        title: "API Key Removed",
        description: "Your API key has been successfully removed.",
      });
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: `Failed to remove API key: ${error.message}`,
        variant: "destructive",
      });
    },
  });

  const handleRemoveKey = (key: string) => {
    removeKeyMutation.mutate(key);
  };

  const handleToggleSecrets = () => {
    setShowSecrets(!showSecrets);
    queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <BackHomeButton />
      <APIKeyDisplay
        apiKeys={apiKeys}
        isLoading={isLoading}
        onRemoveKey={handleRemoveKey}
        isRemoving={removeKeyMutation.isPending}
        showSecrets={showSecrets}
        onToggleSecrets={handleToggleSecrets}
      />
    </div>
  );
};

export default SettingsPage;
