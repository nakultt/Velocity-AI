# Project Configuration Template

This file lists all locations where you need to update the project name and branding when using this as a template.

## Quick Setup
1. Replace `{{APP_NAME}}` with your project name in all files listed below
2. Replace `{{APP_LOGO}}` with your logo filename in `/public/` directory
3. Update version number and copyright as needed

---

## Project Name Locations

### API & Backend (`src/lib/api.ts`)
- Line 2: API Client comment
- Line 65, 76, 300, 310: localStorage/sessionStorage keys (`{{APP_NAME}}_user`)

### Authentication Context (`src/context/AuthContext.tsx`)
- Line 34: Storage key constant (`{{APP_NAME}}_user`)
- Line 35: Remember key constant (`{{APP_NAME}}_remember`)

### Components

#### Chat Box (`src/components/chat/chat-box.tsx`)
- Line 541: Welcome message

#### Sidebar (`src/components/layout/sidebar.tsx`)
- Line 5: Logo path variable
- Line 155, 223: Logo image alt text
- Line 157, 225: App name text

#### App Layout (`src/components/layout/app-layout.tsx`)
- Line 18: Logo path variable
- Line 96, 201, 234: Logo image alt text  
- Line 97, 202, 235: App name text

### Pages

#### Landing Page (`src/pages/landing.tsx`)
- Logo references and branding text (check entire file)

#### Login Page (`src/pages/login.tsx`)
- Line 361, 700: Logo image alt text
- Line 364, 703: App name text

#### Signup Page (`src/pages/signup.tsx`)
- Line 52, 91: Logo image alt text
- Line 55, 93: App name text
- Line 60: Heading text

#### Settings Page (`src/pages/settings.tsx`)
- Line 186: Version text
- Line 187: Copyright text

---

## Logo/Image Locations

### Current Logo Path
`/public/logo.png` → Replace with your logo file (update path in `APP_CONFIG.logo`)

### Files Referencing Logo
1. `src/components/layout/sidebar.tsx` (line 5)
2. `src/components/layout/app-layout.tsx` (line 18)
3. `src/pages/signup.tsx` (src attribute in img tags)
4. `src/pages/login.tsx` (src attribute in img tags)
5. `src/pages/landing.tsx` (src attribute in img tags)

---

## Additional Configuration

### HTML Title (`index.html`)
- Update `<title>` tag

### Package.json
- Update `name` field
- Update `description` field
- Update `version` field

### Environment Variables (`.env`)
- `VITE_API_URL`: Update backend URL if different
- Add any project-specific environment variables

---

## Recommended Approach

Create a config file at `src/config/app.config.ts`:

```typescript
export const APP_CONFIG = {
  name: '{{APP_NAME}}',
  logo: '/{{APP_LOGO}}.png',
  version: '1.0.0',
  copyright: '© 2026 {{APP_NAME}}. All rights reserved.',
  storageKeys: {
    user: '{{APP_NAME}}_user',
    remember: '{{APP_NAME}}_remember'
  }
};
```

Then import and use this config throughout the application.
