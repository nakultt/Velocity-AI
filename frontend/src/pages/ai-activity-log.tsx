/**
 * AI Activity Log — shows all AI actions (both modes)
 * Chronological feed: mail reads, Slack fetches, GitHub scans, etc.
 */

import { useEffect, useState } from "react";
import {
  Github,
  Mail,
  MessageSquare,
  FileText,
  Calendar,
  TicketCheck,
  Loader2,
  Activity,
  Filter,
  Bot,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getActivityLog, type ActivityLogEntry } from "@/lib/api";
import { useMode } from "@/context/ModeContext";

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  github: <Github className="w-4 h-4" />,
  gmail: <Mail className="w-4 h-4" />,
  slack: <MessageSquare className="w-4 h-4" />,
  notion: <FileText className="w-4 h-4" />,
  calendar: <Calendar className="w-4 h-4" />,
  jira: <TicketCheck className="w-4 h-4" />,
};

const SOURCE_COLORS: Record<string, string> = {
  github: "bg-gray-500/20 text-gray-300",
  gmail: "bg-red-500/20 text-red-400",
  slack: "bg-purple-500/20 text-purple-400",
  notion: "bg-neutral-500/20 text-neutral-300",
  calendar: "bg-blue-500/20 text-blue-400",
  jira: "bg-blue-500/20 text-blue-400",
};

export default function AIActivityLog() {
  const { mode } = useMode();
  const [entries, setEntries] = useState<ActivityLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await getActivityLog();
        setEntries(data);
      } catch (err) {
        console.error("Failed to load activity log:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [mode]);

  const sources = [...new Set(entries.map((e) => e.source))];
  const filtered = filter ? entries.filter((e) => e.source === filter) : entries;

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
          <Activity className="w-8 h-8 text-primary" />
          AI Activity Log
        </h1>
        <p className="text-muted-foreground mt-1">
          Everything your AI assistant accessed, read, and analyzed — full transparency
        </p>
      </div>

      {/* Source Filters */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={filter === null ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter(null)}
        >
          <Filter className="w-3.5 h-3.5 mr-1.5" />
          All ({entries.length})
        </Button>
        {sources.map((source) => (
          <Button
            key={source}
            variant={filter === source ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(filter === source ? null : source)}
          >
            {SOURCE_ICONS[source] || <Bot className="w-3.5 h-3.5" />}
            <span className="ml-1.5 capitalize">{source}</span>
            <span className="ml-1 text-xs opacity-70">
              ({entries.filter((e) => e.source === source).length})
            </span>
          </Button>
        ))}
      </div>

      {/* Activity Feed */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <Card className="bg-card/50 border-border/50">
            <CardContent className="py-12 text-center text-muted-foreground">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No activity logged yet. AI actions will appear here as they happen.</p>
            </CardContent>
          </Card>
        ) : (
          filtered.map((entry) => (
            <Card key={entry.id} className="bg-card/50 border-border/50 hover:border-border transition-colors">
              <CardContent className="py-4 flex items-start gap-4">
                {/* Source Icon */}
                <div className={`p-2.5 rounded-lg shrink-0 ${SOURCE_COLORS[entry.source] || "bg-muted text-muted-foreground"}`}>
                  {SOURCE_ICONS[entry.source] || <Bot className="w-4 h-4" />}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{entry.action}</p>
                  {entry.details && (
                    <p className="text-xs text-muted-foreground mt-1">{entry.details}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                    <span className="text-xs text-muted-foreground">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                    <span className="px-2 py-0.5 text-xs rounded-md bg-muted text-muted-foreground capitalize">
                      {entry.source}
                    </span>
                    <span className={`px-2 py-0.5 text-xs rounded-md ${entry.mode === "workspace" ? "bg-blue-500/15 text-blue-400" : "bg-emerald-500/15 text-emerald-400"}`}>
                      {entry.mode === "workspace" ? "Workspace" : "Personal"}
                    </span>
                    {entry.project && (
                      <span className="px-2 py-0.5 text-xs rounded-md bg-primary/10 text-primary">
                        {entry.project}
                      </span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
