import json
import math
import time
import uuid
from .science import now


def iris_module():
    import iris
    return iris


def is_object(value):
    return value is not None and not isinstance(value, (str, int, float, bytes))


def check_status(status):
    if status != 1:
        raise RuntimeError('IRIS operation failed: ' + iris_module().system.Status.GetErrorText(status))


def run_get(run_id):
    raw = iris_module().gref('^GaiaRuns').get([run_id])
    return json.loads(raw) if raw else None


def run_put(state):
    iris = iris_module()
    global_ref = iris.gref('^GaiaRuns')
    global_ref[state['runId']] = json.dumps(state, allow_nan=False)


def new_run(tag, count):
    if type(count) is not int or not 1 <= count <= 20:
        raise ValueError('count must be an integer between 1 and 20')
    if not isinstance(tag, str) or not tag or len(tag) > 100:
        raise ValueError('tag is required')
    iris = iris_module()
    ref = iris.gref('^GaiaRuns')
    # Short-lived run status is bounded; report history stays in the SQL table.
    keys = list(ref.keys())
    for key in keys:
        run_key = key[0] if isinstance(key, list) else key
        old = run_get(run_key)
        if old and time.time() - old.get('createdEpoch', 0) > 7*86400:
            ref.kill([run_key])
    if len(list(ref.keys())) >= 1000:
        raise RuntimeError('Run status capacity reached')
    run_id = str(uuid.uuid4())
    run_put(dict(runId=run_id, tag=tag, count=count, status='ACCEPTED', completed=0,
                 reportIds=[], createdAt=now(), createdEpoch=time.time()))
    return run_id


def run_update(run_id, **updates):
    state = run_get(run_id)
    if state is None:
        raise ValueError('Unknown run')
    state.update(updates)
    run_put(state)


def validate_tag(tag):
    raw = iris_module().gref('^GaiaConfig').get(['supportedTags'])
    if not raw:
        raise RuntimeError('Fink tag catalog unavailable')
    if tag not in json.loads(raw):
        raise ValueError('Unsupported Fink tag')


def stream_bytes(stream, limit=4*1024*1024):
    if not is_object(stream):
        return None
    if stream.Size > limit:
        raise ValueError('Stream exceeds byte limit')
    stream.Rewind()
    chunks = []
    while not stream.AtEnd:
        part = stream.Read(32768)
        chunks.append(part.encode('latin1') if isinstance(part, str) else bytes(part))
    return b''.join(chunks)


def save_image(data):
    from .science import validate_png
    validate_png(data)
    stream = iris_module().cls('%Stream.GlobalBinary')._New()
    for offset in range(0, len(data), 32768):
        check_status(stream.Write(data[offset:offset+32768]))
    check_status(stream._Save())
    return str(stream._Id())


def open_image(ref):
    return iris_module().cls('%Stream.GlobalBinary')._OpenId(ref) if ref else None


def save_report(state, session_id):
    iris = iris_module()
    evidence = state['current']
    report = iris.cls('Gaia.Data.DiscoveryReport')._New()
    report.RunId = state['runId']
    report.Tag = state['tag']
    report.CreatedAt = now()
    report.InteropSessionId = str(session_id)
    evidence['interopSessionId'] = str(session_id)
    obs = evidence['observation']
    report.DiaObjectId = str(obs['diaObjectId'])
    report.DiaSourceId = str(obs.get('diaSourceId', ''))
    for prop, key in [('RA', 'raDeg'), ('Dec', 'decDeg'), ('ObservedMjdTai', 'observedMjdTai')]:
        if obs.get(key) is not None:
            setattr(report, prop, obs[key])
    for kind in ['science', 'template', 'difference']:
        ref = evidence.get('finkImages', {}).get(kind)
        if ref:
            setattr(report, kind.title()+'PNG', open_image(ref))
    report.Assessment = evidence.get('assessment', 'INCONCLUSIVE')
    report.Summary = evidence.get('summary', 'Insufficient evidence to complete the investigation.')[:4000]
    report.ReviewStatus = 'PENDING' if report.Assessment == 'REVIEW_CANDIDATE' else 'NOT_REQUIRED'
    if report.Assessment == 'INCONCLUSIVE':
        evidence['embeddingStatus'] = 'SKIPPED_INCONCLUSIVE'
    report.EvidenceJSON = json.dumps(evidence, allow_nan=False)
    report.SearchText = report.Summary
    check_status(report._Save())
    report_id = str(report._Id())
    state['reportId'] = report_id
    state.setdefault('reportIds', []).append(report_id)
    run_update(state['runId'], completed=len(state['reportIds']), reportIds=state['reportIds'])
    if report.Assessment == 'INCONCLUSIVE':
        return state
    # Optional indexing is deliberately outside the successful report save.
    try:
        from .embedding import embed
        vector = embed(report.SearchText)
        if vector:
            evidence['embeddingStatus'] = 'OK'
            iris.sql.exec('UPDATE Gaia_Data.DiscoveryReport SET SearchEmbedding=TO_VECTOR(?,FLOAT,1536), EmbeddingModel=?, EvidenceJSON=? WHERE ID=?', json.dumps(vector), 'text-embedding-3-small', json.dumps(evidence), report_id)
    except Exception as error:
        from .diagnostics import diagnostic, record_failure
        evidence['embeddingStatus'] = 'ERROR'
        code, details = diagnostic(error, 'REPORT_EMBEDDING_ERROR')
        record_failure(evidence, 'REPORT_EMBEDDING', code, details)
        report.EvidenceJSON = json.dumps(evidence)
        check_status(report._Save())
    return state


