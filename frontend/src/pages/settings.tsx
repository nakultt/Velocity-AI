import { useState, useEffect } from "react";
import { Moon, Sun, User, Palette, LogOut, Loader2, X } from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { APP_CONFIG } from '@/config/app.config';

const Settings = () => {
  const [isDark, setIsDark] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  // Edit Profile State
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editPassword, setEditPassword] = useState("");
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);
  const { updateProfile, logout } = useAuth();

  // Check initial theme
  useEffect(() => {
    const isDarkMode = document.documentElement.classList.contains("dark");
    setIsDark(isDarkMode);
  }, []);

  // Initialize edit form when opening modal
  useEffect(() => {
    if (isEditProfileOpen && user) {
      setEditName(user.name || "");
      setEditEmail(user.email || "");
      setEditPassword("");
      setProfileError(null);
      setProfileSuccess(null);
    }
  }, [isEditProfileOpen, user]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    
    setIsUpdatingProfile(true);
    setProfileError(null);
    setProfileSuccess(null);
    
    try {
      await updateProfile({
        name: editName,
        email: editEmail,
        password: editPassword || undefined // Only send if set
      });
      setProfileSuccess("Profile updated successfully!");
      setTimeout(() => setIsEditProfileOpen(false), 1500);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Toggle theme
  const toggleTheme = () => {
    const newDarkMode = !isDark;
    setIsDark(newDarkMode);
    if (newDarkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  const settingsSections = [
    {
      title: "Appearance",
      icon: Palette,
      items: [
        {
          label: "Dark Mode",
          description: "Toggle dark theme",
          action: (
            <button
              onClick={toggleTheme}
              className="relative w-14 h-8 bg-muted rounded-full p-1 transition-colors"
            >
              <motion.div
                animate={{ x: isDark ? 24 : 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
                className="w-6 h-6 bg-primary rounded-full flex items-center justify-center"
              >
                {isDark ? (
                  <Moon size={14} className="text-primary-foreground" />
                ) : (
                  <Sun size={14} className="text-primary-foreground" />
                )}
              </motion.div>
            </button>
          ),
        },
      ],
    },
    {
      title: "Account",
      icon: User,
      items: [
        {
          label: "Profile",
          description: "Manage your account details",
          action: (
            <button 
              onClick={() => setIsEditProfileOpen(true)}
              className="px-4 py-2 text-sm bg-secondary hover:bg-secondary/80 rounded-lg transition"
            >
              Edit
            </button>
          ),
        },
        {
          label: "Log Out",
          description: "Sign out of your account",
          action: (
            <button 
              onClick={handleLogout}
              className="px-4 py-2 text-sm bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg transition flex items-center gap-2"
            >
              <LogOut size={14} />
              Log Out
            </button>
          ),
        },
      ],
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="text-2xl font-bold text-foreground mb-6">Settings</h1>

        <div className="space-y-6">
          {/* Settings Sections */}
          {settingsSections.map((section) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-border rounded-xl overflow-hidden"
            >
              <div className="flex items-center gap-3 p-4 border-b border-border bg-muted/30">
                <section.icon size={20} className="text-muted-foreground" />
                <h2 className="font-semibold text-foreground">
                  {section.title}
                </h2>
              </div>
              <div className="divide-y divide-border">
                {section.items.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 hover:bg-muted/20 transition"
                  >
                    <div>
                      <p className="font-medium text-foreground">
                        {item.label}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {item.description}
                      </p>
                    </div>
                    {item.action}
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* App Info */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>{APP_CONFIG.name} {APP_CONFIG.version}</p>
          <p className="mt-1">{APP_CONFIG.copyright}</p>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {isEditProfileOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md bg-card border border-border rounded-xl shadow-lg overflow-hidden"
          >
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h2 className="text-lg font-semibold">Edit Profile</h2>
              <button 
                onClick={() => setIsEditProfileOpen(false)}
                className="p-1 hover:bg-muted rounded-full transition"
              >
                <X size={20} />
              </button>
            </div>
            
            <form onSubmit={handleUpdateProfile} className="p-4 space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Name</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="Your Name"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="name@example.com"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">New Password (Optional)</label>
                <input
                  type="password"
                  value={editPassword}
                  onChange={(e) => setEditPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="Leave blank to keep current"
                />
              </div>

              {profileError && (
                <div className="p-3 bg-red-500/10 text-red-500 rounded-lg text-sm">
                  {profileError}
                </div>
              )}
              
              {profileSuccess && (
                <div className="p-3 bg-green-500/10 text-green-500 rounded-lg text-sm">
                  {profileSuccess}
                </div>
              )}

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setIsEditProfileOpen(false)}
                  className="px-4 py-2 mr-2 text-sm text-foreground hover:bg-muted rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUpdatingProfile}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isUpdatingProfile && <Loader2 size={14} className="animate-spin" />}
                  Save Changes
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Settings;
