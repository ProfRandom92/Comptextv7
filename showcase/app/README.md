# Comptextv7 Vercel Showcase App

This is the dedicated SHOWCASE-02 frontend for Comptextv7. It is intentionally separate from the operational dashboard and Daimler-style experiment surfaces.

## Deployment posture

- Static-first HTML/CSS application.
- Vercel-compatible through `vercel.json`.
- No backend, API server, database, or local execution dependency.
- No Chilli/Hatch assets and no core processing logic changes.
- No fake metrics or fake validation claims; the page points reviewers to repository documents and CI artifacts.

## Local checks

```bash
npm run validate
npm run build
```

`npm run build` copies `public/` into `dist/`, which is the configured Vercel output directory.

## Vercel setup

Use `showcase/app` as the Vercel project root. The configured build command is:

```bash
npm run build
```

The configured output directory is:

```bash
dist
```
