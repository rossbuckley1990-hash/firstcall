"""R07 NO_MACHINE_TRANSLATION / FAIL_CLOSED. Does not adjudicate eligibility."""
MECHANISM = 'NO_MACHINE_TRANSLATION'
VERSION = '1.0.0'

def evidence_requirement(*, required_predicate_has_english_support):
    if type(required_predicate_has_english_support) is not bool:
        raise ValueError('explicit human evidence assessment required')
    if required_predicate_has_english_support:
        return {'translation': None, 'code': None, 'reason': None}
    return {'translation': None, 'code': 'UNRESOLVED', 'reason': 'TRANSLATION_NOT_AVAILABLE'}
