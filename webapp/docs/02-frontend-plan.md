# LangID Platform — Frontend Plan (Next.js)

> **Framework**: Next.js 15 (App Router)  
> **Language**: TypeScript (strict mode)  
> **Styling**: Tailwind CSS v4 + shadcn/ui  
> **State**: Zustand (client) + TanStack Query (server state)  
> **Auth**: JWT stored in httpOnly cookies via Next.js middleware

---

## 1. Project Structure

```
webapp/frontend/
├── public/
│   ├── fonts/
│   └── images/
│
├── src/
│   ├── app/                              # Next.js App Router
│   │   ├── layout.tsx                    # Root layout (providers, fonts, theme)
│   │   ├── page.tsx                      # Landing / marketing page
│   │   ├── globals.css                   # Tailwind imports + CSS variables
│   │   │
│   │   ├── (auth)/                       # Auth route group (no sidebar)
│   │   │   ├── layout.tsx
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── signup/
│   │   │   │   └── page.tsx
│   │   │   └── forgot-password/
│   │   │       └── page.tsx
│   │   │
│   │   ├── (dashboard)/                  # Authenticated user routes
│   │   │   ├── layout.tsx                # Dashboard shell (sidebar + header)
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx              # Overview: recent jobs, usage stats
│   │   │   ├── classify/
│   │   │   │   ├── page.tsx              # Text/document classification UI
│   │   │   │   └── [jobId]/
│   │   │   │       └── page.tsx          # Classification result viewer
│   │   │   ├── documents/
│   │   │   │   ├── page.tsx              # Document library
│   │   │   │   └── [docId]/
│   │   │   │       └── page.tsx          # Document detail + pages
│   │   │   ├── annotations/
│   │   │   │   └── page.tsx              # User's submitted annotations
│   │   │   ├── billing/
│   │   │   │   └── page.tsx              # Usage, credits, subscription
│   │   │   └── settings/
│   │   │       └── page.tsx              # Profile settings
│   │   │
│   │   ├── (admin)/                      # Admin-only routes
│   │   │   ├── layout.tsx                # Admin shell (different sidebar)
│   │   │   ├── admin/
│   │   │   │   ├── page.tsx              # Admin dashboard overview
│   │   │   │   ├── users/
│   │   │   │   │   ├── page.tsx          # User management table
│   │   │   │   │   └── [userId]/
│   │   │   │   │       └── page.tsx      # User detail + usage
│   │   │   │   ├── tiers/
│   │   │   │   │   └── page.tsx          # Tier configuration
│   │   │   │   ├── models/
│   │   │   │   │   └── page.tsx          # Model rate configuration
│   │   │   │   ├── config/
│   │   │   │   │   └── page.tsx          # System config (rates, currency)
│   │   │   │   └── annotations/
│   │   │   │       ├── page.tsx          # Annotation review queue
│   │   │   │       └── [annotationId]/
│   │   │   │           └── page.tsx      # Single annotation review
│   │   │   └── ...
│   │   │
│   │   └── api/                          # Next.js API routes (BFF proxy)
│   │       └── auth/
│   │           ├── login/route.ts        # Set httpOnly cookie
│   │           ├── logout/route.ts       # Clear cookie
│   │           └── refresh/route.ts      # Refresh token
│   │
│   ├── components/                       # Reusable UI components
│   │   ├── ui/                           # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── skeleton.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/                       # Layout components
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   ├── admin-sidebar.tsx
│   │   │   └── mobile-nav.tsx
│   │   │
│   │   ├── auth/                         # Auth-specific components
│   │   │   ├── login-form.tsx
│   │   │   ├── signup-form.tsx
│   │   │   └── auth-guard.tsx
│   │   │
│   │   ├── classify/                     # Classification-specific
│   │   │   ├── text-input-panel.tsx       # Text area with classify button
│   │   │   ├── file-upload-panel.tsx      # Drag & drop upload
│   │   │   ├── model-selector.tsx         # Choose classification model
│   │   │   ├── result-viewer.tsx          # Color-coded segment display
│   │   │   ├── segment-card.tsx           # Individual segment with annotation
│   │   │   ├── confidence-bar.tsx         # Per-language confidence display
│   │   │   └── language-legend.tsx        # Color legend for languages
│   │   │
│   │   ├── documents/                    # Document management
│   │   │   ├── document-list.tsx
│   │   │   ├── document-card.tsx
│   │   │   ├── upload-dialog.tsx
│   │   │   ├── page-viewer.tsx
│   │   │   └── storage-usage-bar.tsx
│   │   │
│   │   ├── annotations/                  # Annotation components
│   │   │   ├── annotation-form.tsx        # Correct a segment
│   │   │   ├── annotation-list.tsx
│   │   │   └── annotation-badge.tsx
│   │   │
│   │   ├── billing/                      # Billing components
│   │   │   ├── tier-card.tsx
│   │   │   ├── usage-chart.tsx
│   │   │   ├── credits-display.tsx
│   │   │   └── subscription-manager.tsx
│   │   │
│   │   ├── admin/                        # Admin-specific components
│   │   │   ├── tier-form.tsx
│   │   │   ├── model-rate-form.tsx
│   │   │   ├── config-editor.tsx
│   │   │   ├── user-table.tsx
│   │   │   ├── annotation-review-card.tsx
│   │   │   ├── annotation-review-queue.tsx
│   │   │   └── stats-card.tsx
│   │   │
│   │   └── shared/                       # Cross-cutting components
│   │       ├── data-table.tsx             # Generic data table with sorting/filtering
│   │       ├── pagination.tsx
│   │       ├── empty-state.tsx
│   │       ├── loading-skeleton.tsx
│   │       ├── confirm-dialog.tsx
│   │       ├── file-dropzone.tsx
│   │       ├── stat-card.tsx
│   │       └── page-header.tsx
│   │
│   ├── lib/                              # Utilities and configuration
│   │   ├── api/                          # API client layer
│   │   │   ├── client.ts                 # Axios/fetch wrapper with interceptors
│   │   │   ├── auth.ts                   # Auth API calls
│   │   │   ├── documents.ts             # Document API calls
│   │   │   ├── classification.ts        # Classification API calls
│   │   │   ├── annotations.ts           # Annotation API calls
│   │   │   ├── billing.ts               # Billing API calls
│   │   │   └── admin.ts                 # Admin API calls
│   │   │
│   │   ├── hooks/                        # Custom React hooks
│   │   │   ├── use-auth.ts               # Auth state + actions
│   │   │   ├── use-classification.ts     # Classification mutations/queries
│   │   │   ├── use-documents.ts
│   │   │   ├── use-billing.ts
│   │   │   └── use-debounce.ts
│   │   │
│   │   ├── stores/                       # Zustand stores
│   │   │   ├── auth-store.ts
│   │   │   └── ui-store.ts               # Sidebar state, theme, etc.
│   │   │
│   │   ├── utils.ts                      # cn(), formatters, etc.
│   │   ├── constants.ts                  # App-wide constants
│   │   └── validators.ts                 # Zod schemas for forms
│   │
│   ├── types/                            # Global TypeScript types
│   │   ├── api.ts                        # API response types
│   │   ├── user.ts
│   │   ├── document.ts
│   │   ├── classification.ts
│   │   ├── billing.ts
│   │   ├── annotation.ts
│   │   └── admin.ts
│   │
│   └── middleware.ts                     # Auth redirect, role checks
│
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── .env.local
├── .env.example
└── Dockerfile
```

