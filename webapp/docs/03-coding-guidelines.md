# LangID Platform — Coding Agent Guidelines

> These guidelines apply to **all coding agents** working on this codebase.  
> They cover both the **FastAPI backend** and the **Next.js frontend**.

---

## 1. Universal Principles

### 1.1 Type Safety Everywhere

- **Backend (Python)**: Use type hints on every function signature, variable declaration where non-obvious, and return types. Use `typing` generics (`list[str]`, `dict[str, Any]`, `Optional[X]`) over legacy `List`, `Dict`, etc. Pydantic models for all API boundaries.
- **Frontend (TypeScript)**: Enable `strict: true` in `tsconfig.json`. No `any` types unless explicitly justified with a comment. Define interfaces/types for all API responses, component props, and store state. Use Zod schemas for runtime validation.

```python
# ✅ Backend — Good
async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    ...

# ❌ Backend — Bad
async def get_user_by_id(db, user_id):
    ...
```

```typescript
// ✅ Frontend — Good
interface ClassifiedSegment {
  id: string;
  text: string;
  predictedLanguage: Language;
  confidence: number;
}

// ❌ Frontend — Bad
const segment: any = response.data;
```

### 1.2 Docstrings — Yes. Comment Clutter — No.

- **Every function, class, and module** gets a concise docstring explaining *what* it does, its parameters, and its return value.
- **Do NOT add inline comments** that merely restate the code. Comments should only explain *why* something non-obvious is done.

```python
# ✅ Good
async def charge_classification(
    self, user_id: UUID, model_name: str, token_count: int
) -> UsageRecord:
    """Charge a user for classification based on token count and model rate.

    Args:
        user_id: The user to charge.
        model_name: The classification model used (looked up in model_rates).
        token_count: Number of tokens processed.

    Returns:
        The created UsageRecord.

    Raises:
        InsufficientCreditsError: If user's balance is too low.
        ModelNotFoundError: If model_name doesn't exist or is inactive.
    """
    ...

# ❌ Bad — Obvious comment clutter
# Get the user from the database
user = await self.get_user(user_id)
# Check if user exists
if not user:
    # Raise an error
    raise UserNotFoundError()
```

```typescript
// ✅ Good — TSDoc
/**
 * Renders a color-coded text segment with expandable confidence details.
 * Clicking the segment toggles the detail panel.
 */
export function SegmentCard({ segment, onAnnotate }: SegmentCardProps) { ... }
```

### 1.3 Abstraction & Reusability

- **Extract shared logic** into services (backend) or hooks/utilities (frontend).
- **Don't duplicate code** across routes or components. If two handlers do similar DB queries, extract a service method.
- **Component-driven UI**: Break UI into small, focused, reusable components. A component should do one thing.
- **Generic data table**: Build ONE reusable data table component. Don't create separate table components for users, annotations, documents, etc.

### 1.4 Separation of Concerns

**Backend — 3-Layer Architecture:**
```
API Routes (thin controllers) → Services (business logic) → DB Models/Queries
```

- **Routes** (`api/v1/*.py`): Parse request, call service, return response. No business logic.
- **Services** (`services/*.py`): All business logic. Database queries, validation, billing calculations.
- **Models** (`db/models/*.py`): SQLAlchemy ORM models. No business logic.

**Frontend — Similar separation:**
```
Pages (layout + composition) → Components (UI) → Hooks (logic) → API Client (network)
```

- **Pages** (`app/**/page.tsx`): Compose components, handle route params. Minimal logic.
- **Components** (`components/*.tsx`): Receive props, render UI. Use hooks for data/state.
- **Hooks** (`lib/hooks/*.ts`): Encapsulate TanStack Query calls, Zustand state, side effects.
- **API Client** (`lib/api/*.ts`): Typed API call functions. No UI or state logic.

---

## 2. Backend-Specific Guidelines (FastAPI + Python)

### 2.1 Project Conventions

