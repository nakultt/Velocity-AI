import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Mail,
  Calendar,
  Github,
  MessageSquare,
  FileText,
  Loader2,
  CheckCircle2,
  XCircle,
  ExternalLink,
  TicketCheck,
  X,
  Unplug,
  Key,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getIntegrationStatus,
  getGoogleConnectUrl,
  connectService,
  disconnectService,
  type IntegrationStatus,
} from "@/lib/api";

// Service metadata
const SERVICE_META: Record<
  string,
  { name: string; description: string; icon: React.ReactNode; color: string; connectType: "oauth" | "token"; tokenFields?: string[] }
> = {
  gmail: {
    name: "Gmail",
    description: "Send and read emails, manage drafts",
    icon: <Mail className="w-6 h-6" />,
    color: "text-red-500",
    connectType: "oauth",
  },
  calendar: {
    name: "Google Calendar",
    description: "Schedule events, set reminders, manage your day",
    icon: <Calendar className="w-6 h-6" />,
    color: "text-blue-500",
    connectType: "oauth",
  },
  github: {
    name: "GitHub",
    description: "Read repos, issues, PRs, and commits",
    icon: <Github className="w-6 h-6" />,
    color: "text-gray-700 dark:text-gray-300",
    connectType: "token",
    tokenFields: ["token"],
  },
  slack: {
    name: "Slack",
    description: "Read and send messages across channels",
    icon: <MessageSquare className="w-6 h-6" />,
    color: "text-purple-500",
    connectType: "token",
    tokenFields: ["token"],
  },
  notion: {
    name: "Notion",
    description: "Access databases, pages, and docs",
    icon: <FileText className="w-6 h-6" />,
    color: "text-gray-800 dark:text-gray-200",
    connectType: "token",
    tokenFields: ["token"],
  },
  jira: {
    name: "Jira",
    description: "Track issues, sprints, and project boards",
    icon: <TicketCheck className="w-6 h-6" />,
    color: "text-blue-500",
    connectType: "token",
    tokenFields: ["token", "email", "cloudUrl"],
  },
  docs: {
    name: "Google Docs",
    description: "Create and edit documents",
    icon: <FileText className="w-6 h-6" />,
    color: "text-blue-600",
    connectType: "oauth",
  },
  sheets: {
    name: "Google Sheets",
    description: "Create and manage spreadsheets",
    icon: <FileText className="w-6 h-6" />,
    color: "text-green-600",
    connectType: "oauth",
  },
  drive: {
    name: "Google Drive",
    description: "Access and manage files",
    icon: <FileText className="w-6 h-6" />,
    color: "text-yellow-500",
    connectType: "oauth",
  },
  forms: {
    name: "Google Forms",
    description: "Create forms and view responses",
    icon: <FileText className="w-6 h-6" />,
    color: "text-purple-600",
    connectType: "oauth",
  },
};

// All Google services connect together via single OAuth
const GOOGLE_SERVICES = ["gmail", "calendar", "docs", "sheets", "drive", "forms"];

