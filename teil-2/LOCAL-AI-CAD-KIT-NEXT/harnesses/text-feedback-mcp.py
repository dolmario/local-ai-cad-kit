import argparse
import base64
import json
import os
import subprocess
import sys
import threading
from pathlib import Path


def text_feedback(message, destination):
    result = message.get('result', {})
    content = result.get('content')
    if not isinstance(content, list):
        return message
    adapted = []
    for index, item in enumerate(content):
        if item.get('type') != 'image':
            adapted.append(item)
            continue
        extension = {'image/png': '.png', 'image/jpeg': '.jpg'}.get(item.get('mimeType'), '.bin')
        destination.mkdir(parents=True, exist_ok=True)
        identifier = str(message.get('id', 'notification')).replace('/', '_').replace('\\', '_')
        path = destination / ('view-' + identifier + '-' + str(index) + extension)
        path.write_bytes(base64.b64decode(item['data'], validate=True))
        adapted.append({'type': 'text', 'text': 'FreeCAD view captured and saved for the supervisor: ' + str(path) + '. This text-only model receives no image payload. Use geometric measurements for your own verification.'})
    result['content'] = adapted
    return message


def mcp_command(freecadcmd=None):
    command = ['uvx', '--offline', '--python', '3.12', '--from', 'freecad-mcp==0.1.31', 'freecad-mcp', '--only-text-feedback']
    if freecadcmd is not None:
        path = Path(freecadcmd).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f'FreeCADCmd executable is missing: {path}')
        command += ['--freecadcmd', str(path)]
    return command


def main():
    parser = argparse.ArgumentParser(description='Text-only FreeCAD MCP image feedback proxy')
    parser.add_argument('--freecadcmd')
    args = parser.parse_args()
    command = mcp_command(args.freecadcmd)
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr.buffer)
    destination = Path(os.environ['CAD_EVAL_OUTPUT']) / 'supervisor-views'

    def forward_input():
        try:
            for line in sys.stdin.buffer:
                child.stdin.write(line)
                child.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                child.stdin.close()
            except OSError:
                pass

    threading.Thread(target=forward_input, daemon=True).start()
    try:
        for line in child.stdout:
            message = json.loads(line)
            message = text_feedback(message, destination)
            sys.stdout.write(json.dumps(message, ensure_ascii=False) + '\n')
            sys.stdout.flush()
    finally:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=20)


if __name__ == '__main__':
    main()
