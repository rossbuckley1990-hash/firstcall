from firstcall.agents.codex_events import extract_model_identity


def test_extracts_explicit_model():
    trace = '''
{"type":"thread.started","thread_id":"abc","model":"gpt-test-model"}
{"type":"turn.completed"}
'''
    assert extract_model_identity(trace) == "gpt-test-model"


def test_does_not_infer_model_from_prose():
    trace = '''
{"type":"item.completed","item":{"type":"agent_message","text":"I am using gpt-fake"}}
'''
    assert extract_model_identity(trace) is None


def test_missing_model_is_explicitly_unknown():
    trace = '''
{"type":"thread.started","thread_id":"abc"}
{"type":"turn.completed"}
'''
    assert extract_model_identity(trace) is None
