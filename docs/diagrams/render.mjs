/** Documentation only. See SOURCES.md for dependencies, commands and logo attribution. */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const toolRoot = process.env.GAIA_DOC_TOOLS;
if (!toolRoot) throw new Error('Set GAIA_DOC_TOOLS to the temporary documentation npm prefix.');
const requireTool = createRequire(join(resolve(toolRoot), 'package.json'));
const sharp = requireTool('sharp');
const { JSDOM } = requireTool('jsdom');
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { default: mermaid } = await import(pathToFileURL(requireTool.resolve('mermaid')));
mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
const readme = await readFile(join(root, 'README.md'), 'utf8');
const names = ['architecture', 'batch-ingestion', 'adaptive-investigation', 'human-review'];
const diagrams = [...readme.matchAll(/^```mermaid\r?\n([\s\S]*?)^```/gm)].map(m => m[1]);
if (diagrams.length !== names.length) throw new Error('Expected four README Mermaid diagrams.');
for (let i = 0; i < diagrams.length; i++) {
  await mermaid.parse(diagrams[i]);
  console.log(`Mermaid parser PASS: ${names[i]}`);
}
// Check Markdown links without treating code examples as links.
const prose = readme.replace(/^```[\s\S]*?^```/gm, '');
for (const m of prose.matchAll(/\]\(([^)]+)\)/g)) {
  const href = m[1].replace(/^<|>$/g, '').split('#')[0];
  if (!href || /^(https?:|mailto:)/.test(href)) continue;
  await readFile(join(root, decodeURIComponent(href))).catch(async error => {
    if (error.code !== 'EISDIR') throw error;
  });
}
console.log('README local links PASS');
if (process.argv.includes('--check')) process.exit(0);
await mkdir(here, { recursive: true });

