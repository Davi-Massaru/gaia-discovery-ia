"""Allowlisted technical diagnostics. Raw provider errors are never persisted."""
import re


def diagnostic(error, default='PROVIDER_ERROR'):
    message = str(error).lower()
    code = default
    for markers, candidate in [
        (('spend limit', 'spend_limit'), 'OPENAI_SPEND_LIMIT_EXCEEDED'),
        (('insufficient_quota',), 'OPENAI_INSUFFICIENT_QUOTA'),
        (('invalid_api_key', 'incorrect api key'), 'OPENAI_AUTHENTICATION_FAILED'),
        (('missing_api_key',), 'OPENAI_KEY_MISSING'),
        (('model_not_found',), 'OPENAI_MODEL_UNAVAILABLE'),
        (('rate_limit', 'rate limit'), 'OPENAI_RATE_LIMITED'),
        (('timeout', 'timed out'), 'PROVIDER_TIMEOUT'),
    ]:
        if any(marker in message for marker in markers):
            code = candidate
            break
    kind = type(error).__name__ if not isinstance(error, str) else 'NativeAIHubError'
    details = {'errorType': kind if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', kind) else 'ProviderError'}
    status = getattr(error, 'code', None)
    if type(status) is int and 100 <= status <= 599:
        details['httpStatus'] = status
    return code, details


def record_failure(evidence, stage, code, details=None, fatal=False):
    item = dict(failureStage=stage, failureCode=code, diagnostic=details or {})
    evidence.setdefault('technicalFailures', []).append(item)
    # An optional indexing/history failure must not hide a fatal reasoning failure.
    if fatal or evidence.get('executionStatus') != 'FAILED':
        evidence.update(executionStatus='FAILED' if fatal else 'DEGRADED', **item)
