'use strict';
const $ = s => document.querySelector(s);
const base = new URL('.', document.baseURI);
let offset = 0, pollTimer, generation = 0;
const escape = v => String(v ?? 'Unavailable').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const badge = v => `<span class="badge ${escape(v)}">${escape(v)}</span>`;
const imageURL = (id, kind) => new URL(`api/discoveries/${encodeURIComponent(id)}/images/${kind}`, base).href;
const mjd = value => value == null || value === '' ? 'Unavailable' : `${Number(value).toFixed(6)} MJD TAI`;
const observedDate = value => value == null || value === '' ? 'Unavailable' : `${new Date((Number(value)-40587)*86400000).toISOString().replace('T',' ').replace('Z',' TAI')}`;

function notice(message) { $('#notice').textContent = message; $('#notice').hidden = !message; }
async function api(path, body) {
  const response = await fetch(new URL(path, base), body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  let result;
  try { result = await response.json(); } catch { result = {}; }
  if (!response.ok) { const error = new Error(result.error || (response.status===401?'Authentication required.':`Request failed (${response.status})`)); error.status=response.status; throw error; }
  if (!result || typeof result!=='object') throw new Error('Invalid API response.');
  $('#connection').textContent = 'IRIS connected'; $('#connection').classList.add('connected');
  return result;
}
function imageErrors() {
  document.querySelectorAll('img').forEach(img => img.addEventListener('error', () => { const text = document.createElement('span'); text.textContent = 'Image unavailable'; img.replaceWith(text); }, {once:true}));
}
async function feed() {
  const token = ++generation;
  $('#feed').hidden=false; $('#report').hidden=true;
  $('#reports').innerHTML='<p class="empty">Loading saved reports…</p>';
  const search = $('#search').value.trim();
  $('#semantic-note').hidden = !search;
  const data = await api(`api/discoveries?limit=20&offset=${offset}&search=${encodeURIComponent(search)}&status=${encodeURIComponent($('#status-filter').value)}&review_status=${encodeURIComponent($('#review-filter').value)}`);
  if (token !== generation) return;
  $('#reports').innerHTML = data.items.length ? data.items.map(r => `<article class="report-row">
    <a href="#report/${encodeURIComponent(r.id)}" class="thumbnail" aria-label="Open report ${escape(r.id)}">${r.images.science ? `<img src="${imageURL(r.id,'science')}" alt="Saved Science cutout" loading="lazy">` : 'Image unavailable'}</a>
    <div><h3><a href="#report/${encodeURIComponent(r.id)}">Investigation #${escape(r.id)}</a></h3><p class="mono">Rubin ${escape(r.diaObjectId)}</p><p class="metadata">Observed ${escape(observedDate(r.observedMjdTai))} · ${escape(r.tag)}</p><p class="metadata">Processed ${escape(r.createdAt)}</p></div>
    <div class="report-actions">${badge(r.assessment)}<p class="metadata">Review: ${escape(r.reviewStatus)}</p><a class="open-link" href="#report/${encodeURIComponent(r.id)}">Open report ↗</a></div></article>`).join('') : '<p class="empty">No saved investigations found.</p>';
  $('#previous').disabled = offset === 0 || !!search; $('#next').disabled = data.items.length < 20 || !!search; $('#page-number').textContent=String(offset/20+1);
  imageErrors();
}
async function report(id) {
  const token=++generation;
  $('#feed').hidden=true; $('#report').hidden=false; $('#report').innerHTML='<p class="empty">Loading investigation…</p>';
  const r=await api(`api/discoveries/${encodeURIComponent(id)}`);
  if(token!==generation)return;
  const e=r.evidence;
  const decisions=e.decisionHistory || [];
  $('#report').innerHTML=`<a class="back" href="#feed">← Back to reports</a><div class="report-header"><p class="eyebrow">PERSISTED SCIENTIFIC INVESTIGATION</p><h1>Investigation #${escape(r.id)}</h1><div class="badges">${badge(r.assessment)}${badge(r.reviewStatus)}</div><div class="ids"><div class="mono"><small>RUBIN OBJECT</small>${escape(r.diaObjectId)}</div><div class="mono"><small>DETECTION</small>${escape(r.diaSourceId)}</div><div class="mono"><small>ICRS POSITION</small>${escape(r.ra)}°, ${escape(r.dec)}°</div></div><p class="metadata">Observed ${escape(observedDate(r.observedMjdTai))} (${escape(mjd(r.observedMjdTai))}) · Tag ${escape(r.tag)}<br>Processed ${escape(r.createdAt)}</p></div>
    <div class="images">${['science','template','difference'].map(kind=>`<figure class="cutout"><figcaption>${kind}</figcaption><div class="frame">${r.images[kind]?`<a href="${imageURL(r.id,kind)}" target="_blank" rel="noopener" aria-label="View original ${kind} PNG"><img src="${imageURL(r.id,kind)}" alt="Authentic Fink ${kind} cutout"></a>`:'<span class="muted">Image unavailable</span>'}</div></figure>`).join('')}</div><p class="image-note">Vera C. Rubin Observatory · Fink-provided cutouts from detection ${escape(r.diaSourceId)}. Pixel-preserving enlargement; AI Hub reasons over structured evidence.</p>
    <div class="report-layout"><div>${e.executionStatus?`<section class="panel"><h2>Execution status</h2>${badge(e.executionStatus)}${(e.technicalFailures||[]).map(f=>`<p class="review-note">${escape(f.failureStage)} · ${escape(f.failureCode)}</p>`).join('')}<p class="review-note">Technical execution is tracked separately from scientific assessment.</p></section>`:''}<section class="panel"><p class="eyebrow">NATIVE IRIS AI HUB</p><h2>Scientific assessment</h2><p class="summary">${escape(r.summary)}</p>${(e.errors||[]).map(err=>`<p class="review-note">${escape(err)}</p>`).join('')}<p class="review-note">Preliminary investigation. No confirmed discovery or definitive source association.</p></section>
    <section class="panel"><h2>Hypothesis & evidence timeline</h2><ol class="timeline">${decisions.length ? decisions.map((d,i)=>`<li><small>DECISION ${i+1} · ${escape(d.next_action)}</small><p><strong>${escape(d.hypothesis)}</strong></p>${d.alternative?`<p>Alternative: ${escape(d.alternative)}</p>`:''}${d.question?`<p>Question: ${escape(d.question)}</p>`:''}<p>${escape(d.reason)}</p><p class="mono">${escape(d.timestamp)}</p></li>`).join(''):'<li><p>No valid AI decision was recorded. The report preserves the failure and available observations.</p></li>'}</ol>
    ${(e.evidenceTimeline||[]).map(item=>`<p class="review-note">${escape(item.source)} · ${escape(item.status)} · ${escape(item.interpretation)}</p>`).join('')}${Object.entries(e.scientificEvidence||{}).map(([group,items])=>`<h3>${escape(group)}</h3>${items.length?items.map(item=>`<p class="review-note">${escape(item.source)} · ${escape(item.fact)}</p>`).join(''):'<p class="review-note">No explicit evidence recorded in this category.</p>'}`).join('')}</section>
    <section class="panel"><h2>Related investigations</h2><p class="review-note">Semantic analogies from saved reports, not astronomical crossmatches.</p>${(e.historicalAnalogies||[]).map(h=>`<a class="related" href="#report/${encodeURIComponent(h.id)}">Investigation #${escape(h.id)}</a><p class="review-note">${escape(h.summary)} · Similarity ${Number(h.similarity).toFixed(3)}</p>`).join('')||'<p class="review-note">No historical analogies available.</p>'}${e.historyStatus==='ERROR'?'<p class="review-note">Optional history search was unavailable.</p>':''}</section></div>
    <aside><section class="panel"><h2>Scientific sources</h2><div class="source"><div class="source-title"><h3>Fink / Rubin</h3>${badge(e.errors?.some(v=>v.startsWith('FINK')||v.startsWith('MISSING')||v==='INCOMPLETE_CUTOUTS')?'ERROR':'OK')}</div><p>Alert measurements and authentic cutouts.</p><details><summary>Source provenance</summary><pre>${escape(JSON.stringify(e.provenance||[],null,2))}</pre></details></div>
    ${Object.entries(e.catalogs||{}).map(([name,c])=>`<div class="source"><div class="source-title"><h3>${escape(name)}</h3>${badge(c.status)}</div><p>${c.status==='NOT_REQUESTED'?'Not requested by AI Hub.':c.status==='ERROR'?'Catalog unavailable; candidate count is unknown.':`${(c.matches||[]).length} candidate association(s).`}</p>${c.error?`<p>${escape(c.error)}</p>`:''}${c.timestamp?`<p class="mono">${escape(c.timestamp)}</p>`:''}${(c.matches||[]).map(m=>`<details><summary>${escape(m.id)} · ${Number(m.separationArcsec).toFixed(3)}″</summary><pre>${escape(JSON.stringify(m,null,2))}</pre></details>`).join('')}${c.sanitized_query?`<details><summary>Query & endpoint</summary><pre>${escape(c.sanitized_endpoint)}\n${escape(c.sanitized_query)}${c.transport?'\n\nTransport: '+escape(JSON.stringify(c.transport,null,2)):''}</pre></details>`:''}</div>`).join('')}</section>
    <section class="panel"><h2>Native human review</h2>${badge(r.reviewStatus)}<p class="review-note">Reviewers use the native IRIS Workflow Inbox. Acceptance means further scientific investigation.</p></section><section class="panel"><h2>Interoperability trace</h2><p class="mono">Session ${escape(r.interopSessionId)}</p><p class="review-note">Find this session in IRIS Management Portal → Interoperability → Visual Trace.</p></section></aside></div>`;
  imageErrors();
}
async function route() {
  notice('');
  try { const match=location.hash.match(/^#report\/(\d+)$/); if(match)await report(match[1]);else await feed(); }
  catch(error){notice(error.message);const failed=error.status===undefined||error.status>=500||error.status===401;$('#connection').textContent=failed?'API unavailable':'IRIS connected';$('#connection').classList.toggle('connected',!failed);if($('#report').hidden)$('#reports').innerHTML='<p class="empty">'+escape(error.message)+'</p>';else $('#report').innerHTML='<a class="back" href="#feed">← Back to reports</a><p class="empty">'+escape(error.message)+'</p>';}
}
async function pollRun(id) {
  try {
    const run=await api(`api/discoveries/runs/${encodeURIComponent(id)}`);
    $('#run-status').textContent=`Run ${run.status} · ${run.completed || 0}/${run.total ?? run.count} investigated${run.error?' · '+run.error:''}`;
    if(['COMPLETED','NO_ALERTS','FAILED'].includes(run.status)){ $('#fetch').disabled=false; if(!location.hash.startsWith('#report/'))await feed();return; }
    pollTimer=setTimeout(()=>pollRun(id),2000);
  }catch(error){notice(error.message);$('#fetch').disabled=false;}
}
$('#run-form').addEventListener('submit',async event=>{
  event.preventDefault();notice('');$('#fetch').disabled=true;
  try {const form=new FormData(event.target);const run=await api('api/discoveries/run',{tag:form.get('tag'),count:Number(form.get('count'))});$('#run-status').hidden=false;$('#run-status').textContent=`Run ${run.status}`;clearTimeout(pollTimer);await pollRun(run.runId);}
  catch(error){notice(error.message);$('#fetch').disabled=false;}
});
$('#search-form').addEventListener('submit',event=>{event.preventDefault();offset=0;route();});
['#status-filter','#review-filter'].forEach(selector=>$(selector).addEventListener('change',()=>{offset=0;route();}));
$('#refresh').addEventListener('click',route);
$('#previous').addEventListener('click',()=>{offset=Math.max(0,offset-20);route();});
$('#next').addEventListener('click',()=>{offset+=20;route();});
window.addEventListener('hashchange',route);
const tags=JSON.parse($('#supported-tags').textContent);
// Descriptions summarized from the official Fink /api/v1/tags metadata.
const tagDescriptions={
  extragalactic_lt20mag_candidate:'Bright, rising extragalactic candidates with magnitude below 20.',
  extragalactic_new_candidate:'Recent extragalactic candidates first seen less than 5 days ago, with magnitude below 24 and a brightness-change rate that meets the filter criteria.',
  faint_trails:'Faint trails longer than 2 arcseconds, with magnitudes between 18 and 21.',
  hostless_candidate:'Candidates without an identified host galaxy according to the ELEPHANT method.',
  in_tns:'Alerts associated with an object already listed in the Transient Name Server (TNS), either as a candidate or a confirmed event.',
  mdwarf_flare:'Likely flares from M dwarf stars, selected in bluer bands at high airmass.',
  most_likely_sn:'Likely supernovae according to the SuperNNova and CATS classifiers.',
  sn_near_galaxy_candidate:'Candidates associated with a cataloged galaxy and showing properties consistent with supernovae.'
};
const tagDescription=tag=>tagDescriptions[tag]||'Fink alert filter. No description is available for this tag.';
$('#tag').innerHTML=tags.length?tags.map(tag=>`<option title="${escape(tagDescription(tag))}" ${tag==='extragalactic_new_candidate'?'selected':''}>${escape(tag)}</option>`).join(''):'<option disabled>Fink tags unavailable</option>';
function updateTagTooltip(){ $('#tag').title=tags.length?`${$('#tag').value}: ${tagDescription($('#tag').value)} Tags select candidates; they are not scientific confirmations.`:'Fink tags unavailable'; }
$('#tag').addEventListener('change',updateTagTooltip);
updateTagTooltip();
$('#fetch').disabled=tags.length===0;
if(!tags.length)notice('Fink tag catalog unavailable. Refresh after the Production starts.');
route();
