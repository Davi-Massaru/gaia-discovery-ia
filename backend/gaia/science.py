import csv
import io
import json
import math
import re
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

CATALOGS = {
    'GAIA': ('https://gea.esac.esa.int/tap-server/tap/sync', 'gaiadr3.gaia_source', 'source_id,ra,dec,parallax,pmra,pmdec,phot_g_mean_mag,ruwe', 'source_id', 5),
    'SIMBAD': ('https://simbad.cds.unistra.fr/simbad/sim-tap/sync', 'basic', 'main_id,ra,dec,otype', 'main_id', 5),
    'IRSA': ('https://irsa.ipac.caltech.edu/TAP/sync', 'allwise_p3as_psd', 'designation,ra,dec,w1mpro,w2mpro,ph_qual', 'designation', 10),
}


def now():
    return datetime.now(timezone.utc).isoformat()


def coordinates(ra, dec):
    if isinstance(ra, bool) or isinstance(dec, bool):
        raise ValueError('Invalid coordinates')
    ra, dec = float(ra), float(dec)
    if not math.isfinite(ra) or not math.isfinite(dec) or not 0 <= ra < 360 or not -90 <= dec <= 90:
        raise ValueError('Coordinates outside ICRS bounds')
    return ra, dec


def separation(ra1, dec1, ra2, dec2):
    ra1, dec1 = coordinates(ra1, dec1)
    ra2, dec2 = coordinates(ra2, dec2)
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    x = math.cos(d2) * math.sin(r2-r1)
    y = math.cos(d1)*math.sin(d2)-math.sin(d1)*math.cos(d2)*math.cos(r2-r1)
    z = math.sin(d1)*math.sin(d2)+math.cos(d1)*math.cos(d2)*math.cos(r2-r1)
    return math.degrees(math.atan2(math.hypot(x, y), z))*3600


def query(catalog, ra, dec, radius=None):
    endpoint, table, columns, _, default = CATALOGS[catalog]
    ra, dec = coordinates(ra, dec)
    radius = default if radius is None else float(radius)
    if not math.isfinite(radius) or not 0 < radius <= default:
        raise ValueError('Search radius outside catalog bounds')
    adql = (f'SELECT TOP 20 {columns} FROM {table} WHERE '
            f"1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra:.10f},{dec:.10f},{radius/3600:.12f}))")
    return endpoint, adql, radius


def parse_catalog(catalog, transport, ra, dec, adql, radius):
    result = dict(source=catalog, status='ERROR', timestamp=now(), sanitized_endpoint=CATALOGS[catalog][0],
                  sanitized_query=adql, radiusArcsec=radius, matches=[])
    allowed_endpoints = [CATALOGS[catalog][0]]
    if catalog == 'SIMBAD':
        allowed_endpoints.append('https://simbad.cfa.harvard.edu/simbad/sim-tap/sync')
    actual_endpoint = transport.get('endpoint', allowed_endpoints[0])
    if actual_endpoint not in allowed_endpoints:
        result['error'] = 'INVALID_TAP_ENDPOINT'
        return result
    result['sanitized_endpoint'] = actual_endpoint
    def metadata(raw):
        safe = {}
        for name in ('httpStatus', 'elapsedMs'):
            value = raw.get(name)
            if type(value) is int and value >= 0:
                safe[name] = value
        for name in ('errorType', 'errorCode', 'failurePhase', 'method'):
            value = raw.get(name)
            if isinstance(value, str) and re.fullmatch(r'[A-Za-z_]{1,80}', value):
                safe[name] = value
        if raw.get('endpoint') in allowed_endpoints:
            safe['endpoint'] = raw['endpoint']
        return safe
    result['transport'] = metadata(transport)
    result['transport']['attempts'] = [metadata(item) for item in transport.get('attempts', [])[:2] if isinstance(item, dict)]
    if transport.get('status') != 'OK' or transport.get('httpStatus') != 200:
        result['error'] = transport.get('errorCode', 'TAP_TRANSPORT_ERROR')
        return result
    try:
        body = transport['csvBody'].lstrip('\ufeff')
        if not body.strip() or body.lstrip().startswith(('<', '{', '[')):
            raise ValueError('TAP did not return CSV')
        reader = csv.DictReader(io.StringIO(body), strict=True)
        required = CATALOGS[catalog][2].split(',')
        if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
            raise ValueError('Invalid TAP schema')
        matches = []
        for row in reader:
            if len(matches) >= 20 or None in row or any(row.get(k) is None for k in required):
                raise ValueError('Invalid or oversized TAP rows')
            cra, cdec = coordinates(row['ra'], row['dec'])
            identifier = row[CATALOGS[catalog][3]]
            if not identifier:
                raise ValueError('Missing source identifier')
            distance = separation(ra, dec, cra, cdec)
            if distance > radius + 0.01:
                raise ValueError('TAP row outside requested cone')
            match = {k: row[k] or None for k in required}
            for key in required:
                if key not in ('source_id', 'main_id', 'designation', 'otype', 'ph_qual', 'ra', 'dec'):
                    value = row[key].strip()
                    if value.lower() in ('', 'null', 'nan'):
                        match[key] = None
                    else:
                        number = float(value)
                        if not math.isfinite(number):
                            raise ValueError('Nonfinite catalog measurement')
                        match[key] = number
            match.update(id=str(identifier), ra=cra, dec=cdec, separationArcsec=distance)
            match['associationCaution'] = 'Position-only proximity is not identity; epochs and positional uncertainties differ.'
            if catalog == 'GAIA':
                match['epoch'] = 2016.0
                match['properMotionCaution'] = 'Gaia DR3 epoch 2016.0; pmra includes cos(dec). No uncertainty-aware epoch propagation was applied.'
            elif catalog == 'IRSA':
                match['blendingCaution'] = 'AllWISE has a broader PSF; blending and epoch differences limit association.'
            matches.append(match)
        result.update(status='OK' if matches else 'EMPTY', matches=sorted(matches, key=lambda m: m['separationArcsec']))
    except (ValueError, TypeError, KeyError, csv.Error):
        result['error'] = 'INVALID_TAP_RESPONSE'
    return result


