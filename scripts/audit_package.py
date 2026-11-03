#!/usr/bin/env python3
"""Static audit of Gaia Discovery AI's refactored spec package; never requires network."""
from pathlib import Path
from urllib.parse import unquote
import ast, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
errors=[]
def fail(s): errors.append(s); print('FAIL',s)

base=[
 'README.md','SPEC.md','.gitignore','.env.example','agents/IA_HUB.agent.md',
 'docs/specification/WORKFLOW.md','docs/specification/TECHNOLOGY_MAP.md',
 'docs/specification/COMPONENT_MODELS.md','docs/specification/UI_SPEC.md',
 'docs/implementation/IMPLEMENTATION_GUIDE.md','docs/implementation/CLASS_MAP.md',
 'docs/implementation/CLASS_CONTRACTS.md','docs/implementation/CODEX_PROMPT.md',
 'docs/implementation/REVIEW_AND_VALIDATION.md',
 'docs/contest/BONUS_ASSESSMENT.md','docs/contest/BONUS_IMPLEMENTATION_PLAN.md',
 'docs/contracts/external_endpoints.json','docs/contracts/AI_HUB_DECISION.schema.json',
 'scripts/verify_contracts.py',
]
services=['FINK','GAIA','SIMBAD','IRSA','OPENAI_EMBEDDINGS','CROSSMATCH',
'JAVA_PEX_TAP_ADAPTER','VECTOR_HISTORY','INTERNAL_MESSAGES','API_ENDPOINT_INDEX','API_CONTRACT_EXAMPLES','WSGI_API']
base += [f'docs/contracts/{n}.md' for n in services]
components=['INGESTION','DISCOVERY_BPL','AI_HUB','CATALOGS_PEX','SCIENTIFIC_NORMALIZATION',
'VECTOR_HISTORY','REPORT_REVIEW','REST_UI','DEPLOYMENT']
base += [f'docs/specification/components/{i:02d}_{n}.md' for i,n in enumerate(components,1)]
for name in base:
 if not (ROOT/name).is_file(): fail('Missing '+name)
if (ROOT/'.env').exists() and '--workspace' not in sys.argv: fail('Do not package real .env secrets (use --workspace for local validation)')
if '--workspace' in sys.argv:
 for name in ['.gitignore','.dockerignore']:
  if '.env' not in (ROOT/name).read_text():fail('Missing credential exclusion in '+name)
for p in ROOT.rglob('*.md'):
 txt=p.read_text(encoding='utf8')
 clean=re.sub(r'(?ms)^```.*?^```\s*$', '',txt)
 for href in re.findall(r'\]\(([^)]+)\)',clean):
  href=href.strip('<>').split('#',1)[0]
  if not href or href.startswith(('https://','http://','mailto:','data:')): continue
  if not (p.parent/unquote(href)).exists(): fail(f'Broken link: {p.relative_to(ROOT)} -> {href}')
for p in ROOT.rglob('*.json'):
 try: json.loads(p.read_text(encoding='utf8'))
 except Exception as ex: fail(f'JSON: {p.relative_to(ROOT)} {ex}')
manifest=json.loads((ROOT/'docs/contracts/external_endpoints.json').read_text())
if len(manifest.get('sources',[]))!=4: fail('Expected Fink Gaia SIMBAD IRSA sources')
for src in manifest.get('sources',[]):
 if not src.get('base','').startswith('https://'):fail('Non-HTTPS source '+str(src.get('name')))
 for ep in src.get('endpoints',[]):
  if ep.get('method') not in ('GET','POST') or not ep.get('path','').startswith('/'):
   fail('Malformed endpoint manifest: '+str(ep))
schema=json.loads((ROOT/'docs/contracts/AI_HUB_DECISION.schema.json').read_text())
if schema.get('properties',{}).get('next_action',{}).get('enum')!=['CHECK_GAIA','CHECK_SIMBAD','CHECK_IRSA','FINISH']:
 fail('AI action schema mismatch')
if not {'CATALOG_CONTEXT_FOUND','REVIEW_CANDIDATE','INCONCLUSIVE'}.issubset(set(schema.get('properties',{}).get('assessment',{}).get('enum',[]))):
 fail('AI assessment schema mismatch')
for f in ('scripts/audit_package.py','scripts/verify_contracts.py'):
 try: ast.parse((ROOT/f).read_text(encoding='utf8'))
 except SyntaxError as ex: fail('Python invalid '+f+': '+str(ex))
spec=(ROOT/'SPEC.md').read_text()
for token in ['count` 1–20','default 5','AstronomyReviewer','EnsLib.Workflow.Operation',
 'EnsLib.Workflow.TaskRequest','TaskResponse.%Action','<sync>','Embedded Python','PEX',
 'CATALOG_CONTEXT_FOUND','GET` | `/api/discoveries/runs/{runId}']:
 if token not in spec:fail('Missing master invariant: '+token)
# WSGI boundary must remain canonical; guard against losing it in future refactors.
for required in ('SPEC.md','docs/implementation/CLASS_MAP.md',
                 'docs/implementation/CLASS_CONTRACTS.md',
                 'docs/specification/components/08_REST_UI.md',
                 'docs/contracts/WSGI_API.md'):
 content=(ROOT/required).read_text(encoding='utf8')
 if 'WSGI' not in content or 'Flask' not in content:
  fail('WSGI/Flask missing from '+required)
if (ROOT/'src/iris/Gaia/API/DiscoveryAPI.cls').exists():
 fail('Obsolete native REST class conflicts with Flask WSGI')
if 'Gaia.API.DiscoveryAPI` |' in (ROOT/'docs/implementation/CLASS_MAP.md').read_text():
 fail('Obsolete native REST class still in class map')
if 'backend/app.py' not in (ROOT/'docs/implementation/CLASS_MAP.md').read_text():
 fail('Python Flask WSGI entry point missing from class map')
for token in ['EnsLib.Workflow.Operation','AutoCreateRole' ,'EnsLib.Workflow.TaskRequest',
 'EnsLib.Workflow.TaskResponse','<sync>','TASK_ERROR']:
 if token not in (ROOT/'docs/specification/components/07_REPORT_REVIEW.md').read_text():
  fail('Missing native Workflow invariant: '+token)
if errors:print(f'FAIL: {len(errors)} problem(s)');sys.exit(1)
print(f'PASS: {len(base)} required files, relative links, JSON, API manifest, schemas and Python syntax')
