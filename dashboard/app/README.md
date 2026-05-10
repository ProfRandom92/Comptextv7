# CompText Industrial Ops Console

This frontend is intentionally structured as an internal platform/SRE/ML-Ops tool rather than a static showcase page.

## Architecture decisions

- **Feature-based architecture:** route-level domains live under `src/features/*` and compose shared infrastructure from `src/components`, `src/lib`, and `src/types`.
- **Typed API boundary:** `src/types/domain.ts` describes the backend contract emitted by `dashboard/industrial_dashboard.py` at `/api/dashboard`.
- **React Query state model:** server state is owned by TanStack Query with refresh, retry, stale-time, and abort-signal behavior configured in `src/lib/queryClient.ts`.
- **Data-heavy UX:** tables use TanStack Virtual and column-level search to keep large benchmark, forensic, and incident lists responsive.
- **Operational UX:** the shell has scalable navigation, CSV/JSON export links, explicit loading/error/empty states, and a keyboard-accessible command palette (`Ctrl/⌘+K`).
- **Reusable visualization and theme:** charts are abstract SVG components, and design tokens are centralized in `src/styles/tokens.css`.

## Local development

```bash
npm install
npm run dev
```

Run the Python API in another terminal:

```bash
python dashboard/industrial_dashboard.py --host 127.0.0.1 --port 8765
```

Build the production bundle:

```bash
npm run build
```

After a build, the stdlib Python server serves `dashboard/app/dist` automatically. Without a built bundle it falls back to the lightweight HTML export screen so air-gapped validation remains possible.
