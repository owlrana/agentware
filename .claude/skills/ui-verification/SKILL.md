# UI Verification Skill — Playwright

> **When to invoke**: when a task changes UI behavior, page rendering, or
> web-API interactions. ALWAYS ask the user first; never run E2E checks unprompted.

## Why this skill exists

Marking a UI task "complete" because the build and unit tests pass is risky —
units don't catch routing bugs, hydration issues, race conditions on real
network calls, broken visual states, or wrong API payloads. A real browser
hitting the real running app is the only honest "complete" for a UI task. This
skill is gated on user consent at every checkpoint.

## Prerequisites

- The target web app has Playwright installed and a `playwright.config.*`. If
  onboarding's Step 6 ran, it is set up; otherwise run the "Manual setup" at the
  end of this file.
- The configuration entry recording the web-app path and runner command lives at
  `<KDIR>/configurations/playwright.md` (where `KDIR=$(scripts/agentware config
  --knowledge-dir-only)`). Read it before running any spec — paths differ per user.
- The web app is runnable locally. Prefer letting `playwright.config.*` manage
  the dev server via its `webServer` block.

## When to ask the user

Before marking a UI-affecting task complete in the worklog, ALWAYS ask:

> "This task touches the UI. Want me to run a Playwright check before marking it
> complete? (y/n; default: n)"

- If **no**: mark complete, but note in the worklog that the E2E check was
  deferred. Do not silently skip.
- If **yes**: ask which depth to run.

### Depth modes

| Mode | What it does | Default when |
|------|--------------|--------------|
| **shallow** | Render + visible-element assertions | Pure visual / styling change |
| **with-api** | Shallow + intercept the relevant API request, assert payload + status | Any change touching a fetch / form submit / mutation |
| **deep** | With-API + multi-step user flow + state mutations | Complex flows, sequential-interaction bug fixes |

If unsure, default to **with-api** when the change involves a network call, else **shallow**.

## Procedure

### Step 1 — Identify the change surface

What page/route/component changed? Which interactions trigger it? Which network
calls are involved (grep the diff for `fetch`, `axios`, `useQuery`)? What is the
smallest end-to-end path that exercises the change? Write these down first.

### Step 2 — Author or update the spec

Specs live under `<webapp>/tests/agentware/<feature>.spec.ts` (or `.js`). One
spec per task. Focused, minimal assertions.

#### Shallow template
```ts
import { test, expect } from '@playwright/test';

test('renders <feature>', async ({ page }) => {
  await page.goto('/your/route');
  await expect(page.getByRole('heading', { name: /your feature/i })).toBeVisible();
});
```

#### With-API template
```ts
import { test, expect } from '@playwright/test';

test('submits form and posts to /api/x', async ({ page }) => {
  const requestPromise = page.waitForRequest((req) =>
    req.url().endsWith('/api/x') && req.method() === 'POST');
  const responsePromise = page.waitForResponse((res) => res.url().endsWith('/api/x'));

  await page.goto('/your/route');
  await page.getByLabel('Name').fill('alice');
  await page.getByRole('button', { name: 'Submit' }).click();

  const request = await requestPromise;
  expect(request.postDataJSON()).toMatchObject({ name: 'alice' });
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({ ok: true });
});
```

#### Deep template
```ts
import { test, expect } from '@playwright/test';

test('full create-then-edit flow', async ({ page }) => {
  await page.route('**/api/items', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({ status: 201, contentType: 'application/json',
        body: JSON.stringify({ id: 'item-1' }) });
    } else { await route.continue(); }
  });
  await page.goto('/items/new');
  await page.getByLabel('Title').fill('hello');
  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page).toHaveURL(/\/items\/item-1$/);
  await expect(page.getByRole('heading', { name: 'hello' })).toBeVisible();
});
```

### Step 3 — Run the spec

From the web-app directory recorded in `<KDIR>/configurations/playwright.md`:

```bash
npx --yes playwright test tests/agentware/<feature>.spec.ts --reporter=list
```

**Default mode is HEADED** — a real browser window opens. agentware targets local
dev on macOS/Linux desktops where seeing the browser catches visual bugs headless
swallows. The shipped config reads `process.env.CI` and flips to headless on CI:

```bash
CI=true npx --yes playwright test tests/agentware/<feature>.spec.ts --reporter=list
```

Debugging: `--debug` (inspector), `--trace on` (open with `npx playwright
show-trace trace.zip`), `--ui` (UI mode).

### Step 4 — Interpret the result

#### Pass
- Mark the plan task ✅.
- Append to the worklog: spec path, run command, what was asserted (1–2 lines),
  the `OK` line(s) from the runner.

#### Fail
- DO NOT mark complete. Surface the failing assertion (expected vs received), the
  relevant network exchange (re-run with `--trace on` if needed), and the
  screenshot at `test-results/.../test-failed-1.png`.
- Ask the user: "Playwright failed at <assertion>. (a) fix code and retry,
  (b) fix spec and retry, (c) mark incomplete with this evidence and stop, or
  (d) skip the E2E check and mark complete anyway?"
- Only the user can choose (d). Default to (a) for a real product bug, (b) only
  when the spec is clearly wrong. Never default to (d).

### Step 5 — Persist what was learned

If a useful pattern emerged, capture it via
`scripts/agentware learn --topic playwright-patterns ...`. Keep patterns generic.

## Gotchas

- **Selector stability** — prefer `getByRole`/`getByLabel`/`getByText` over CSS/XPath.
- **Network mocking order** — `page.route()` matches in registration order;
  `page.unroute()` first to override mid-test.
- **Process cleanup** — set `webServer.reuseExistingServer: !process.env.CI`.
- **Auth** — use `storageState` via `globalSetup`, not per-spec login.
- **Base URL hygiene** — read baseURL from `process.env.BASE_URL`; never hardcode in specs.
- **Race on first assertion** — prefer `await expect(...).toBeVisible({ timeout: 10000 })`.

## Manual setup (if onboarding's Step 6 was skipped)

In the target web-app directory:

```bash
# New project:
npm init playwright@latest --yes
# Existing project:
npm install -D @playwright/test && npx --yes playwright install
# yarn / pnpm:
yarn add -D @playwright/test && yarn playwright install
pnpm add -D @playwright/test && pnpm exec playwright install
```

Then create/update `playwright.config.ts` (or `.js`) with at minimum:

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    // Default: HEADED — flip to headless on CI by exporting CI=true.
    headless: process.env.CI === 'true',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

Create `tests/agentware/.gitkeep` so the agent has a known location for specs.

Finally, record the setup in the external knowledge dir so future agents can find
the web-app path and runner command. Write `<KDIR>/configurations/playwright.md`:

```markdown
# Playwright UI verification

- Web-app path: `<absolute or repo-relative path to the app>`
- Runner command: `npx playwright test`
- Default spec location: `tests/agentware/`
- baseURL env var: `BASE_URL` (defaults to `http://localhost:3000`)
- Dev server command: `npm run dev` (managed by playwright.config webServer)
```

Then register it:

```bash
scripts/agentware index add \
  --id config-playwright \
  --title "Playwright UI verification" \
  --category configurations \
  --path configurations/playwright.md \
  --tags "playwright,ui-verification,e2e,frontend" \
  --summary "Web-app path + Playwright runner command for E2E checks"
```