interface TokenModalState {
  service: string;
  token: string;
  email: string;
  cloudUrl: string;
}

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [connectingService, setConnectingService] = useState<string | null>(null);

  // Token input modal state
  const [tokenModal, setTokenModal] = useState<TokenModalState | null>(null);

  const loadIntegrations = useCallback(async () => {
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
  }, []);

  // Check for OAuth callback params
  useEffect(() => {
    const successParam = searchParams.get("success");
    const errorParam = searchParams.get("error");

    if (successParam) {
      setSuccess("Google services connected successfully!");
      loadIntegrations();
      navigate("/integrations", { replace: true });
      setTimeout(() => setSuccess(null), 5000);
    }
    if (errorParam) {
      setError(`Connection failed: ${errorParam}`);
      navigate("/integrations", { replace: true });
    }
  }, [searchParams, navigate, loadIntegrations]);

  useEffect(() => {
    loadIntegrations();
  }, [loadIntegrations]);

  const handleConnect = (service: string) => {
    const meta = SERVICE_META[service];
    if (!meta) return;

    if (meta.connectType === "oauth" || GOOGLE_SERVICES.includes(service)) {
      // Google OAuth — connect all Google services at once
      window.location.href = getGoogleConnectUrl("google");
    } else {
      // Token-based — show input modal
      setTokenModal({ service, token: "", email: "", cloudUrl: "" });
    }
  };

  const handleTokenSubmit = async () => {
    if (!tokenModal) return;
    setConnectingService(tokenModal.service);

    try {
      await connectService(
        tokenModal.service,
        tokenModal.token,
        tokenModal.email || undefined,
        tokenModal.cloudUrl || undefined
      );
      setSuccess(`${SERVICE_META[tokenModal.service]?.name} connected!`);
      setTokenModal(null);
      await loadIntegrations();
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setConnectingService(null);
    }
  };

  const handleDisconnect = async (service: string) => {
    try {
      // If it's a Google service, disconnect all Google services
      if (GOOGLE_SERVICES.includes(service)) {
        for (const svc of GOOGLE_SERVICES) {
          await disconnectService(svc);
        }
      } else {
        await disconnectService(service);
      }
      setSuccess(`${SERVICE_META[service]?.name} disconnected.`);
      await loadIntegrations();
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Disconnect failed");
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

      {/* Status Messages */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-destructive/10 text-destructive border border-destructive/20 flex items-center gap-2">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {success && (
        <div className="mb-6 p-4 rounded-lg bg-green-500/10 text-green-500 border border-green-500/20 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{success}</span>
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
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full text-red-500 hover:text-red-600 hover:bg-red-50/10"
                        onClick={() => handleDisconnect(integration.service)}
                      >
                        <Unplug className="w-4 h-4 mr-2" />
                        Disconnect
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      className="w-full"
                      onClick={() => handleConnect(integration.service)}
                    >
                      {meta.connectType === "oauth" ? (
                        <ExternalLink className="w-4 h-4 mr-2" />
                      ) : (
                        <Key className="w-4 h-4 mr-2" />
                      )}
                      Connect
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Token Input Modal */}
      {tokenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-card border border-border rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Key className="w-5 h-5 text-primary" />
                Connect {SERVICE_META[tokenModal.service]?.name}
              </h2>
              <button
                onClick={() => setTokenModal(null)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">
                  API Token
                </label>
                <input
                  type="password"
                  value={tokenModal.token}
                  onChange={(e) => setTokenModal({ ...tokenModal, token: e.target.value })}
                  placeholder={
                    tokenModal.service === "github"
                      ? "ghp_..."
                      : tokenModal.service === "slack"
                      ? "xoxb-..."
                      : tokenModal.service === "notion"
                      ? "ntn_..."
                      : "Enter API token"
                  }
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              {tokenModal.service === "jira" && (
                <>
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-1.5">
                      Email
                    </label>
                    <input
                      type="email"
                      value={tokenModal.email}
                      onChange={(e) => setTokenModal({ ...tokenModal, email: e.target.value })}
                      placeholder="your@email.com"
                      className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-1.5">
                      Cloud URL
                    </label>
                    <input
                      type="url"
                      value={tokenModal.cloudUrl}
                      onChange={(e) => setTokenModal({ ...tokenModal, cloudUrl: e.target.value })}
                      placeholder="https://your-org.atlassian.net"
                      className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    />
                  </div>
                </>
              )}

              <p className="text-xs text-muted-foreground">
                {tokenModal.service === "github"
                  ? "Generate a personal access token at GitHub → Settings → Developer settings → Personal access tokens."
                  : tokenModal.service === "slack"
                  ? "Create a Slack app and get the Bot User OAuth Token from your app settings."
                  : tokenModal.service === "notion"
                  ? "Create an integration at notion.so/my-integrations and copy the internal integration token."
                  : tokenModal.service === "jira"
                  ? "Generate an API token at id.atlassian.com/manage-profile/security/api-tokens."
                  : "Enter your service API token."}
              </p>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setTokenModal(null)}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleTokenSubmit}
                  disabled={
                    !tokenModal.token ||
                    connectingService === tokenModal.service ||
                    (tokenModal.service === "jira" && (!tokenModal.email || !tokenModal.cloudUrl))
                  }
                >
                  {connectingService === tokenModal.service ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                  )}
                  Connect
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
