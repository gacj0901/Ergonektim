import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the six-observer assessment room", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>ERGONEKTIM · Aptadynamic Viability Assessment<\/title>/i);
  assert.match(html, /Sala de evaluación/);
  assert.match(html, /Seis observadores independientes/);
  assert.match(html, /Sin escalar global/);
  assert.match(html, /El archivo se procesa localmente y no se transmite\./);
  assert.match(html, /Estado telemétrico/);
  assert.match(html, /Estado de estabilidad/);
  assert.match(html, /Estado de desempeño/);
  assert.match(html, /Reporte de condición/);
  assert.match(html, /Enlace causal/);
  assert.match(html, /Fidelidad de estimación/);
  assert.equal((html.match(/class="observer-card /g) ?? []).length, 6);
  assert.match(
    html,
    /property="og:image" content="http:\/\/localhost(?::3000)?\/og\.png"/,
  );
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/i);
});

test("keeps presentation separate from scientific computation", async () => {
  const [page, layout, packageJson, hosting] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(new URL("../.openai/hosting.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /ergonektim\.assessment\.v1/);
  assert.match(page, /application\/json,\.json/);
  assert.match(page, /await file\.text\(\)/);
  assert.match(page, /LOCALE_STORAGE_KEY = "ergonektim-locale"/);
  assert.match(page, /window\.localStorage\.setItem\(LOCALE_STORAGE_KEY/);
  assert.match(page, /global_scalar_emitted/);
  assert.match(page, /outcomes_accessed/);
  assert.doesNotMatch(page, /\bfetch\s*\(/);
  assert.doesNotMatch(page, /XMLHttpRequest|WebSocket|EventSource/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  assert.match(packageJson, /"name": "ergonektim-dashboard"/);
  assert.match(layout, /\/og\.png/);
  assert.match(hosting, /"project_id"/);
  assert.match(hosting, /"d1": null/);
  assert.match(hosting, /"r2": null/);

  await access(new URL("../public/og.png", import.meta.url));
  await assert.rejects(
    access(new URL("../app/_sites-preview/SkeletonPreview.tsx", import.meta.url)),
  );
});
