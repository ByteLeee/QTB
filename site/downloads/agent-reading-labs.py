#!/usr/bin/env python3
"""12 small, runnable infrastructure labs for the QTB Agent reading series.

Python 3.9+; standard library only; no network, credentials or LLM.
Lab 10 launches the included minimal local stdio MCP teaching server.
Keep this file, agent-control-experiment.py and agent-mcp-lab.py together.
Run: python3 agent-reading-labs.py --episode 7 --output trace.json
Run all: python3 agent-reading-labs.py --all
Each lab first exposes a failure, then checks a specific repair against external
state. These fixtures do not measure model intelligence, token cost, or latency.
Temporary files are automatically removed. Only --output persists a file.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def lab01():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'note.txt'
        path.touch()
        claimed_success = path.exists()
        verified_success = path.read_text(encoding='utf-8') == 'feedback'
        check(claimed_success and not verified_success, 'Empty-file trap disappeared')
        path.write_text('feedback', encoding='utf-8')
        check(path.read_text(encoding='utf-8') == 'feedback', 'Readback differs')
        return {'failure': 'file exists but content is empty', 'before': False,
                'after': True, 'evidence': 'file content read back as feedback'}


def lab02():
    path = Path(__file__).with_name('agent-control-experiment.py')
    spec = importlib.util.spec_from_file_location('qtb_control', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for case in module.CASES:
        fixed = module.run(case, module.fixed_policy(case))
        adaptive = module.run(case, module.simulated_policy)
        check(fixed['pass'] and adaptive['pass'], 'Controller result regressed')
        rows.append({'case': case['id'], 'fixed': fixed, 'adaptive': adaptive})
    return {'failure': 'fixed workflow reads irrelevant documents', 'rows': rows,
            'limitation': 'deterministic policies; required-document list is supplied'}


def lab03():
    def execute(policy, budget):
        trace, observation = [], {}
        for _ in range(budget):
            action = policy(observation.copy())
            if action == 'finish':
                trace.append({'action': 'finish'})
                return trace, 'finished'
            if action != 'read':
                return trace, 'invalid_action'
            observation = {'answer': '09:00'}
            trace.append({'action': action, 'result': observation.copy()})
        return trace, 'step_budget'
    trace, reason = execute(lambda observation: 'read', 3)
    repaired, repaired_reason = execute(lambda observation: 'finish' if observation else 'read', 3)
    zero, zero_reason = execute(lambda observation: 'finish', 0)
    check(len(trace) == 3 and reason == zero_reason == 'step_budget' and not zero,
          'Step budget was exceeded or mistaken for completion')
    check(repaired_reason == 'finished' and repaired[-1]['action'] == 'finish',
          'Policy did not use the new observation to finish')
    return {'failure': 'unbounded repeat policy', 'stopped_by': 'step_budget',
            'trace': trace, 'repaired_trace': repaired}


def validate_write(arguments):
    if set(arguments) != {'name', 'content', 'overwrite'}:
        return 'schema_error'
    if not isinstance(arguments['name'], str) or not arguments['name']:
        return 'name_error'
    if Path(arguments['name']).name != arguments['name'] or arguments['name'] in {'.', '..'}:
        return 'scope_error'
    if not isinstance(arguments['content'], str) or not isinstance(arguments['overwrite'], bool):
        return 'type_error'
    return 'accepted'


def lab04():
    rows = [({'data': 'hello', 'mode': 'save'}, 'schema_error'),
            ({'name': '../note.txt', 'content': 'hello', 'overwrite': False}, 'scope_error'),
            ({'name': 'note.txt', 'content': 'hello', 'overwrite': 'false'}, 'type_error'),
            ({'name': 'note.txt', 'content': 'hello', 'overwrite': False}, 'accepted')]
    trace = []
    for arguments, expected in rows:
        result = validate_write(arguments)
        check(result == expected, 'Tool contract mismatch')
        trace.append({'arguments': arguments, 'result': result})
    return {'failure': 'valid-looking JSON has the wrong meaning or scope',
            'trace': trace, 'limitation': 'does not measure the effect on a real model'}


def support(claim, evidence):
    # Deliberately narrow deterministic verifier, not general semantic entailment.
    return claim == evidence.get('fact') and evidence.get('kind') == 'primary'


def lab05():
    claim = 'A says feedback changes output'
    search_hit = {'id': 'commentary', 'fact': 'B discusses feedback', 'kind': 'commentary'}
    primary = {'id': 'author-A', 'fact': claim, 'kind': 'primary'}
    check(not support(claim, search_hit), 'Related text was treated as support')
    check(support(claim, primary), 'Matching evidence was rejected')
    return {'failure': 'related search hit used to assert an author attribution',
            'rejected': search_hit, 'accepted': primary,
            'limitation': 'exact fixture equality; natural-language support needs separate evaluation'}


def lab06():
    stale = {'path': 'old/note.txt', 'version': '1', 'permission': 'write'}
    current = {'path': 'new/note.txt', 'version': '2', 'permission': 'read'}
    lossy_summary = {'task': 'edit the note'}
    required = {'path', 'version', 'permission'}
    check(not required <= lossy_summary.keys(), 'Lossy compression was accepted')
    checkpoint = {key: current[key] for key in required}
    check(checkpoint != stale and checkpoint['permission'] == 'read', 'Stale permission survived')
    return {'failure': 'summary dropped changed path and permission',
            'stale_memory': stale, 'rejected_summary': lossy_summary,
            'checkpoint': checkpoint, 'limitation': 'fields are chosen for this task only'}


def lab07():
    naive = []
    for _ in range(2):
        naive.append('note')  # First commit happened; its reply was lost.
    store = {}
    trace = []
    for attempt in range(2):
        token, body = 'request-001', 'note'
        if token in store:
            check(store[token] == body, 'Same request ID used for different content')
            trace.append({'attempt': attempt, 'result': 'same_result_no_new_write'})
        else:
            store[token] = body
            trace.append({'attempt': attempt, 'result': 'committed_reply_lost'})
    changed_intent_rejected = store['request-001'] != 'different note'
    check(len(naive) == 2 and len(store) == 1 and changed_intent_rejected, 'Idempotency broken')
    return {'failure': 'timeout retry created two notes', 'naive_writes': len(naive),
            'repaired_writes': len(store), 'trace': trace,
            'changed_intent_rejected': changed_intent_rejected,
            'limitation': 'in-memory model; production commit+token must be atomic and durable'}


def allowed(action, origin, grant):
    return origin == 'user' and action in grant


def lab08():
    grant = {'read', 'draft'}
    requests = [('read', 'user', True), ('draft', 'user', True),
                ('delete', 'user', False), ('publish', 'retrieved-document', False),
                ('read', 'retrieved-document', False)]
    trace = []
    for action, origin, expected in requests:
        result = allowed(action, origin, grant)
        check(result == expected, 'Untrusted content changed permissions')
        trace.append({'action': action, 'origin': origin, 'allowed': result})
    return {'failure': 'document text mistaken for a user grant', 'trace': trace,
            'limitation': 'demonstrates a boundary, not a complete prompt-injection defense'}


def lab09():
    cases = [{'id': 'normal', 'expected': 'saved', 'actual': 'saved'},
             {'id': 'empty', 'expected': 'rejected', 'actual': 'saved'},
             {'id': 'duplicate', 'expected': 'unchanged', 'actual': 'saved'},
             {'id': 'unauthorized', 'expected': 'denied', 'actual': 'saved'}]
    passed = [row for row in cases if row['actual'] == row['expected']]
    check(len(passed) == 1, 'Fixture unexpectedly changed')
    return {'failure': 'one successful demo hides three task failures',
            'demo_rate': '1/1', 'suite_rate': '1/4', 'cases': cases,
            'limitation': 'four designed cases; not a population reliability estimate'}


def lab10():
    requests = [
        {'jsonrpc': '2.0', 'id': 0, 'method': 'tools/list'},
        {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
         'params': {'protocolVersion': '2025-11-25', 'capabilities': {},
                    'clientInfo': {'name': 'qtb-lab-client', 'version': '1.0.0'}}},
        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
        {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
         'params': {'name': 'read_note', 'arguments': {'id': 'n1'}}},
        {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
         'params': {'name': 'read_note', 'arguments': {'id': 'missing'}}},
    ]
    process = subprocess.run([sys.executable, str(Path(__file__).with_name('agent-mcp-lab.py'))],
                             input=''.join(json.dumps(row)+'\n' for row in requests),
                             text=True, capture_output=True, timeout=10, check=True)
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    check([row['id'] for row in responses] == [0, 1, 2, 3, 4], 'Unexpected notification reply or request correlation')
    check('error' in responses[0], 'Pre-initialization call should fail')
    check(responses[1]['result']['protocolVersion'] == '2025-11-25', 'Version mismatch')
    check(responses[2]['result']['tools'][0]['name'] == 'read_note', 'Tool discovery failed')
    response = responses[3]
    check(not response['result']['isError'] and response['result']['content'][0]['text'] == 'feedback', 'Tool execution failed')
    check(responses[4]['result']['isError'], 'Tool error was lost')
    task_success = 'deadline' in response['result']['content'][0]['text']
    check(not task_success, 'Successful protocol reply was mistaken for task success')
    return {'failure': 'successful transport used to claim task completion',
            'requests': requests, 'responses': responses, 'task_success': task_success,
            'limitation': 'real local stdio teaching subset; no authentication or full MCP conformance'}


def lab11():
    workers = [{'answer': 'Monday', 'source': 'copied-blog'} for _ in range(3)]
    agreement = len({row['answer'] for row in workers}) == 1
    independent_sources = len({row['source'] for row in workers})
    primary = {'answer': 'Tuesday', 'source': 'original-notice'}
    check(agreement and independent_sources == 1, 'Correlated-error fixture changed')
    check(workers[0]['answer'] != primary['answer'], 'Fixture no longer contradicts primary')
    return {'failure': 'three agreeing workers copied the same wrong source',
            'workers': workers, 'independent_sources': independent_sources,
            'primary': primary, 'limitation': 'simulated workers; no multi-agent performance measurement'}


def lab12():
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory) / 'report.json'
        report = {'question': 'When?', 'answer': 'Tuesday', 'source': 'original-notice',
                  'scope': 'one fictional notice', 'unresolved': ['timezone'], 'run_id': 'run-001'}
        data = json.dumps(report, sort_keys=True).encode()
        destination.write_bytes(data)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        reread = json.loads(destination.read_text())
        check(reread == report, 'Delivered content differs from report')
        check(bool(reread['unresolved']), 'Unresolved limitations were hidden')
        # A later mutation must invalidate the old acceptance evidence.
        destination.write_text('{}', encoding='utf-8')
        check(hashlib.sha256(destination.read_bytes()).hexdigest() != digest, 'Mutation not detected')
        return {'failure': 'a delivery claim without versioned evidence',
                'report': report, 'accepted_sha256': digest, 'later_change_detected': True,
                'limitation': 'hash proves file identity, not the truth of the report'}


LABS = {index: globals()['lab%02d' % index] for index in range(1, 13)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--episode', type=int, choices=range(1, 13))
    group.add_argument('--all', action='store_true')
    parser.add_argument('--output', help='Save the JSON trace to this exact local path')
    args = parser.parse_args()
    rows = []
    for index in LABS if args.all else [args.episode]:
        result = LABS[index]()
        rows.append({'episode': index, 'pass': True, 'result': result})
        print('episode %02d: PASS — %s' % (index, result['failure']))
    payload = {'simulation': True, 'network': False, 'real_model': False, 'rows': rows}
    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('No model calls, token prices, latency or mobile audio were measured.')


if __name__ == '__main__':
    main()
