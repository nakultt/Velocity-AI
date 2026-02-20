/**
 * Mode Context
 * Provides student/workspace mode state throughout the app
 */

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

export type AppMode = "personal" | "workspace";

interface ModeContextType {
  mode: AppMode;
  setMode: (mode: AppMode) => void;
  isWorkspace: boolean;
}

const ModeContext = createContext<ModeContextType | undefined>(undefined);

const MODE_STORAGE_KEY = "velocity_ai_mode";

function getStoredMode(): AppMode {
  const stored = localStorage.getItem(MODE_STORAGE_KEY);
  if (stored === "workspace" || stored === "personal") return stored;
  return "personal";
}

export function ModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<AppMode>(() => getStoredMode());

  const setMode = (newMode: AppMode) => {
    setModeState(newMode);
    localStorage.setItem(MODE_STORAGE_KEY, newMode);
  };

  return (
    <ModeContext.Provider value={{ mode, setMode, isWorkspace: mode === "workspace" }}>
      {children}
    </ModeContext.Provider>
  );
}

export function useMode(): ModeContextType {
  const context = useContext(ModeContext);
  if (context === undefined) {
    throw new Error("useMode must be used within a ModeProvider");
  }
  return context;
}

export default ModeContext;
