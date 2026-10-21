"""Where the build command runs: Windows (cmd), WSL (a Linux distro) or the native shell of this OS."""
import os, re, subprocess

ENVS = [('windows', 'Windows (cmd.exe)'), ('wsl', 'WSL (Linux distro, e.g. Ubuntu)'), ('native', 'This system\'s shell (Linux / macOS)')]
UNC = re.compile(r'^\\\\(?:wsl\$|wsl\.localhost)\\([^\\]+)(.*)$', re.I)


def default_env():
    """'' = not chosen yet (Windows only: we must ask, because WSL and cmd behave differently)."""
    return '' if os.name == 'nt' else 'native'


def wsl_distros():
    """Names of installed WSL distributions ([] if WSL is missing)."""
    if os.name != 'nt': return []
    try:
        r = subprocess.run(['wsl.exe', '-l', '-q'], capture_output=True, timeout=15, creationflags=0x08000000)
        txt = r.stdout.decode('utf-16-le', 'ignore') if b'\x00' in r.stdout else r.stdout.decode('utf-8', 'ignore')
        return [x.strip().strip('﻿') for x in txt.splitlines() if x.strip().strip('﻿')]
    except Exception: return []


def wsl_location(path, distro):
    """(distro, directory as wsl.exe wants it). \\\\wsl$\\Ubuntu\\home\\me\\p becomes /home/me/p and selects Ubuntu."""
    m = UNC.match(path or '')
    if m: return m.group(1), (m.group(2).replace('\\', '/') or '/')
    return distro, path


def invocation(env, distro, cmd, cwd):
    """-> (program, args, native_args or None). Everything is run through a shell so '&&', pipes and PATH tweaks work."""
    if env == 'wsl':
        d, wd = wsl_location(cwd, distro); a = ['-d', d] if d else []
        if wd: a += ['--cd', wd]
        return 'wsl.exe', a + ['-e', 'bash', '-lc', cmd], None  # login shell: picks up devkitPro / cmake paths from ~/.profile
    if env == 'windows' or (env == '' and os.name == 'nt'): return 'cmd.exe', [], f'/S /C "chcp 65001>nul & {cmd}"'
    return '/bin/sh', ['-c', cmd], None