---

## 2. Page-by-Page Breakdown

### 2.1 Landing Page (`/`)

**Purpose**: Marketing/intro page for unauthenticated visitors.

**Sections**:
- Hero: "Identify Sinhala, Pali & Sanskrit — Sentence by Sentence"
- Feature cards: OCR, Classification, Cloud Storage, Annotation
- Pricing tiers preview
- CTA → Sign Up

### 2.2 Authentication Pages (`/login`, `/signup`)

**Components**: `LoginForm`, `SignupForm`

**Behavior**:
- Form validation with Zod + react-hook-form
- On success → set JWT in httpOnly cookie via Next.js API route → redirect to `/dashboard`
- Display inline errors from backend (email taken, invalid credentials, etc.)

### 2.3 Dashboard (`/dashboard`)

**Purpose**: Overview hub after login.

**Widgets**:
- **Recent Classification Jobs** — Last 5 jobs with status badges
- **Storage Usage** — Visual bar showing used/free/paid storage
- **Credits Balance** — Current credits with trend sparkline
- **Quick Classify** — Mini text area with a "Classify Now" CTA
- **Subscription Status** — Current tier or PAYG indicator

### 2.4 Classification Page (`/classify`)

**This is the core feature page.**

**Layout**: Two-panel layout.

**Left Panel — Input**:
- Tab 1: **Text Input** — Large text area, paste or type Sinhala-script text
- Tab 2: **Document Upload** — Drag-and-drop zone for PDF/image files
- Model selector dropdown (lists active classification models from API)
- "Classify" button

