# Diagram sources and reproduction

These illustrations describe the implemented architecture and BPL paths. They are not IRIS Visual Trace captures or evidence that a new investigation ran.

## Assets

| Asset | Source | Use |
|---|---|---|
| `logos/fink.svg` | [Official Fink primary logo](https://fink-broker.org/Fink_PrimaryLogo_WEB.svg), [identity and attribution](https://fink-broker.org/visual-identity/branding/) | Fink alert broker; logo by Justin Burks |
| `logos/intersystems.svg` | [InterSystems documentation logo](https://docs.intersystems.com/irislatest/csp/docbook/doc-logo.svg) | Identifies the IRIS runtime vendor |
| `logos/esa.svg` | [ESA Brand Centre asset](https://brand.esa.int/wp-content/themes/brandcentre/assets/img/ESA_Logo.svg), [brand page](https://brand.esa.int/assets/logotype/) | Identifies ESA, provider of Gaia DR3 |
| `logos/cds.png` | Embedded CDS header logo in the [official SIMBAD mirror stylesheet](https://simbad.cfa.harvard.edu/cds-navbar-resources/css/cdsnavbar.min.css) | Identifies CDS, provider of SIMBAD |
| `logos/ipac.png` | [Official IPAC logo](https://irsa.ipac.caltech.edu/frontpage/images/ipac_logo-56x40.png), [IRSA](https://irsa.ipac.caltech.edu/) | Identifies IPAC, which hosts IRSA |
| `logos/openai.svg` | [Simple Icons 13.21.0 asset](https://raw.githubusercontent.com/simple-icons/simple-icons/13.21.0/icons/openai.svg), [OpenAI brand guidelines](https://openai.com/brand/) | Identifies the implemented OpenAI provider |

Logos retain their original colors and proportions, embedded in the SVG/PNG so GitHub does not need to load remote assets. They identify the systems involved and do not imply endorsement or partnership. Trademarks belong to their owners. Fink publishes its logo for non-commercial use under the terms on its identity page; those terms remain applicable. The telescope, satellite, database, browser, agent and person pictograms are original SVG line drawings in `render.mjs`, not vendor logos.

## Regenerate

`render.mjs` is documentation tooling only. It reads the four Mermaid blocks in the root README, validates them with the Mermaid parser, checks local README links, draws the branded architecture, and renders each Mermaid block with the official CLI in a separate headless browser. It never connects to IRIS, loads credentials, uses a browser profile, or changes application dependencies.

Use Node.js compatible with the Mermaid CLI and a local Chrome/Chromium executable. Install tools into a temporary directory, outside the repository:

```powershell
$env:GAIA_DOC_TOOLS = Join-Path $env:TEMP 'gaia-readme-tools'
$env:PUPPETEER_SKIP_DOWNLOAD = 'true'
npm.cmd install --prefix $env:GAIA_DOC_TOOLS --no-save --package-lock=false `
  @mermaid-js/mermaid-cli@11.12.0 sharp@0.34.5 jsdom@26
$env:GAIA_CHROME = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
node docs/diagrams/render.mjs
```

For parser/link checks without launching Chrome or regenerating images:

```powershell
node docs/diagrams/render.mjs --check
```

The branded source is `system-architecture.svg`; its exported PNG is 2850 × 2040 pixels. `batch-ingestion-mermaid.png`, `adaptive-investigation-mermaid.png` and `human-review-mermaid.png` are generated directly from the corresponding README blocks. The architecture Mermaid block is also rendered for verification; its redundant PNG is removed by the renderer after the check.

## Documentation verification — November 8, 2026

- Reproduced the original parser failures in all three sequence diagrams. Unescaped semicolons split message text into separate Mermaid statements; replacing them with conjunctions/commas fixes the actual grammar error. See [Mermaid sequence syntax](https://mermaid.js.org/syntax/sequenceDiagram) and [GitHub diagram documentation](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).
- All four corrected blocks passed the Mermaid parser and rendered successfully through Mermaid CLI 11.12.0. Exported images were visually inspected for text, arrow direction and clipping.
- The diagram follows `Gaia.Production`, `DiscoveryWorkflow` BPL, the native agent Operation, Python persistence/history and the shared Java transport. The satellite icon identifies Gaia's space mission context; SIMBAD/AllWISE remain catalog services, not direct satellite integrations.
- The original task's domain narrative, workflow inventory, agent contract, catalog bounds, source map, installation, guided tutorials, screenshots, verification and attribution remain in the README.
- At the time of the November 8 revision, Docker was unavailable and no authenticated Visual Trace capture could be obtained. The November 9 live validation documented in the root README adds real application screenshots and the authenticated native Visual Trace of session 210 under `docs/screenshots/`, with the matching session/message export under `docs/evidence/`; these remain distinct from the generated diagrams.
- This revision changes documentation and diagram assets only. The 31-test result referenced in the README belongs to the earlier November 3 verification; it is not represented as a new runtime test.
