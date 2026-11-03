from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, Response
from gaia import store

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4096
WEB = Path(__file__).resolve().parent.parent / 'web'


@app.errorhandler(ValueError)
def invalid(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(Exception)
def unavailable(error):
    from werkzeug.exceptions import HTTPException
    if isinstance(error, HTTPException):
        return jsonify(error=error.description), error.code
    return jsonify(error='IRIS backend unavailable'), 503


@app.post('/api/discoveries/run')
def start_run():
    body = request.get_json()
    if not isinstance(body, dict) or set(body) - {'tag', 'count'}:
        raise ValueError('Expected {tag,count}')
    count = body.get('count', 5)
    if type(count) is not int or not 1 <= count <= 20:
        raise ValueError('count must be an integer between 1 and 20')
    tag = body.get('tag')
    if not isinstance(tag, str) or not tag or len(tag) > 100:
        raise ValueError('tag is required')
    store.validate_tag(tag)
    # The adapterless service dispatches asynchronously; no BPL or review wait here.
    import iris
    run_id = iris.cls('Gaia.Interop.DiscoveryService').StartRun(tag, count)
    return jsonify(runId=run_id, status='ACCEPTED'), 202


@app.get('/api/discoveries/runs/<run_id>')
def get_run(run_id):
    result = store.run_get(run_id)
    return (jsonify(result), 200) if result else (jsonify(error='Run not found'), 404)


@app.get('/api/discoveries')
def list_reports():
    try:
        limit, offset = int(request.args.get('limit', 20)), int(request.args.get('offset', 0))
    except ValueError:
        raise ValueError('Invalid pagination')
    if not 1 <= limit <= 100 or not 0 <= offset <= 1000000:
        raise ValueError('Invalid pagination bounds')
    search = request.args.get('search', '')
    if len(search) > 2000:
        raise ValueError('Search exceeds 2000 characters')
    status, review_status = request.args.get('status', ''), request.args.get('review_status', '')
    store.validate_report_filters(status, review_status)
    return jsonify(items=store.report_list(limit, offset, search, status, review_status), limit=limit, offset=offset)


@app.get('/api/discoveries/<int:report_id>')
def get_report(report_id):
    result = store.report_get(report_id)
    return (jsonify(result), 200) if result else (jsonify(error='Report not found'), 404)


@app.get('/api/discoveries/<int:report_id>/images/<kind>')
def get_image(report_id, kind):
    if kind not in ('science', 'template', 'difference'):
        return jsonify(error='Image kind not found'), 404
    import iris
    report = iris.cls('Gaia.Data.DiscoveryReport')._OpenId(str(report_id))
    stream = getattr(report, kind.title()+'PNG') if store.is_object(report) else None
    if not store.is_object(stream):
        return jsonify(error='Cutout unavailable'), 404
    if request.environ.get('wsgi.run_once'):
        # EAP 154 iris_wsgi_interface decodes every yielded byte chunk as UTF-8.
        # Emit binary through the existing IRIS response device AFTER WSGI headers.
        def native_body():
            stream.Rewind()
            iris.cls('%REST.Impl')._WriteResponse(stream)
            yield b''
        return Response(native_body(), mimetype='image/png', headers={
            'Content-Length': str(stream.Size), 'Cache-Control': 'private, max-age=3600'})
    return Response(store.stream_bytes(stream), mimetype='image/png', headers={'Cache-Control': 'private, max-age=3600'})


@app.get('/')
def index():
    import html
    import json
    import iris
    tags = iris.gref('^GaiaConfig').get(['supportedTags']) or '[]'
    safe_tags = json.dumps(json.loads(tags)).replace('<', '\\u003c')
    page = (WEB/'index.html').read_text().replace('__SUPPORTED_TAGS__', safe_tags)
    page = page.replace('<head>', '<head><base href="'+html.escape(request.script_root.rstrip('/')+'/', quote=True)+'">')
    return Response(page, mimetype='text/html')


@app.get('/assets/<path:name>')
def assets(name):
    return send_from_directory(WEB, name)
