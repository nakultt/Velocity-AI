# Quick Setup Guide for Template

## Step 1: Update App Configuration

Edit `/src/config/app.config.ts` and replace all placeholders:

```typescript
export const APP_CONFIG = {
  name: 'YourAppName',              // ← Replace this
  logo: '/your_logo.png',            // ← Replace this
  version: '1.0.0',
  copyright: '© 2026 YourAppName. All rights reserved.',  // ← Replace this
  storageKeys: {
    user: 'yourapp_user',            // ← Replace this
    remember: 'yourapp_remember'     // ← Replace this
  },
  api: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000'
  }
};
```

## Step 2: Update Logo

1. Replace `/public/logo.png` with your logo file
2. Update the logo filename in `app.config.ts`

## Step 3: Update HTML Title

Edit `/index.html`:
```html
<title>YourAppName</title>
```

## Step 4: Update Package.json (Optional)

Edit `package.json`:
```json
{
  "name": "your-app-name",
  "description": "Your app description",
  "version": "1.0.0"
}
```

## That's It!

All branding is now centralized in the config file. The entire app will automatically use your app name and logo.

---

## Development Settings

### Bypass Login (For Development/Demos)

To skip the login screen during development or demos, set this in `/src/config/app.config.ts`:

```typescript
dev: {
  bypassLogin: true  // Set to true to bypass authentication
}
```

When enabled:
- Landing page (`/`) automatically redirects to `/chatbot`
- All protected routes are accessible without login
- **Remember to set to `false` for production!**

---

## What Was Changed

All hardcoded app name references have been replaced with `APP_CONFIG.name`
All hardcoded logo paths have been replaced with `APP_CONFIG.logo`
Storage keys use `APP_CONFIG.storageKeys.*`
API base URL uses `APP_CONFIG.api.baseUrl`

See `PROJECT_CONFIG.md` for detailed documentation of all locations.
