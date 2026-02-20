/**
 * Project Detail — drills into a specific project's activities
 * Accessed via /company-activity/:projectId
 */

import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Github,
  Mail,
  MessageSquare,
  FileText,
  Calendar,
  TicketCheck,
  CheckCircle2,
  AlertCircle,
  PauseCircle,
  Clock,
  Loader2,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getProjectDetail, type ProjectDetail as ProjectDetailData } from "@/lib/api";

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

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string }> = {
  active: { icon: <CheckCircle2 className="w-5 h-5" />, color: "text-emerald-400" },
  paused: { icon: <PauseCircle className="w-5 h-5" />, color: "text-amber-400" },
  completed: { icon: <CheckCircle2 className="w-5 h-5" />, color: "text-blue-400" },
};

const URGENCY_COLORS: Record<string, string> = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-green-500/20 text-green-400 border-green-500/30",
};

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ProjectDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!projectId) return;
      try {
        const detail = await getProjectDetail(projectId);
        setData(detail);
      } catch (err) {
        setError("Project not found");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-12 h-12 text-destructive" />
        <p className="text-lg text-muted-foreground">{error || "Something went wrong"}</p>
        <Button variant="outline" onClick={() => navigate("/company-dashboard")}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const { project, activities, priorities } = data;
  const status = STATUS_CONFIG[project.status] || STATUS_CONFIG.active;

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      {/* Back + Header */}
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/company-dashboard")}
          className="mb-4 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>

        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-foreground">{project.name}</h1>
              <span className={`flex items-center gap-1.5 ${status.color}`}>
                {status.icon}
                <span className="text-sm font-medium capitalize">{project.status}</span>
              </span>
            </div>
            <p className="text-muted-foreground mt-1">{project.description}</p>
          </div>

          {/* Progress */}
          <div className="min-w-[200px]">
            <div className="flex justify-between text-sm mb-1.5">
              <span className="text-muted-foreground">Progress</span>
              <span className="text-foreground font-bold">{project.progress}%</span>
            </div>
            <div className="h-3 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-primary/70 rounded-full transition-all"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Meta Row */}
        <div className="flex flex-wrap gap-4 mt-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            Updated {project.last_updated}
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="flex -space-x-1.5">
              {project.team_members.map((m) => (
                <div
                  key={m}
                  className="w-6 h-6 rounded-full bg-primary/20 border-2 border-background flex items-center justify-center"
                  title={m}
                >
                  <span className="text-[10px] font-medium text-primary">{m[0]}</span>
                </div>
              ))}
            </span>
            {project.team_members.join(", ")}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {project.tech_stack.map((t) => (
              <span key={t} className="px-2 py-0.5 text-xs rounded-md bg-muted text-muted-foreground">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Two Column: Activities + Priorities */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Activity Feed — 2 cols */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary" />
            Activity Feed
            <span className="text-sm font-normal text-muted-foreground">
              ({activities.length} updates)
            </span>
          </h2>

          {activities.length === 0 ? (
            <Card className="bg-card/50 border-border/50">
              <CardContent className="py-8 text-center text-muted-foreground">
                No activities found for this project yet. AI is monitoring integrations.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {activities.map((activity) => (
                <Card key={activity.id} className="bg-card/50 border-border/50">
                  <CardContent className="py-4 flex items-start gap-4">
                    <div className={`p-2 rounded-lg shrink-0 ${SOURCE_COLORS[activity.source] || "bg-muted text-muted-foreground"}`}>
                      {SOURCE_ICONS[activity.source] || <FileText className="w-4 h-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">{activity.message}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs text-muted-foreground capitalize">{activity.source}</span>
                        <span className="text-xs text-muted-foreground">{activity.timestamp}</span>
                        {activity.verified ? (
                          <span className="flex items-center gap-1 text-xs text-emerald-400">
                            <ShieldCheck className="w-3 h-3" /> Verified
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-amber-400">
                            <ShieldAlert className="w-3 h-3" /> Unverified
                          </span>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Priorities — 1 col */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-primary" />
            Priorities
          </h2>

          {priorities.length === 0 ? (
            <Card className="bg-card/50 border-border/50">
              <CardContent className="py-8 text-center text-muted-foreground text-sm">
                No priorities for this project.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {priorities.map((p) => (
                <Card key={p.id} className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="text-sm">{p.title}</CardTitle>
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold border shrink-0 ${URGENCY_COLORS[p.urgency] || URGENCY_COLORS.medium}`}>
                        {p.urgency}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-xs text-muted-foreground">{p.ai_reasoning}</p>
                    {p.assigned_to && (
                      <p className="text-xs text-primary mt-2">→ {p.assigned_to}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