| Aspect              | Convention                                                        |
| :------------------ | :---------------------------------------------------------------- |
| **Python version**  | 3.12+                                                             |
| **Formatter**       | `ruff format` (Black-compatible)                                  |
| **Linter**          | `ruff check` with `select = ["E", "F", "I", "N", "UP", "B"]`     |
| **Type checker**    | `mypy --strict` (or `pyright`)                                    |
| **Import order**    | stdlib → third-party → local, enforced by ruff `isort`            |
| **Naming**          | `snake_case` for functions/variables, `PascalCase` for classes    |
| **Line length**     | 100 characters                                                    |
| **Test framework**  | `pytest` + `pytest-asyncio`                                       |

### 2.2 Pydantic Schemas

- All API request/response bodies MUST be Pydantic `BaseModel` subclasses.
- Use `Field(...)` with descriptions for OpenAPI docs.
- Separate `Create`, `Update`, and `Response` schemas. Don't reuse one model for all.
- Never expose internal DB fields (password_hash, internal IDs) in response schemas.

```python
# ✅ Good — Separate schemas
class TierCreate(BaseModel):
    """Schema for creating a new subscription tier."""
    name: str = Field(..., min_length=1, max_length=64, description="Display name for the tier")
    price_usd: Decimal = Field(..., ge=0, description="Monthly price in USD")
    included_credits: Decimal = Field(..., ge=0, description="Credits included per month")
    ocr_pages_included: int = Field(default=0, ge=0, description="Free OCR pages per month")

class TierUpdate(BaseModel):
    """Schema for partially updating a tier."""
    name: str | None = None
    price_usd: Decimal | None = Field(default=None, ge=0)
    included_credits: Decimal | None = Field(default=None, ge=0)
    ocr_pages_included: int | None = Field(default=None, ge=0)

class TierResponse(BaseModel):
    """Schema for tier in API responses."""
    id: UUID
    name: str
    price_usd: Decimal
    included_credits: Decimal
    ocr_pages_included: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### 2.3 Async Everything

- Use `async def` for all route handlers and service methods.
- Use `asyncpg` driver with SQLAlchemy async sessions.
- Use `await` for all DB operations. No sync blocking calls in the event loop.
- For CPU-bound ML inference, dispatch to Celery workers or use `run_in_executor`.

### 2.4 Dependency Injection

```python
# ✅ Good — Dependencies
from app.dependencies import get_db, get_current_user, require_admin

