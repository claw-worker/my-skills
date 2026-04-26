#!/usr/bin/env python3
import argparse
import base64
import json
import locale
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def resolve_absolute_path(path_value):
  return os.path.abspath(os.path.expanduser(path_value))


def read_windows_env(name, scope):
  if os.name != 'nt':
    return None

  try:
    import winreg
  except ImportError:
    return None

  if scope == 'User':
    hive = winreg.HKEY_CURRENT_USER
    sub_key = 'Environment'
    access = winreg.KEY_READ
  elif scope == 'Machine':
    hive = winreg.HKEY_LOCAL_MACHINE
    sub_key = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    access = winreg.KEY_READ
    if hasattr(winreg, 'KEY_WOW64_64KEY'):
      access |= winreg.KEY_WOW64_64KEY
  else:
    return None

  try:
    with winreg.OpenKey(hive, sub_key, 0, access) as key:
      value, _ = winreg.QueryValueEx(key, name)
  except OSError:
    return None

  return value if isinstance(value, str) and value.strip() else None


def get_api_key_value(explicit_api_key):
  if explicit_api_key and explicit_api_key.strip():
    return explicit_api_key

  process_value = os.environ.get('OPENAI_API_KEY')
  if process_value and process_value.strip():
    return process_value

  for scope in ('User', 'Machine'):
    candidate = read_windows_env('OPENAI_API_KEY', scope)
    if candidate:
      return candidate

  raise RuntimeError('OPENAI_API_KEY is not set. Pass -ApiKey or export OPENAI_API_KEY first.')


def read_text_file(path):
  data = Path(path).read_bytes()
  encodings = ['utf-8-sig', locale.getpreferredencoding(False) or 'utf-8']
  for encoding in encodings:
    try:
      return data.decode(encoding)
    except UnicodeDecodeError:
      continue
  return data.decode('utf-8', errors='replace')


def get_prompt_text(prompt, prompt_file):
  if prompt and prompt_file:
    raise RuntimeError('Use -Prompt or -PromptFile, not both.')

  if prompt_file:
    prompt_path = resolve_absolute_path(prompt_file)
    if not os.path.exists(prompt_path):
      raise RuntimeError(f'Prompt file not found: {prompt_path}')
    return read_text_file(prompt_path)

  if prompt:
    return prompt

  raise RuntimeError('Missing prompt. Use -Prompt or -PromptFile.')


def ensure_parent_directory(path_value):
  parent = Path(path_value).parent
  parent.mkdir(parents=True, exist_ok=True)


def ensure_writable_target(path_value, force):
  if os.path.exists(path_value) and not force:
    raise RuntimeError(f'File already exists: {path_value}. Use -Force to overwrite.')


def write_json_utf8(path_value, payload):
  text = json.dumps(payload, ensure_ascii=False, indent=2)
  Path(path_value).write_text(text, encoding='utf-8', newline='\n')


def post_json(endpoint, api_key, request_path, response_path):
  body = Path(request_path).read_bytes()
  request = urllib.request.Request(
    endpoint,
    data=body,
    method='POST',
    headers={
      'Authorization': f'Bearer {api_key}',
      'Content-Type': 'application/json'
    }
  )

  try:
    with urllib.request.urlopen(request) as response:
      response_body = response.read()
  except urllib.error.HTTPError as exc:
    response_body = exc.read()
  except urllib.error.URLError as exc:
    reason = exc.reason if exc.reason else exc
    raise RuntimeError(f'HTTP request failed: {reason}') from exc

  Path(response_path).write_bytes(response_body)


def load_response_json(response_path):
  try:
    return json.loads(Path(response_path).read_text(encoding='utf-8'))
  except json.JSONDecodeError as exc:
    raise RuntimeError(f'Failed to parse JSON response: {exc}') from exc


def extract_image_base64(response):
  output_items = response.get('output') or []
  for item in output_items:
    if item.get('type') == 'image_generation_call' and item.get('result'):
      return item['result']
  raise RuntimeError('No image_generation_call.result found in the response.')


def parse_args():
  parser = argparse.ArgumentParser(description='Generate an image through the CIII Responses API.')
  parser.add_argument('-Prompt', '--prompt', dest='prompt')
  parser.add_argument('-PromptFile', '--prompt-file', dest='prompt_file')
  parser.add_argument('-OutFile', '--out-file', dest='out_file', default='.\\output.png')
  parser.add_argument('-Endpoint', '--endpoint', dest='endpoint', default='https://codex.ciii.club/v1/responses')
  parser.add_argument('-ApiKey', '--api-key', dest='api_key')
  parser.add_argument('-TextModel', '--text-model', dest='text_model', default='gpt-5.4')
  parser.add_argument('-ImageModel', '--image-model', dest='image_model', default='gpt-image-2')
  parser.add_argument('-Size', '--size', dest='size', default='1536x1024')
  parser.add_argument('-Quality', '--quality', dest='quality', default='high')
  parser.add_argument('-OutputFormat', '--output-format', dest='output_format', default='png')
  parser.add_argument('-Background', '--background', dest='background', default='opaque')
  parser.add_argument('-ToolChoice', '--tool-choice', dest='tool_choice', default='required')
  parser.add_argument('-RequestFile', '--request-file', dest='request_file')
  parser.add_argument('-ResponseFile', '--response-file', dest='response_file')
  parser.add_argument('-Force', '--force', dest='force', action='store_true')
  return parser.parse_args()


def main():
  args = parse_args()
  api_key = get_api_key_value(args.api_key)
  prompt_text = get_prompt_text(args.prompt, args.prompt_file)
  output_path = resolve_absolute_path(args.out_file)
  ensure_parent_directory(output_path)
  ensure_writable_target(output_path, args.force)

  output_dir = str(Path(output_path).parent)
  base_name = Path(output_path).stem
  request_path = resolve_absolute_path(args.request_file) if args.request_file else os.path.join(output_dir, f'{base_name}-request.json')
  response_path = resolve_absolute_path(args.response_file) if args.response_file else os.path.join(output_dir, f'{base_name}-response.json')

  for path_value in (request_path, response_path):
    ensure_parent_directory(path_value)
    ensure_writable_target(path_value, args.force)

  payload = {
    'model': args.text_model,
    'input': prompt_text,
    'tools': [
      {
        'type': 'image_generation',
        'model': args.image_model,
        'action': 'generate',
        'size': args.size,
        'quality': args.quality,
        'output_format': args.output_format,
        'background': args.background
      }
    ],
    'tool_choice': args.tool_choice
  }

  write_json_utf8(request_path, payload)
  post_json(args.endpoint, api_key, request_path, response_path)
  response = load_response_json(response_path)

  if response.get('error'):
    error_json = json.dumps(response['error'], ensure_ascii=False, separators=(',', ':'))
    raise RuntimeError(f'API error: {error_json}')

  if response.get('code') and response.get('message'):
    error_json = json.dumps({
      'code': response['code'],
      'message': response['message']
    }, ensure_ascii=False, separators=(',', ':'))
    raise RuntimeError(f'API error: {error_json}')

  image_bytes = base64.b64decode(extract_image_base64(response))
  Path(output_path).write_bytes(image_bytes)

  result = {
    'output_file': output_path,
    'request_file': request_path,
    'response_file': response_path,
    'response_id': response.get('id'),
    'model': response.get('model'),
    'status': response.get('status')
  }
  print(json.dumps(result, ensure_ascii=False, indent=2))
  return 0


if __name__ == '__main__':
  try:
    raise SystemExit(main())
  except Exception as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(1)
