import { Routes, Route, Navigate } from "react-router-dom";
import { Component as LandingPage } from "@/pages/landing";
import Chatbot from "@/pages/chatbot";
import Settings from "@/pages/settings";
import IntegrationsPage from "@/pages/integrations";
import CompanyDashboard from "@/pages/company-dashboard";
import ProjectDetailPage from "@/pages/project-detail";
import AIActivityLog from "@/pages/ai-activity-log";
import { AppLayout } from "@/components/layout/app-layout";
import { ModeProvider } from "@/context/ModeContext";

// Layout wrapper
const WithLayout = ({ children }: { children: React.ReactNode }) => (
  <AppLayout>{children}</AppLayout>
);

export default function App() {
  return (
    <ModeProvider>
      <Routes>
        {/* Landing page - no sidebar */}
        <Route path="/" element={<LandingPage />} />

        {/* Auth pages — redirect to chatbot (no auth needed) */}
        <Route path="/login" element={<Navigate to="/chatbot" replace />} />
        <Route path="/signup" element={<Navigate to="/chatbot" replace />} />

        {/* App pages with sidebar layout */}
        <Route
          path="/chatbot"
          element={
            <WithLayout>
              <Chatbot />
            </WithLayout>
          }
        />
        <Route
          path="/company-dashboard"
          element={
            <WithLayout>
              <CompanyDashboard />
            </WithLayout>
          }
        />
        <Route
          path="/company-activity/:projectId"
          element={
            <WithLayout>
              <ProjectDetailPage />
            </WithLayout>
          }
        />
        <Route
          path="/ai-activity"
          element={
            <WithLayout>
              <AIActivityLog />
            </WithLayout>
          }
        />
        <Route
          path="/settings"
          element={
            <WithLayout>
              <Settings />
            </WithLayout>
          }
        />
        <Route
          path="/integrations"
          element={
            <WithLayout>
              <IntegrationsPage />
            </WithLayout>
          }
        />
      </Routes>
    </ModeProvider>
  );
}
