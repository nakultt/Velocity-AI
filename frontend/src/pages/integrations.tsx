import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Mail,
  Calendar,
  Github,
  MessageSquare,
  FileText,
  HardDrive,
  Loader2,
  CheckCircle2,
  XCircle,
  ExternalLink,
  TicketCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getIntegrationStatus, getGoogleConnectUrl, type IntegrationStatus } from "@/lib/api";

// Service metadata for display
const SERVICE_META: Record<string, { name: string; description: string; icon: React.ReactNode; color: string }> = {
  gmail: {
    name: "Gmail",
    description: "Send and read emails, manage drafts",
    icon: <Mail className="w-6 h-6" />,
    color: "text-red-500",
  },
  calendar: {
    name: "Google Calendar",
    description: "Schedule events, set reminders, manage your day",
    icon: <Calendar className="w-6 h-6" />,
    color: "text-blue-500",
  },
  github: {
    name: "GitHub",
    description: "Read repos, issues, PRs, and commits",
    icon: <Github className="w-6 h-6" />,
    color: "text-gray-700 dark:text-gray-300",
  },
  slack: {
    name: "Slack",
    description: "Read and send messages across channels",
    icon: <MessageSquare className="w-6 h-6" />,
    color: "text-purple-500",
  },
  notion: {
    name: "Notion",
    description: "Access databases, pages, and docs",
    icon: <FileText className="w-6 h-6" />,
    color: "text-gray-800 dark:text-gray-200",
  },
  docs: {
    name: "Google Docs",
    description: "Create and edit documents",
    icon: <FileText className="w-6 h-6" />,
    color: "text-blue-600",
  },
  sheets: {
    name: "Google Sheets",
    description: "Create and manage spreadsheets",
    icon: <FileText className="w-6 h-6" />,
    color: "text-green-600",
  },
  drive: {
    name: "Google Drive",
    description: "Access and manage files",
    icon: <HardDrive className="w-6 h-6" />,
    color: "text-yellow-500",
  },
  jira: {
    name: "Jira",
    description: "Track issues, sprints, and project boards",
    icon: <TicketCheck className="w-6 h-6" />,
    color: "text-blue-500",
  },
};

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Check for OAuth callback params
  useEffect(() => {
    const success = searchParams.get("success");
    const errorParam = searchParams.get("error");

    if (success) {
      // Refresh integrations after successful connection
      loadIntegrations();
      // Clean URL
      navigate("/integrations", { replace: true });
    }
    if (errorParam) {
      setError(`Connection failed: ${errorParam}`);
      navigate("/integrations", { replace: true });
    }
  }, [searchParams, navigate]);

  const loadIntegrations = async () => {
    setIsLoading(true);
    try {
      const data = await getIntegrationStatus();
      setIntegrations(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load integrations");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadIntegrations();
  }, []);

  const handleConnect = (service: string) => {
    // Google services use OAuth flow
    const googleServices = ["gmail", "calendar", "docs", "sheets", "drive"];
    if (googleServices.includes(service)) {
      window.location.href = getGoogleConnectUrl(service);
    } else {
      // For non-Google services, show a placeholder message
      setError(`${SERVICE_META[service]?.name || service} integration coming soon!`);
      setTimeout(() => setError(null), 3000);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 max-w-5xl mx-auto w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Integrations</h1>
        <p className="text-muted-foreground mt-2">
          Connect your tools so Velocity AI can act on your behalf — read emails, create events, check PRs, and more.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-destructive/10 text-destructive border border-destructive/20 flex items-center gap-2">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {integrations.map((integration) => {
            const meta = SERVICE_META[integration.service];
            if (!meta) return null;

            return (
              <Card
                key={integration.service}
                className={`transition-all hover:shadow-md ${
                  integration.connected
                    ? "border-green-500/30 bg-green-50/5"
                    : "border-border hover:border-primary/30"
                }`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className={`${meta.color}`}>{meta.icon}</div>
                    {integration.connected ? (
                      <div className="flex items-center gap-1 text-green-500 text-xs font-medium">
                        <CheckCircle2 className="w-4 h-4" />
                        Connected
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground">Not connected</div>
                    )}
                  </div>
                  <CardTitle className="text-lg">{meta.name}</CardTitle>
                  <CardDescription>{meta.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  {integration.connected ? (
                    <div className="space-y-2">
                      {integration.last_synced && (
                        <p className="text-xs text-muted-foreground">
                          Connected: {new Date(integration.last_synced).toLocaleDateString()}
                        </p>
                      )}
                      <Button variant="outline" size="sm" className="w-full" disabled>
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        Active
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      className="w-full"
                      onClick={() => handleConnect(integration.service)}
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Connect
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