**Right Panel — Results** (appears after classification):
- **Color-coded segment display**: Each sentence/phrase is a highlighted block:
  - 🔵 Sinhala (blue tint)
  - 🟢 Pali (green tint)
  - 🟡 Sanskrit (yellow tint)
  - ⚪ Mixed/Unknown (gray tint)
- Each segment is clickable → expands to show:
  - Confidence scores per language (horizontal bar)
  - "Mark as incorrect" button → opens annotation form
- **Summary statistics**: Pie/donut chart showing language distribution
- **Export** button: Download result as JSON or CSV

### 2.5 Classification Result Page (`/classify/[jobId]`)

**Purpose**: View a previously completed classification job.

**Features**:
- Same result viewer as `/classify` right panel
- Job metadata: timestamp, model used, token count, credits charged
- Navigation between segments
- Annotation status indicators on segments (if any corrections submitted)

### 2.6 Documents Library (`/documents`)

**Features**:
- Grid/list toggle for document cards
- Each card: filename, size, upload date, page count, OCR status
- Actions: Download, OCR, Classify, Delete
- Storage usage bar at top
- Upload button opens upload dialog

### 2.7 Document Detail (`/documents/[docId]`)

**Features**:
- Document metadata panel
- Page-by-page viewer:
  - Page image (if available)
  - Extracted text (side-by-side or below)
  - OCR status per page
- Actions: Run OCR on remaining pages, Classify extracted text
- Page navigation

### 2.8 Annotations Page (`/annotations`)

**Features**:
- Table of user's submitted annotations
- Columns: Segment text, Original prediction, Your correction, Status (pending/reviewed), Date
- Filter by status
- Click to view the full classification context

### 2.9 Billing Page (`/billing`)

**Features**:
- **Current Subscription**: Tier name, price, renewal date, included credits/OCR pages
- **Credits Balance**: Current balance with top-up option
- **Usage Breakdown**: Tabbed view by Classification / OCR / Storage
  - Usage chart (line/bar) over time
  - Detailed usage table
- **Tier Comparison**: Cards showing available tiers with "Switch" button
- **PAYG Rates**: Display current per-token and per-page rates

### 2.10 Settings (`/settings`)

**Features**:
- Profile: Display name, email
- Password change
- Account deletion

---

## 3. Admin Panel Pages

### 3.1 Admin Dashboard (`/admin`)

**Widgets**:
- Total users, active subscriptions, revenue this month
- Pending annotations count
- System health indicators
- Recent activity feed

### 3.2 User Management (`/admin/users`)

