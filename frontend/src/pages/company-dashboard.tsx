/**
 * Company Dashboard — Workspace Mode
 * Lists all projects as clickable cards that navigate to detail pages.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Users,
  GitBranch,
  Loader2,
  AlertCircle,
  CheckCircle2,
  PauseCircle,
  Clock,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getProjects, getPriorities, type Project, type Priority } from "@/lib/api";

export default function CompanyDashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [priorities, setPriorities] = useState<Priority[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      try {
        const [p, pr] = await Promise.all([getProjects(), getPriorities()]);
        setProjects(p);
        setPriorities(pr);
      } catch (err) {
        console.error("Failed to load dashboard:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const statusConfig: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
    active: {
      icon: <CheckCircle2 className="w-4 h-4" />,
      color: "text-emerald-400",
      bg: "bg-emerald-400/10",
    },
    paused: {
      icon: <PauseCircle className="w-4 h-4" />,
      color: "text-amber-400",
      bg: "bg-amber-400/10",
    },
    completed: {
      icon: <CheckCircle2 className="w-4 h-4" />,
      color: "text-blue-400",
      bg: "bg-blue-400/10",
    },
  };

  const urgencyConfig: Record<string, string> = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    low: "bg-green-500/20 text-green-400 border-green-500/30",
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Company Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Real-time project status powered by AI — auto-synced from GitHub, Slack, Gmail & more
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Active Projects", value: projects.filter(p => p.status === "active").length, icon: <GitBranch className="w-5 h-5" /> },
          { label: "Team Members", value: [...new Set(projects.flatMap(p => p.team_members))].length, icon: <Users className="w-5 h-5" /> },
          { label: "Open Priorities", value: priorities.length, icon: <AlertCircle className="w-5 h-5" /> },
          { label: "Avg Progress", value: `${Math.round(projects.reduce((s, p) => s + p.progress, 0) / (projects.length || 1))}%`, icon: <TrendingUp className="w-5 h-5" /> },
        ].map((stat) => (
          <Card key={stat.label} className="bg-card/50 border-border/50">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">{stat.icon}</div>
                <div>
                  <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Projects Grid */}
      <div>
        <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-primary" />
          Projects
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => {
            const status = statusConfig[project.status] || statusConfig.active;
            return (
              <Card
                key={project.id}
                className="bg-card/50 border-border/50 hover:border-primary/50 transition-all duration-200 cursor-pointer group"
                onClick={() => navigate(`/company-activity/${project.id}`)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg group-hover:text-primary transition-colors">
                      {project.name}
                    </CardTitle>
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.bg} ${status.color}`}>
                      {status.icon}
                      {project.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {project.description}
                  </p>

                  {/* Progress */}
                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="text-foreground font-medium">{project.progress}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-primary to-primary/70 rounded-full transition-all duration-500"
                        style={{ width: `${project.progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Team */}
                  <div className="flex items-center justify-between">
                    <div className="flex -space-x-2">
                      {project.team_members.slice(0, 3).map((member) => (
                        <div
                          key={member}
                          className="w-7 h-7 rounded-full bg-primary/20 border-2 border-card flex items-center justify-center"
                          title={member}
                        >
                          <span className="text-xs font-medium text-primary">
                            {member[0]}
                          </span>
                        </div>
                      ))}
                      {project.team_members.length > 3 && (
                        <div className="w-7 h-7 rounded-full bg-muted border-2 border-card flex items-center justify-center">
                          <span className="text-xs text-muted-foreground">
                            +{project.team_members.length - 3}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {project.last_updated}
                    </div>
                  </div>

                  {/* Tech Stack */}
                  <div className="flex flex-wrap gap-1.5">
                    {project.tech_stack.map((tech) => (
                      <span
                        key={tech}
                        className="px-2 py-0.5 text-xs rounded-md bg-muted text-muted-foreground"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>

                  {/* View Details */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full mt-2 group-hover:bg-primary/10 group-hover:text-primary transition-colors"
                  >
                    View Activities
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Top Priorities */}
      <div>
        <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-primary" />
          AI-Ranked Priorities
        </h2>
        <div className="space-y-3">
          {priorities.slice(0, 5).map((priority) => (
            <Card key={priority.id} className="bg-card/50 border-border/50">
              <CardContent className="py-4 flex items-center gap-4">
                <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${urgencyConfig[priority.urgency] || urgencyConfig.medium}`}>
                  {priority.urgency}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-foreground truncate">{priority.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5 truncate">
                    {priority.project} {priority.assigned_to && `· ${priority.assigned_to}`}
                  </p>
                </div>
                <p className="text-xs text-muted-foreground max-w-xs hidden lg:block">
                  {priority.ai_reasoning}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
