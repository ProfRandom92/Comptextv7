# Comptextv7 Enterprise Infrastructure Showcase

This is the dedicated enterprise-grade infrastructure showcase for Comptextv7. It presents deterministic token compression, replay verification, artifact lineage, CI-backed validation, operational telemetry, and reviewer walkthroughs as a restrained internal platform surface.

## Deployment posture

- React + TypeScript + Vite single-page application.
- Netlify-compatible preview and production deployment through `netlify.toml`.
- Vercel compatibility is retained for existing showcase deployments through `vercel.json`.
- Static artifact output only; no backend, API server, database, secrets, or production customer data.
- Operational semantics are represented with stable IDs: `RUN-2026-05-13-8842`, `ART-CTX7-2F91A`, `REP-CONSISTENCY-441`, and `GH-ACT-551882`.

## Local checks

```bash
npm run validate
npm run typecheck
npm run build
```

`npm run build` emits the deployable static application into `dist/`.

## Netlify setup

Use `showcase/app` as the Netlify base directory. The configured build command is:

```bash
npm run build
```

The configured publish directory is:

```bash
dist
```