- Searchable, sortable data table
- Columns: Name, Email, Role, Tier, Credits, Storage, Status, Joined
- Click row → User detail page with full usage history
- Actions: Toggle active, change role

### 3.3 Tier Configuration (`/admin/tiers`)

- Cards or table showing all tiers
- Edit form: Name, Price (USD), Included Credits, OCR Pages Included
- Create new tier dialog
- Deactivate tier (with warning about existing subscribers)

### 3.4 Model Rate Configuration (`/admin/models`)

- Table of all registered models
- Columns: Name, Type (Classification/OCR), Rate (credits/token or credits/page), Status
- Edit rate inline or via dialog
- Register new model

### 3.5 System Configuration (`/admin/config`)

- Form for key-value system settings:
  - **USD to Credits Rate**: numeric input
  - **System Currency Name**: text input
  - **Free Storage Allowance**: numeric input (MB/GB)
  - **Storage Rate**: numeric input (credits/GB/month)
- Each field saves independently with confirmation

### 3.6 Annotation Review (`/admin/annotations`)

**This is a critical admin workflow.**

**Queue View**:
- Filterable table of annotations
- Filters: Status (pending/reviewed/all), Language, Date range
- Sort by: Date, Original prediction, User
- Bulk actions: Batch approve, batch reject

**Review Card** (per annotation):
- Original segment text displayed prominently
- Original prediction with confidence
- User's proposed correction
- User's comment
- **Side-by-side comparison** with color coding
- Surrounding context (adjacent segments) for reference
- Action buttons: ✅ Valid for Training / ❌ Invalid / 🔄 Skip
- Admin notes field

**Stats View**:
- Total annotations, reviewed vs pending
- Breakdown by correction type (Sinhala→Pali, Pali→Sanskrit, etc.)
- Top annotators by volume
- Inter-annotator agreement metrics

---

## 4. Key UI Components Design

### 4.1 Result Viewer (Core Component)

```tsx
// Conceptual structure of the color-coded result viewer

interface ClassifiedSegment {
  id: string;
  text: string;
  predictedLanguage: "sinhala" | "pali" | "sanskrit" | "mixed";
  confidence: number;
  probabilities: Record<string, number>;
  startCharOffset: number;
  endCharOffset: number;
  annotation?: Annotation;
}

// The viewer renders a flowing paragraph where each segment 
// is a colored inline block. Clicking a segment reveals details.
// 
// ┌─────────────────────────────────────────────────────┐
// │ ██ සිංහල වාක්‍යයක් ██ පාලි වාක්‍යයක් ██ සංස්කෘත   │
// │ (blue bg)          (green bg)         (yellow bg)   │
// │                                                     │
// │ [Clicked segment expands below:]                    │
// │ ┌─ Confidence ─────────────────────────────────┐    │
// │ │ Sinhala  ████████████████████░░░ 85%          │    │
// │ │ Pali     ███░░░░░░░░░░░░░░░░░░░ 10%          │    │
// │ │ Sanskrit ██░░░░░░░░░░░░░░░░░░░░  5%          │    │
// │ └──────────────────────────────────────────────┘    │
// │ [ 🏷️ Mark as Incorrect ]                            │
// └─────────────────────────────────────────────────────┘
```

### 4.2 Language Color System

```typescript
export const LANGUAGE_COLORS = {
  sinhala: {
    bg: "bg-blue-50 dark:bg-blue-950/30",
    border: "border-blue-200 dark:border-blue-800",
    text: "text-blue-700 dark:text-blue-300",
    badge: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    hex: "#3B82F6",
  },
  pali: {
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    border: "border-emerald-200 dark:border-emerald-800",
    text: "text-emerald-700 dark:text-emerald-300",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
    hex: "#10B981",
  },
  sanskrit: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-amber-200 dark:border-amber-800",
    text: "text-amber-700 dark:text-amber-300",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
    hex: "#F59E0B",
  },
  mixed: {
    bg: "bg-gray-50 dark:bg-gray-900/30",
    border: "border-gray-200 dark:border-gray-700",
    text: "text-gray-600 dark:text-gray-400",
    badge: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
    hex: "#6B7280",
  },
} as const;
```