def validate_decision(decision, done, count):
    # The checked-in schema is authoritative, including additionalProperties=false.
    import jsonschema
    schema = json.loads((Path(__file__).resolve().parents[2] / 'docs/contracts/AI_HUB_DECISION.schema.json').read_text())
    jsonschema.validate(decision, schema)
    action = decision['next_action']
    if count >= 4 or (action != 'FINISH' and (action[6:] in done or len(done) >= 3)):
        raise ValueError('Agent exceeded distinct catalog/decision budget')
    return decision


def observation(row, object_id):
    def identifier(value):
        if type(value) not in (str, int) or not re.fullmatch(r'[0-9]{1,100}', str(value)):
            raise ValueError('Missing or invalid Fink source identifier')
        return str(value)
    object_id = identifier(object_id)
    out = {'diaObjectId': object_id, 'diaSourceId': identifier(row.get('r:diaSourceId')),
           'raDeg': row.get('r:ra'), 'decDeg': row.get('r:dec'), 'observedMjdTai': row.get('r:midpointMjdTai'),
           'psfFlux': row.get('r:psfFlux'), 'psfFluxErr': row.get('r:psfFluxErr')}
    if str(row.get('r:diaObjectId', object_id)) != str(object_id) or not out['diaSourceId']:
        raise ValueError('Detection does not belong to requested object')
    out['raDeg'], out['decDeg'] = coordinates(out['raDeg'], out['decDeg'])
    for key in ['observedMjdTai', 'psfFlux', 'psfFluxErr']:
        if out[key] is None or isinstance(out[key], bool) or not math.isfinite(float(out[key])):
            raise ValueError('Missing or invalid observation ' + key)
        out[key] = float(out[key])
    if not 30000 < out['observedMjdTai'] < 100000 or out['psfFluxErr'] <= 0:
        raise ValueError('Invalid observation time or flux uncertainty')
    return out


def validate_png(data):
    if not isinstance(data, bytes) or not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data)>4*1024*1024:
        raise ValueError('Invalid PNG cutout')
    offset, seen_header, seen_pixels = 8, False, False
    while offset+12<=len(data):
        length=struct.unpack('>I',data[offset:offset+4])[0]
        kind=data[offset+4:offset+8]
        end=offset+12+length
        if end>len(data):raise ValueError('Truncated PNG chunk')
        payload=data[offset+8:offset+8+length]
        crc=struct.unpack('>I',data[end-4:end])[0]
        if zlib.crc32(kind+payload)&0xffffffff != crc:raise ValueError('Invalid PNG checksum')
        if not seen_header:
            if kind!=b'IHDR' or length!=13:raise ValueError('Missing PNG header')
            width,height=struct.unpack('>II',payload[:8])
            if not 0<width<=4096 or not 0<height<=4096:raise ValueError('Invalid PNG dimensions')
            seen_header=True
        elif kind==b'IHDR':raise ValueError('Duplicate PNG header')
        if kind==b'IDAT':seen_pixels=True
        if kind==b'IEND':
            if length or end!=len(data) or not seen_pixels:raise ValueError('Invalid PNG end')
            return
        offset=end
    raise ValueError('Incomplete PNG cutout')