def report_get(report_id):
    report = iris_module().cls('Gaia.Data.DiscoveryReport')._OpenId(str(report_id))
    if not is_object(report):
        return None
    result = {name[0].lower()+name[1:]: getattr(report, name) for name in [
        'RunId', 'DiaObjectId', 'DiaSourceId', 'Tag', 'CreatedAt', 'InteropSessionId',
        'RA', 'Dec', 'ObservedMjdTai', 'Assessment', 'Summary', 'ReviewStatus']}
    result['id'] = str(report._Id())
    result['ra'] = result.pop('rA')
    result['evidence'] = json.loads(report.EvidenceJSON)
    result['images'] = {kind: is_object(getattr(report, kind.title()+'PNG')) for kind in ['science', 'template', 'difference']}
    return result


def validate_report_filters(status='', review_status=''):
    if status not in ('', 'INCONCLUSIVE', 'REVIEW_CANDIDATE', 'CATALOG_CONTEXT_FOUND'):
        raise ValueError('Invalid report status')
    if review_status not in ('', 'NOT_REQUIRED', 'PENDING', 'ACCEPTED_FOR_REVIEW', 'REJECTED', 'TASK_ERROR'):
        raise ValueError('Invalid review status')


def report_list(limit=20, offset=0, search='', status='', review_status=''):
    validate_report_filters(status, review_status)
    iris = iris_module()
    if search:
        from .embedding import search_previous
        return [report_get(item['id']) for item in search_previous(search, min(limit, 3), status, review_status)]
    filters, params = [], []
    for column, value in [('Assessment', status), ('ReviewStatus', review_status)]:
        if value:
            filters.append(column+'=?')
            params.append(value)
    where = ' WHERE '+' AND '.join(filters) if filters else ''
    rows = iris.sql.exec('SELECT ID FROM Gaia_Data.DiscoveryReport'+where+' ORDER BY ID DESC LIMIT ? OFFSET ?', *params, limit, offset)
    return [report_get(str(row[0])) for row in rows]


def review(report_id, action):
    # Own native string buffers before hashing or invoking IRIS again.
    action = str(action).encode('utf-8').decode('utf-8')
    report_id = str(report_id).encode('utf-8').decode('utf-8')
    status = {'ACCEPT': 'ACCEPTED_FOR_REVIEW', 'REJECT': 'REJECTED'}.get(action, 'TASK_ERROR')
    iris = iris_module()
    report = iris.cls('Gaia.Data.DiscoveryReport')._OpenId(str(report_id))
    if not is_object(report) or report.Assessment != 'REVIEW_CANDIDATE':
        raise ValueError('Review does not reference a candidate report')
    report.ReviewStatus = status
    evidence = json.loads(report.EvidenceJSON)
    evidence['review'] = dict(action=action, status=status, timestamp=now())
    report.EvidenceJSON = json.dumps(evidence)
    check_status(report._Save())
    return 1
