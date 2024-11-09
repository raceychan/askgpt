import { Button } from "@/components/ui/button";
import { useNavigate } from "@tanstack/react-router";

export const BackHomeButton: React.FC = () => {
  const navigate = useNavigate();
  return (
    <Button
      variant="ghost"
      onClick={() => navigate({ to: "/" })}
      className="self-start mb-4"
    >
      ← Back to Home
    </Button>
  );
};
