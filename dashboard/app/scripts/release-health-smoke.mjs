import assert from 'node:assert/strict';
import process from 'node:process';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

const expectedSnippets = [
  'Release health summary',
  'yellow',
  'Contract validation',
  'API/export validation',
  'Project health report',
  'None reported',
  'Review the synthetic release checklist before tagging.',
  'Synthetic/static fixtures only.',
];

const fallbackSnippets = [
  'Release health summary',
  'Health summary unavailable. Expected docs/reports/dashboard-health-summary.json.',
  'unknown',
  'unavailable',
  'Generate docs/reports/dashboard-health-summary.json before release review.',
  'No real Daimler data, customer payloads, secrets, cookies, tokens, raw production logs, or proprietary documents are included.',
];

function assertIncludes(markup, snippets, label) {
  for (const snippet of snippets) {
    assert.ok(
      markup.includes(snippet),
      `${label} markup should include ${JSON.stringify(snippet)}. Rendered markup:\n${markup}`,
    );
  }
}

let server;
try {
  server = await createServer({
    appType: 'custom',
    logLevel: 'error',
    optimizeDeps: { noDiscovery: true },
    server: { middlewareMode: true },
  });

  const React = (await import('react')).default;
  const { OverviewPage } = await server.ssrLoadModule('/src/features/overview/OverviewPage.tsx');
  const { fallbackPayload } = await server.ssrLoadModule('/src/mocks/fallbackPayload.ts');
  const { releaseHealthSummaryFallback } = await server.ssrLoadModule('/src/mocks/releaseHealthSummary.ts');

  const healthySummary = {
    overall_status: 'yellow',
    checks: {
      contract_validation_report: { status: 'present', present: true, required: true },
      api_export_validation_report: { status: 'present', present: true, required: true },
      project_health_report: { status: 'warning', present: true, required: true },
    },
    missing_artifacts: {
      required_local: [],
      optional_cross_repo: [],
    },
    next_recommended_actions: [
      'Review the synthetic release checklist before tagging.',
      'Keep the release health summary attached to the dashboard review.',
    ],
    safety_notes: [
      'Synthetic/static fixtures only.',
      'No secrets, tokens, cookies, customer data, raw production logs, or proprietary documents are included.',
    ],
    synthetic: true,
    summary_type: 'dashboard_release_health_smoke_fixture',
  };

  const healthyMarkup = renderToStaticMarkup(
    React.createElement(OverviewPage, {
      payload: fallbackPayload,
      releaseHealth: { summary: healthySummary, unavailable: false },
    }),
  );
  assertIncludes(healthyMarkup, expectedSnippets, 'healthy release health smoke');

  const fallbackMarkup = renderToStaticMarkup(
    React.createElement(OverviewPage, {
      payload: fallbackPayload,
      releaseHealth: {
        summary: releaseHealthSummaryFallback,
        unavailable: true,
        message: 'Health summary unavailable. Expected docs/reports/dashboard-health-summary.json. 503 Service Unavailable',
      },
    }),
  );
  assertIncludes(fallbackMarkup, fallbackSnippets, 'fallback release health smoke');

  console.log('Release health dashboard smoke checks passed.');
} catch (error) {
  console.error('Release health dashboard smoke checks failed.');
  console.error(error);
  process.exitCode = 1;
} finally {
  if (server) await server.close();
}