// All brand assets are embedded, preserving proportions and original colors.
const logos = {};
for (const [name, file] of Object.entries({ fink: 'fink.svg', iris: 'intersystems.svg',
  esa: 'esa.svg', cds: 'cds.png', ipac: 'ipac.png', openai: 'openai.svg' })) {
  const bytes = await readFile(join(here, 'logos', file));
  logos[name] = `data:image/${file.endsWith('svg') ? 'svg+xml' : 'png'};base64,${bytes.toString('base64')}`;
}
const esc = s => String(s).replace(/[&<>\"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const text = (x, y, value, cls = 'body') => `<text x="${x}" y="${y}" class="${cls}">${esc(value)}</text>`;
const line = (x1, y1, x2, y2) => `<path d="M${x1} ${y1}L${x2} ${y2}"/>`;
const icons = {
  browser: '<rect x="3" y="5" width="42" height="34" rx="5"/><path d="M3 15h42M10 10h1m5 0h1m5 0h1M14 25l-5 5 5 5m20-10 5 5-5 5m-8-12-4 14"/>',
  telescope: '<path d="M8 15l23-8 6 16-23 8zM14 31l-5 3M30 8l4-2 7 18-4 2M24 29v7m0 0L13 46m11-10 11 10"/><circle cx="9" cy="8" r="1"/><path d="M43 4v6m-3-3h6"/>',
  satellite: '<path d="M18 17l13 13-11 11L7 28zM21 14l7-7 13 13-7 7M5 18l8-8 7 7-8 8M30 30l7-7 8 8-8 8M19 28l9-9M17 37l-5 5M30 7l3-4m8 17 4-3"/>',
  database: '<ellipse cx="24" cy="10" rx="19" ry="7"/><path d="M5 10v27c0 10 38 10 38 0V10M5 23c0 10 38 10 38 0M5 35c0 10 38 10 38 0"/>',
  agent: '<rect x="7" y="14" width="34" height="27" rx="7"/><path d="M24 14V7m-12 33v5m24-5v5M7 24H2m39 0h5M16 33h16"/><circle cx="24" cy="4" r="3"/><circle cx="17" cy="24" r="2"/><circle cx="31" cy="24" r="2"/>',
  workflow: '<rect x="17" y="3" width="14" height="11" rx="3"/><rect x="2" y="34" width="14" height="11" rx="3"/><rect x="32" y="34" width="14" height="11" rx="3"/><path d="M24 14v11H9v9m15-9h15v9"/>',
  human: '<circle cx="18" cy="12" r="8"/><path d="M2 42v-7c0-13 32-13 32 0v7M32 18h14v24H32M35 24h8m-8 6h8m-8 6h5"/>',
  stars: '<path d="M18 3l4 11 12 3-12 4-4 12-4-12-11-4 11-3zM37 28l2 6 7 2-7 3-2 7-2-7-7-3 7-2z"/>',
  python: '<path d="M18 6h17v17H13v17h17M18 6v11H6v20h12m12 3V29h12V9H30M18 11h1m10 24h1"/>',
  server: '<rect x="5" y="4" width="38" height="17" rx="4"/><rect x="5" y="27" width="38" height="17" rx="4"/><path d="M12 12h1m6 0h1m-8 23h1m6 0h1m9-23h7m-7 23h7"/>',
};
const icon = (name, x, y, color = '#127c89', size = 48) => `<g transform="translate(${x} ${y}) scale(${size / 48})" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">${icons[name]}</g>`;
const logo = (name, x, y, w, h) => `<image href="${logos[name]}" x="${x}" y="${y}" width="${w}" height="${h}" preserveAspectRatio="xMidYMid meet"/>`;
const card = (x, y, w, h, title, lines, pictogram, accent = '#127c89') => `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="18" fill="white" stroke="#d6e1eb" stroke-width="2"/><rect x="${x}" y="${y + 22}" width="5" height="${h - 44}" rx="2" fill="${accent}"/>${icon(pictogram, x + 20, y + 20, accent, 38)}${text(x + 72, y + 46, title, 'card-title')}${lines.map((s, i) => text(x + 22, y + 83 + i * 25, s)).join('')}</g>`;
const arrow = (d, label, x, y, color = '#317989', dashed = false) => `<path d="${d}" fill="none" stroke="${color}" stroke-width="3" stroke-linejoin="round" ${dashed ? 'stroke-dasharray="8 6"' : ''} marker-end="url(#${dashed ? 'optional' : 'arrow'})"/>${label ? text(x, y, label, 'edge') : ''}`;
let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1900" height="1360" viewBox="0 0 1900 1360" role="img" aria-labelledby="title desc"><title id="title">Gaia Discovery AI system architecture</title><desc id="desc">Rubin alerts through Fink enter IRIS. Native BPL validates AI decisions, routes catalog queries through Java PEX, saves reports and conditionally requests native human review. OpenAI provides chat and eligible report embeddings.</desc><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#317989"/></marker><marker id="optional" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#8b60ae"/></marker></defs><style>text{font-family:Arial,Helvetica,sans-serif;fill:#17304c}.title{font-size:43px;font-weight:700}.sub{font-size:22px;fill:#526881}.group{font-size:17px;letter-spacing:2px;font-weight:700;fill:#526881}.card-title{font-size:18px;font-weight:700}.body{font-size:19px;fill:#40556d}.edge{font-size:16px;font-weight:700;fill:#317989;paint-order:stroke;stroke:#f4f7fb;stroke-width:7px;stroke-linejoin:round}.small{font-size:17px;fill:#526881}.white{font-size:22px;font-weight:700;fill:white}</style><rect width="1900" height="1360" fill="#f4f7fb"/>`;
svg += text(50, 67, 'GAIA DISCOVERY AI', 'title') + text(50, 108, 'From astronomical alerts to evidence-backed preliminary investigations', 'sub');
svg += text(50, 182, 'OBSERVATIONS & PEOPLE', 'group') + text(1495, 182, 'EXTERNAL PROVIDERS', 'group');
svg += '<rect x="420" y="210" width="1020" height="990" rx="24" fill="#eaf2f7" stroke="#a9c6da" stroke-width="2"/>';
svg += logo('iris', 455, 236, 218, 53) + text(770, 264, 'IRIS AI Hub EAP 154 · USER namespace', 'card-title') + text(455, 316, 'One native runtime: interoperability, Python, persistence and human workflow', 'small');
// Connectors are drawn before cards, so they never obscure card content.
svg += arrow('M350 420H470', 'HTTP /gaia', 354, 402);
svg += arrow('M730 420H790', '', 0, 0);
svg += arrow('M920 510V620', 'async START_RUN', 800, 563);
svg += arrow('M790 705H730', '', 0, 0);
svg += arrow('M470 705H350', 'REST', 370, 686);
svg += arrow('M1050 650H1080V550H1235V510', 'AGENT_DECIDE', 1100, 573);
svg += arrow('M1050 745H1110', '', 0, 0);
svg += arrow('M1365 420H1490', 'chat', 1395, 401);
svg += arrow('M1365 740H1490', 'TAP / ADQL', 1370, 719);
svg += arrow('M920 810V940', 'save report + session', 804, 881);
svg += arrow('M790 780H760V1010H730', 'candidate only', 588, 865, '#8b60ae', true);
svg += arrow('M350 1010H470', '', 0, 0, '#8b60ae', true);
svg += arrow('M730 1050H790', '', 0, 0, '#8b60ae', true);
svg += arrow('M1110 1030H1050', '', 0, 0);
svg += arrow('M600 510V550H745V1130H920V1100', 'saved reads', 751, 1118);
svg += arrow('M1365 1020H1460V475H1490', 'eligible embeddings', 1492, 1140, '#8b60ae', true);
svg += card(50, 340, 300, 175, 'Researcher browser', ['Feed, filters and reports', 'Authenticated REST + UI'], 'browser');
svg += card(50, 570, 300, 240, 'Rubin / Fink', ['Alert measurements', 'Latest detection + 3 PNGs'], 'telescope');
svg += logo('fink', 90, 710, 215, 78);
svg += card(50, 940, 300, 160, 'Human reviewer', ['Inspect candidate evidence', 'ACCEPT / REJECT in Inbox'], 'human', '#8b60ae');
svg += card(470, 350, 260, 160, 'Flask / WSGI', ['Hosted inside IRIS', 'API mount: /gaia'], 'browser');
svg += card(790, 350, 260, 160, 'DiscoveryService', ['Validate + create run', 'Dispatch asynchronously'], 'server');
svg += card(1110, 350, 255, 160, 'Native AI Hub agent', ['AIHubOperation invokes', 'Gaia.AI.DiscoveryAgent'], 'agent');
svg += card(470, 620, 260, 190, 'FinkOperation', ['LIST_BY_TAG', 'GET_SOURCES + cutouts', 'Preserve provenance'], 'telescope');
svg += card(790, 620, 260, 190, 'DiscoveryWorkflow', ['BPL owns every decision', 'Validate JSON + route', 'At most 3 catalog checks'], 'workflow');
svg += card(1110, 620, 255, 190, 'Catalog Operations', ['Gaia / Simbad / Irsa', 'Shared Java PEX adapter', 'CSV + transport metadata'], 'satellite');
svg += card(470, 940, 260, 160, 'Native Workflow', ['AstronomyReviewer', 'Task replies update report'], 'human', '#8b60ae');
svg += card(790, 940, 260, 160, 'IRIS persistence', ['Reports + PNG streams', 'Evidence + session IDs'], 'database');
svg += card(1110, 940, 255, 160, 'Embedded Python', ['Science normalization', '1536-dim vector history'], 'python');
svg += '<rect x="1490" y="300" width="360" height="215" rx="18" fill="white" stroke="#d6e1eb" stroke-width="2"/>';
svg += logo('openai', 1512, 322, 48, 48) + text(1580, 355, 'OpenAI', 'card-title') + text(1512, 408, 'Chat: structured next action') + text(1512, 440, 'Embeddings: eligible history') + text(1512, 480, 'No agent tools or image analysis', 'small');
svg += '<rect x="1490" y="570" width="360" height="520" rx="18" fill="white" stroke="#d6e1eb" stroke-width="2"/>';
svg += '<rect x="1510" y="590" width="80" height="58" rx="8" fill="#0a334b"/>' + logo('esa', 1518, 601, 64, 36) + icon('satellite', 1780, 600, '#127c89', 42);
svg += text(1605, 624, 'ESA Gaia DR3', 'card-title') + text(1512, 680, 'Stellar astrometry and motion') + text(1512, 708, '5 arcsec cone · max 20 rows', 'small');
svg += '<path d="M1512 735H1828" stroke="#d6e1eb"/>' + logo('cds', 1512, 752, 75, 42) + icon('stars', 1780, 754, '#127c89', 42);
svg += text(1605, 784, 'CDS SIMBAD', 'card-title') + text(1512, 840, 'Known identities and object types') + text(1512, 868, '5 arcsec cone · max 20 rows', 'small');
svg += '<path d="M1512 900H1828" stroke="#d6e1eb"/>' + logo('ipac', 1512, 923, 64, 46) + icon('database', 1780, 920, '#127c89', 42);
svg += text(1605, 950, 'IRSA AllWISE', 'card-title') + text(1512, 1006, 'Infrared photometry and quality') + text(1512, 1034, '10 arcsec cone · max 20 rows', 'small');
svg += text(455, 1167, 'Runtime packaging: Docker Compose / IPM     •     TAP transport: Java PEX via %Java Server', 'small');
svg += line(50, 1245, 1850, 1245) + text(50, 1283, 'Solid arrows: application calls and data flow', 'small') + text(650, 1283, 'Dashed arrows: conditional review or optional embedding path', 'small');
svg += text(50, 1320, 'Architecture illustration, not execution evidence. Positional proximity, semantic similarity and ACCEPT do not confirm a discovery.', 'small') + '</svg>';
await writeFile(join(here, 'system-architecture.svg'), svg);
await sharp(Buffer.from(svg)).resize(2850).png().toFile(join(here, 'system-architecture.png'));
console.log('Architecture SVG and PNG rendered');

// Mermaid CLI renders in its own headless browser; no user browser session is touched.
const cli = join(resolve(toolRoot), 'node_modules/@mermaid-js/mermaid-cli/src/cli.js');
const puppeteer = process.env.GAIA_CHROME ? { executablePath: process.env.GAIA_CHROME } : {};
const configFile = join(here, '.puppeteer.tmp.json');
const themeFile = join(here, '.mermaid.tmp.json');
await writeFile(configFile, JSON.stringify(puppeteer));
await writeFile(themeFile, JSON.stringify({ theme: 'neutral', fontFamily: 'Arial', sequence: { wrap: true, useMaxWidth: false, width: 220 } }));
try {
  for (let i = 0; i < diagrams.length; i++) {
    const input = join(here, `${names[i]}.tmp.mmd`);
    await writeFile(input, diagrams[i]);
    const result = spawnSync(process.execPath, [cli, '-i', input, '-o', join(here, `${names[i]}-mermaid.png`), '-p', configFile, '-c', themeFile, '-b', 'white', '-s', '2'], { encoding: 'utf8', timeout: 60000, windowsHide: true });
    const { unlink } = await import('node:fs/promises');
    await unlink(input);
    if (result.status !== 0) throw new Error(`Mermaid render failed: ${names[i]}\n${result.stderr || result.error}`);
    console.log(`Mermaid renderer PASS: ${names[i]}`);
    if (i === 0) await unlink(join(here, `${names[i]}-mermaid.png`));
  }
} finally {
  const { unlink } = await import('node:fs/promises');
  await unlink(configFile);
  await unlink(themeFile);
}
