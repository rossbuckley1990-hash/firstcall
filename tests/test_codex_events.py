import json

from firstcall.agents.codex_events import (
    extract_codex_evidence,
)


def jl(*events):
    return "\n".join(
        json.dumps(event)
        for event in events
    )


def test_agent_message_claim_is_parsed():
    stdout = jl({
        "type": "item.completed",
        "item": {
            "id": "item_2",
            "type": "agent_message",
            "text": 'FIRSTCALL_RESULT {"ok":true}'
        }
    })

    evidence = extract_codex_evidence(stdout)

    assert evidence.claim.found is True
    assert evidence.claim.ok is True


def test_started_command_is_not_completion_proof():
    stdout = jl({
        "type": "item.started",
        "item": {
            "id": "item_1",
            "type": "command_execution",
            "command": "/bin/zsh -lc 'python integration.py'",
            "aggregated_output": "",
            "status": "in_progress"
        }
    })

    evidence = extract_codex_evidence(stdout)

    assert evidence.candidate_execution_observed is False
    assert evidence.candidate_exit_code is None


def test_completed_success_is_exactly_parsed():
    stdout = jl({
        "type": "item.completed",
        "item": {
            "id": "item_1",
            "type": "command_execution",
            "command": "/bin/zsh -lc 'python integration.py'",
            "aggregated_output":
                'FIRSTCALL_RESULT {"ok":true,"stage":"complete"}\n',
            "exit_code": 0,
            "status": "completed"
        }
    })

    evidence = extract_codex_evidence(stdout)

    assert evidence.candidate_execution_observed is True
    assert evidence.candidate_exit_code == 0
    assert len(evidence.candidate_commands) == 1
    assert (
        evidence.candidate_commands[0].output
        == 'FIRSTCALL_RESULT {"ok":true,"stage":"complete"}\n'
    )
    assert evidence.claim.found is True
    assert evidence.claim.ok is True


def test_completed_failure_preserves_exit_and_output():
    stdout = jl({
        "type": "item.completed",
        "item": {
            "id": "item_1",
            "type": "command_execution",
            "command": "/bin/zsh -lc 'python integration.py'",
            "aggregated_output":
                'FIRSTCALL_RESULT {"ok":false,"stage":"request",'
                '"error_type":"HTTPError","http_status":403}\n',
            "exit_code": 1,
            "status": "failed"
        }
    })

    evidence = extract_codex_evidence(stdout)

    assert evidence.candidate_execution_observed is True
    assert evidence.candidate_exit_code == 1
    assert evidence.claim.found is True
    assert evidence.claim.ok is False
    assert evidence.claim.payload["stage"] == "request"
    assert evidence.claim.payload["error_type"] == "HTTPError"
    assert evidence.claim.payload["http_status"] == 403


def test_assistant_prose_mention_is_not_execution():
    stdout = jl({
        "type": "item.completed",
        "item": {
            "id": "item_1",
            "type": "agent_message",
            "text": "I would run python integration.py."
        }
    })

    evidence = extract_codex_evidence(stdout)

    assert evidence.candidate_execution_observed is False


def test_outer_success_does_not_override_nested_failure():
    stdout = jl(
        {
            "type": "item.completed",
            "item": {
                "id": "item_1",
                "type": "command_execution",
                "command": "python integration.py",
                "aggregated_output":
                    'FIRSTCALL_RESULT {"ok":false}\n',
                "exit_code": 1,
                "status": "failed"
            }
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 20
            }
        }
    )

    evidence = extract_codex_evidence(stdout)

    assert evidence.candidate_exit_code == 1
    assert evidence.claim.ok is False