---

## 5. State Management Strategy

| Concern            | Tool              | Why                                              |
| :----------------- | :---------------- | :----------------------------------------------- |
| **Server state**   | TanStack Query v5 | Automatic caching, refetching, optimistic updates |
| **Auth state**     | Zustand           | Lightweight, persists user info client-side       |
| **UI state**       | Zustand           | Sidebar open/closed, theme, modals                |
| **Form state**     | react-hook-form   | Performance, Zod schema validation integration    |
| **URL state**      | Next.js searchParams | Filters, pagination, sort in URL for shareability |

---

## 6. API Client Architecture

```typescript
// src/lib/api/client.ts

import axios, { AxiosInstance, AxiosError } from "axios";

const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true,  // Send httpOnly cookies
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor: handle 401 → attempt refresh → retry
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Attempt token refresh via Next.js API route
      // If refresh fails → redirect to /login
    }
    return Promise.reject(error);
  }
);

export { apiClient };
```

---

## 7. Authentication Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  Browser  │────▶│ Next.js API  │────▶│  FastAPI      │────▶│ PostgreSQL │
│           │     │ Route (BFF)  │     │  /auth/login  │     │            │
└──────────┘     └──────────────┘     └──────────────┘     └────────────┘
                        │
                        ▼
                 Set httpOnly cookie
                 (access_token)
                 Set httpOnly cookie
                 (refresh_token)
```

- **Why BFF pattern?** JWT tokens are never exposed to JavaScript. Stored in httpOnly, Secure, SameSite=Strict cookies.
- Next.js middleware reads the cookie on every request to determine auth state and redirect if needed.
- Refresh logic happens server-side in the Next.js API route.

---

## 8. Middleware & Route Protection

```typescript
// src/middleware.ts

import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";

const PUBLIC_PATHS = ["/", "/login", "/signup", "/forgot-password"];
const ADMIN_PATHS = ["/admin"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;

  // Public routes — allow
  if (PUBLIC_PATHS.some((p) => pathname === p)) {
    return NextResponse.next();
  }

  // No token — redirect to login
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const payload = verifyToken(token);

  // Admin routes — check role
  if (ADMIN_PATHS.some((p) => pathname.startsWith(p))) {
    if (payload?.role !== "admin") {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api).*)"],
};
```

---

## 9. Key Dependencies

```json
{
  "dependencies": {
    "next": "^15",
    "react": "^19",
    "react-dom": "^19",
    "typescript": "^5.6",
    "tailwindcss": "^4",
    "@tanstack/react-query": "^5",
    "zustand": "^5",
    "axios": "^1.7",
    "react-hook-form": "^7",
    "@hookform/resolvers": "^3",
    "zod": "^3",
    "lucide-react": "latest",
    "recharts": "^2",
    "react-dropzone": "^14",
    "date-fns": "^4",
    "class-variance-authority": "^0.7",
    "clsx": "^2",
    "tailwind-merge": "^2"
  },
  "devDependencies": {
    "@types/react": "^19",
    "@types/node": "^22",
    "eslint": "^9",
    "eslint-config-next": "^15",
    "prettier": "^3"
  }
}
```

---

## 10. Responsive Design Targets

| Breakpoint | Target              | Layout                              |
| :--------- | :------------------ | :---------------------------------- |
| `< 640px`  | Mobile              | Stacked layouts, bottom nav         |
| `640-1024` | Tablet              | Collapsible sidebar, 2-col grids    |
| `> 1024`   | Desktop             | Full sidebar, multi-panel layouts   |

---

## 11. Dark Mode

- Theme toggle in header
- System preference detection
- Tailwind's `dark:` variant + CSS variables
- Persisted in localStorage via Zustand
