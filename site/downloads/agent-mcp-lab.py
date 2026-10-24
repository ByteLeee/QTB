#!/usr/bin/env python3
"""Minimal MCP 2025-11-25 stdio teaching server. Python 3.9+ / stdlib.

Start: python3 agent-mcp-lab.py
Newline-delimited JSON-RPC on stdin/stdout. No network or file writes.
Implements initialize, notifications/initialized, tools/list, tools/call, ping.
Only a teaching subset; not a full SDK or MCP conformance implementation.
Reference: https://modelcontextprotocol.io/docs/2025-11-25/learn/architecture
"""
import json
import sys

VERSION = '2025-11-25'
NOTES = {'n1': 'feedback'}
TOOL = {'name': 'read_note', 'description': 'Read one fictional note by its exact ID. No writes.',
        'inputSchema': {'type': 'object', 'properties': {'id': {'type': 'string'}},
                        'required': ['id'], 'additionalProperties': False}}


def serve():
    initialized = False
    ready = False
    for line in sys.stdin:
        request_id = None
        try:
            request = json.loads(line)
            if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
                raise ValueError('Invalid JSON-RPC request')
            request_id = request.get('id')
            method = request.get('method')
            params = request.get('params', {})
            if not isinstance(method, str) or not isinstance(params, dict):
                raise ValueError('Invalid method or params')
            # A notification has no reply, even when it is not understood.
            if 'id' not in request:
                if method == 'notifications/initialized' and initialized:
                    ready = True
                continue
            if method == 'initialize':
                initialized = True
                ready = False
                result = {'protocolVersion': VERSION, 'capabilities': {'tools': {}},
                          'serverInfo': {'name': 'qtb-reading-lab', 'version': '1.0.0'}}
            elif method == 'ping':
                result = {}
            elif not ready:
                raise ValueError('Initialize and send notifications/initialized first')
            elif method == 'tools/list':
                result = {'tools': [TOOL]}
            elif method == 'tools/call':
                arguments = params.get('arguments', {})
                if params.get('name') != TOOL['name']:
                    raise ValueError('Unknown tool')
                if not isinstance(arguments, dict) or set(arguments) != {'id'} or not isinstance(arguments['id'], str):
                    raise ValueError('Expected exactly one string note id')
                note_id = arguments['id']
                result = {'content': [{'type': 'text', 'text': NOTES.get(note_id, 'note_not_found')}],
                          'isError': note_id not in NOTES}
            else:
                print(json.dumps({'jsonrpc': '2.0', 'id': request_id,
                                  'error': {'code': -32601, 'message': 'Method not found'}}), flush=True)
                continue
            response = {'jsonrpc': '2.0', 'id': request_id, 'result': result}
        except json.JSONDecodeError:
            response = {'jsonrpc': '2.0', 'id': None,
                        'error': {'code': -32700, 'message': 'Parse error'}}
        except ValueError as error:
            response = {'jsonrpc': '2.0', 'id': request_id,
                        'error': {'code': -32602, 'message': str(error)}}
        print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    serve()
