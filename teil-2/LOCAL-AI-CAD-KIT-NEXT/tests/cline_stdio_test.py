import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


KIT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt' and shutil.which('node') and shutil.which('uv'),
                     'requires the Windows Cline toolchain')
class WindowsClineTransportTest(unittest.TestCase):
    def test_arguments_and_stdio_survive_the_windows_shell(self):
        spec = importlib.util.spec_from_file_location('configure', KIT / 'harnesses/configure.py')
        configure = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(configure)
        with tempfile.TemporaryDirectory(prefix='CAD kit with spaces ') as temp:
            kit = Path(temp)
            harnesses = kit / 'harnesses'
            harnesses.mkdir()
            shutil.copyfile(KIT / 'harnesses/cline-stdio.py', harnesses / 'cline-stdio.py')
            argument = str(kit / 'FreeCAD 1.1' / 'FreeCADCmd.exe')
            probe = kit / 'read arguments and stdin.py'
            probe.write_text(
                "import json,sys\n"
                "print(json.dumps([sys.argv[1:], sys.stdin.readline().strip()]))\n"
                "print('probe stderr', file=sys.stderr)\n"
                "sys.exit(3)\n", encoding='utf-8')
            transport = configure.cline_transport(kit, [sys.executable, str(probe), argument])
            runner = """
                const {spawn} = require('node:child_process');
                const cfg = JSON.parse(process.argv[1]);
                const proc = spawn(cfg.command, cfg.args, {
                    cwd: cfg.cwd, env: {...process.env, ...cfg.env},
                    shell: true, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe']
                });
                proc.stdin.end('CAD stdio probe\\n');
                proc.stdout.pipe(process.stdout);
                proc.stderr.pipe(process.stderr);
                proc.on('exit', code => { process.exitCode = code; });
            """
            result = subprocess.run(['node', '-e', runner, json.dumps(transport)],
                                    capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertEqual(json.loads(result.stdout), [[argument], 'CAD stdio probe'])
            self.assertIn('probe stderr', result.stderr)


if __name__ == '__main__':
    unittest.main()
