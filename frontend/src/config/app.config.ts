/**
 * Application Configuration
 * Centralizes all branding and app-specific configuration.
 */

export const APP_CONFIG = {
  // Application Name
  name: 'Velocity AI',
  
  // Branding
  logo: '/velocity.svg',
  
  // Version & Copyright
  version: '1.0.0',
  copyright: '© 2026 Velocity AI. All rights reserved.',
  
  // Local Storage Keys
  storageKeys: {
    user: 'velocity_ai_user',
    remember: 'velocity_ai_remember'
  },
  
  // API Configuration
  api: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000'
  },
  
  // Development Settings
  dev: {
    // Set to true to bypass login screen (useful for development/demos)
    bypassLogin: true
  }
} as const;