@router.post("/tiers", response_model=TierResponse)
async def create_tier(
    data: TierCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TierResponse:
    """Create a new subscription tier. Admin only."""
    return await tier_service.create_tier(db, data)
```

### 2.5 Database Migrations

- Use Alembic for all schema changes. **Never** modify the DB schema manually.
- Migration messages must be descriptive: `"add_annotations_table"`, not `"update"`.
- Auto-generate when possible: `alembic revision --autogenerate -m "description"`.
- Always review auto-generated migrations before applying.

### 2.6 Error Handling

- Use custom exception classes (see `utils/exceptions.py`).
- Services raise domain exceptions. Routes don't catch them — the global handler does.
- Never return 500 with raw stack traces. Log the full error; return a safe message.

### 2.7 Testing

- Every service method gets at least one happy-path and one error-path test.
- Use fixtures for test DB, test client, authenticated headers.
- Integration tests hit real (test) DB, not mocks.
- Name test files `test_<module>.py`, test functions `test_<behavior>`.

---

## 3. Frontend-Specific Guidelines (Next.js + TypeScript)

### 3.1 Project Conventions

| Aspect              | Convention                                                      |
| :------------------ | :-------------------------------------------------------------- |
| **Node version**    | 20+ (LTS)                                                       |
| **Package manager** | `npm`                                                          |
| **Formatter**       | Prettier (default config)                                       |
| **Linter**          | ESLint with `next/core-web-vitals` + `typescript-eslint`        |
| **Naming: files**   | `kebab-case.tsx` for components, `camelCase.ts` for utilities   |
| **Naming: components** | `PascalCase`                                                 |
| **Naming: hooks**   | `use-kebab-case.ts` files, `useCamelCase` function names       |
| **CSS**             | Tailwind utility classes. No inline `style={}` unless dynamic   |

### 3.2 Component Guidelines

- **One component per file** for non-trivial components.
- **Props via interfaces**, always typed, always named `<ComponentName>Props`.
- **Prefer Server Components** for data-fetching pages. Use `"use client"` only when needed (interactivity, hooks, browser APIs).
- **No prop drilling** beyond 2 levels. Use Zustand/Context or composition patterns.

```tsx
// ✅ Good — Typed, focused component
interface ConfidenceBarProps {
  probabilities: Record<string, number>;
  highlightLanguage: string;
}

export function ConfidenceBar({ probabilities, highlightLanguage }: ConfidenceBarProps) {
  // ...
}
```

### 3.3 Data Fetching

- Use **TanStack Query** for all server state.
- Define query keys as constants in a central `queryKeys.ts` or colocated with API functions.
- Mutations should invalidate relevant queries on success.
- Use `Suspense` boundaries with loading skeletons, not conditional rendering.

```typescript
// ✅ Good — API function + hook pattern
// lib/api/classification.ts
export async function getClassificationJob(jobId: string): Promise<ClassificationJob> {
  const { data } = await apiClient.get<ClassificationJob>(`/classify/jobs/${jobId}`);
  return data;
}

// lib/hooks/use-classification.ts
export function useClassificationJob(jobId: string) {
  return useQuery({
    queryKey: ["classification", "job", jobId],
    queryFn: () => getClassificationJob(jobId),
  });
}
```

### 3.4 Form Handling

- Use `react-hook-form` + `@hookform/resolvers/zod` for all forms.
- Define Zod schemas in `lib/validators.ts`.
- Display field-level errors inline.
- Disable submit button during submission.

### 3.5 Error Boundaries

- Wrap each route segment in an `error.tsx` boundary.
- Show user-friendly error messages with a retry button.
- Log errors to console in development.

### 3.6 Loading States

- Every page with data fetching needs a `loading.tsx` or Suspense boundary.
- Use skeleton components that mirror the actual layout (not generic spinners).

### 3.7 Accessibility

- All interactive elements must be keyboard accessible.
- Use semantic HTML (`<button>`, `<nav>`, `<main>`, `<aside>`).
- Images need `alt` text. Decorative images use `alt=""`.
- Color is not the only indicator — supplement with text/icons.

---

## 4. Shared Standards

### 4.1 Git Conventions

- **Branch naming**: `feat/<feature>`, `fix/<bug>`, `chore/<task>`
- **Commit messages**: Conventional Commits format: `feat(auth): add JWT refresh logic`
- **PR size**: Keep PRs focused. One feature or fix per PR. Max ~400 lines changed.

### 4.2 Environment Variables

- All secrets and config via `.env` files.
- Never commit `.env`. Commit `.env.example` with placeholder values.
- Use `pydantic-settings` (backend) and `NEXT_PUBLIC_*` (frontend) for typed env access.

### 4.3 API Contract

- Backend and frontend MUST agree on API response shapes.
- Define Pydantic schemas (backend) and TypeScript interfaces (frontend) that mirror each other.
- Use consistent naming: `snake_case` in API JSON, convert to `camelCase` in frontend via Axios transformer if needed.

### 4.4 Pagination

- All list endpoints return paginated responses.
- Standard response shape:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### 4.5 Logging

- **Backend**: Use `structlog` or Python's `logging` with JSON formatter. Log request ID, user ID, action.
- **Frontend**: Console logging in development only. No `console.log` in production code.

### 4.6 Security Checklist

- [ ] Never log passwords, tokens, or PII
- [ ] Validate all inputs server-side (Pydantic) regardless of client-side validation
- [ ] Rate limit auth endpoints
- [ ] Use parameterized queries (SQLAlchemy handles this)
- [ ] Sanitize file uploads (check mime type, size, extension)
- [ ] CORS configured for specific origins only
- [ ] JWT tokens in httpOnly cookies, never localStorage
- [ ] Admin routes protected by role check at middleware AND route level

---

## 5. Code Review Checklist

Before submitting any code, verify:

- [ ] All functions have type annotations (Python) / TypeScript types (TS)
- [ ] All functions have docstrings / TSDoc comments
- [ ] No `any` types (TS) or missing type hints (Python)
- [ ] No commented-out code
- [ ] No unnecessary inline comments
- [ ] Business logic is in services, not routes/components
- [ ] Reusable logic is extracted, not duplicated
- [ ] Error cases are handled
- [ ] New endpoints have corresponding schemas
- [ ] Database changes have Alembic migrations
- [ ] Tests cover happy path + at least one error case
