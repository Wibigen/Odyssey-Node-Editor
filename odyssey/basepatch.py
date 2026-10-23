"""Base patches: some plugins (Dear ImGui) need changes in your exlaunch project: support files and a few CMake lines.

A plugin asks for it in plugin.json:

    "base": {"title": "Dear ImGui on the exlaunch base", "payload": "base",
             "exact": ["imgui/"],
             "cmake": {"definitions": ["IMGUI_USER_CONFIG=\\"imgui_backend/nvn_imgui_config.h\\""],
                       "include_dirs": ["imgui", "src", "src/program", "libs", "libs/NintendoSDK", "libs/NintendoSDK/nn", "libs/NintendoSDK/nvn"],
                       "glob_sources": ["imgui/*.cpp"], "embed": ["romfs/ShaderData/imgui.bin"]}}

* Every file of <plugin>/<payload>/ is copied into the project ONLY when the project does not have it (matched by its last two path parts,
  e.g. nn/hid.h, so a base that keeps the same headers somewhere else is left alone; paths listed in "exact" are matched exactly).
  Nothing is ever overwritten.
* CMakeLists.txt gets one marked block with only the pieces it lacks (a backup CMakeLists.txt.odn-backup is kept the first time).
* "settings" (optional): choices shown in the base dialog, written into a small generated header of the project:
    "settings": {"file": "src/odn_imgui_config.h", "template": "#define MODE $mode\\n",
                 "fields": [{"id": "mode", "label": "Mode", "options": [["1", "Combo"], ["2", "Auto"]], "default": "1", "enabled_if": {"other_field": "1"}}]}
  Values are checked against the options (nothing else can reach the C++ file); the file is rewritten by the editor each time a choice changes.
* What was added is recorded in <project>/.odn/base_<plugin>.json, so "Remove" can take back exactly that and nothing else.
"""
import hashlib, json, os, re, shutil
from pathlib import Path

from .projectpath import cmake_file

SKIP_DIRS = {'build', '.git', 'deploy', '.odn', 'node_modules', '__pycache__'}
STD = re.compile(r'^(c?[a-z_0-9]+|(std|math|string|stdio|stdlib|stdint|stddef|stdarg|stdbool|stdalign|limits|assert|elf|ctype|time|errno|signal|setjmp|wchar|float|inttypes|locale)\.h|sys/[\w./]+|bits/[\w./]+)$')
BEGIN, END = '# >>> Odyssey Node Editor plugin: {} >>>', '# <<< Odyssey Node Editor plugin: {} <<<'
REV = 2  # revision of the CMake block layout (1: target_embed_binaries; 2: embeds the binary without mixing target_link_libraries signatures)


def key_of(rel):
    p = rel.split('/'); return '/'.join(p[-2:])


def sha1(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


class Report:
    def __init__(self): self.lines, self.warnings, self.ok = [], [], True
    def add(self, s): self.lines.append(s)
    def warn(self, s): self.warnings.append(s)
    def text(self): return '\n'.join(self.lines + ([''] + ['Warning: ' + w for w in self.warnings] if self.warnings else []))


class BasePatch:
    def __init__(self, plugin, project):
        self.pl, self.proj = plugin, Path(project); self.cfg = plugin.base or {}; self.root = plugin.path / self.cfg.get('payload', 'base')
        self.exact = tuple(self.cfg.get('exact') or []); self.cm = self.cfg.get('cmake') or {}
        self.manifest = self.proj / '.odn' / f'base_{plugin.id}.json'; self.cmakef = cmake_file(self.proj) or self.proj / 'CMakeLists.txt'

    # ---------- settings (generated header) ----------
    def settings(self):
        s = self.cfg.get('settings'); return s if isinstance(s, dict) and s.get('fields') and s.get('file') else None

    def setting_values(self, saved=None):
        """{field id: value}: the saved choice when it is one of the options, the default otherwise."""
        out = {}
        for f in (self.settings() or {}).get('fields', []):
            opts = [str(o[0]) for o in f.get('options', [])]; v = str((saved or {}).get(f['id'], f.get('default', opts[0] if opts else '')))
            out[f['id']] = v if v in opts else str(f.get('default', opts[0] if opts else ''))
        return out

    def config_text(self, values):
        s = self.settings(); t = s.get('template', '')
        for k, v in sorted(self.setting_values(values).items(), key=lambda kv: -len(kv[0])): t = t.replace('$' + k, v)
        return t

    def write_config(self, values):
        """Write the generated header (always replaced: it belongs to the editor). Returns the relative path, or '' when the plugin has no settings."""
        s = self.settings()
        if not s or not self.is_project(): return ''
        rel = s['file']; dst = self.proj / rel; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_text(self.config_text(values), 'utf-8')
        mf = self.load_manifest()
        if mf:  # keep the record up to date, so Remove can take the file back
            if rel not in mf.get('added', []): mf.setdefault('added', []).append(rel)
            mf.setdefault('hashes', {})[rel] = sha1(dst); self.manifest.write_text(json.dumps(mf, indent=1), 'utf-8')
        return rel

    # ---------- inspection ----------
    def payload(self):
        return sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*') if p.is_file()) if self.root.is_dir() else []

    def project_keys(self):
        keys, full = set(), set()
        for d, dirs, files in os.walk(self.proj):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            rel = Path(d).relative_to(self.proj).as_posix(); rel = '' if rel == '.' else rel + '/'
            for f in files: full.add(rel + f); keys.add(key_of(rel + f))
        return keys, full

    def is_project(self):
        return self.proj.is_dir() and self.cmakef.is_file()

    def state_of(self, rel, keys, full):
        if rel.startswith(self.exact): return 'ok' if rel in full else 'missing'
        return 'ok' if (rel in full or key_of(rel) in keys) else 'missing'

    def cmake_text(self):
        try: return self.cmakef.read_text('utf-8', 'replace')
        except Exception: return ''

    def cmake_pieces(self, own_block=False):
        """What the CMakeLists.txt lacks: {'target': name, 'defs': [...], 'dirs': [...], 'globs': [...], 'embed': [...]}. own_block=True counts the block this plugin already added."""
        t = self.cmake_text(); body = t if own_block else re.sub(re.escape(BEGIN.format(self.pl.id)) + r'.*?' + re.escape(END.format(self.pl.id)), '', t, flags=re.S)
        tgt = self.cm.get('target') if self.cm.get('target', 'auto') != 'auto' else self.target_name(body)
        defs = [d for d in self.cm.get('definitions', []) if d.split('=')[0] not in body]
        dirs = [d for d in self.cm.get('include_dirs', []) if (self.proj / d).is_dir() and f'${{PROJECT_SOURCE_DIR}}/{d}' not in body]
        globs = [g for g in self.cm.get('glob_sources', []) if g not in body and 'IMGUI_SOURCES' not in body]
        emb = [e for e in self.cm.get('embed', []) if not (os.path.basename(e) in body and ('target_embed_binaries' in body or '__add_binary_library' in body))]
        return dict(target=tgt, defs=defs, dirs=dirs, globs=globs, embed=emb)

    def has_block(self):
        return BEGIN.format(self.pl.id) in self.cmake_text()

    def status(self):
        """-> dict(project_ok, missing=[files], cmake=[missing pieces text], ready, added=bool)"""
        r = dict(project_ok=self.is_project(), missing=[], cmake=[], ready=False, applied=self.manifest.is_file())
        if not r['project_ok']: return r
        keys, full = self.project_keys(); r['missing'] = [p for p in self.payload() if self.state_of(p, keys, full) == 'missing']
        pc = self.cmake_pieces(own_block=True); r['cmake'] = [f'definition {d}' for d in pc['defs']] + [f'include folder {d}' for d in pc['dirs']] + [f'sources {g}' for g in pc['globs']] + [f'embedded binary {e}' for e in pc['embed']]
        if self.has_block() and f'(rev {REV},' not in self.cmake_text().split(END.format(self.pl.id))[0].split(BEGIN.format(self.pl.id))[-1].split('\n')[0]: r['cmake'].append('replace the CMake block of an older version')
        r['ready'] = not r['missing'] and not r['cmake']; return r

    # ---------- apply ----------
    def apply(self, values=None):
        rep = Report()
        if not self.is_project(): rep.ok = False; rep.add(f'Not an exlaunch CMake project (no CMakeLists.txt in {self.proj}).'); return rep
        keys, full = self.project_keys(); mf = self.load_manifest(); added = list(mf.get('added', [])); hashes = dict(mf.get('hashes', {})); copied = 0
        for rel in self.payload():
            if self.state_of(rel, keys, full) == 'ok': continue
            dst = self.proj / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(self.root / rel, dst); added.append(rel); hashes[rel] = sha1(dst); copied += 1
        rep.add(f'{copied} file(s) copied into the project, {len(self.payload()) - copied} already there (left untouched).')
        if self.settings() and not (self.proj / self.settings()['file']).exists():
            self.manifest.parent.mkdir(parents=True, exist_ok=True); added.append(self.settings()['file']); (self.proj / self.settings()['file']).parent.mkdir(parents=True, exist_ok=True)
            (self.proj / self.settings()['file']).write_text(self.config_text(values), 'utf-8'); hashes[self.settings()['file']] = sha1(self.proj / self.settings()['file']); rep.add('Generated ' + self.settings()['file'] + ' from your choices.')
        pc = self.cmake_pieces(); block = self.block(pc)
        if block:
            if not (self.proj / 'CMakeLists.txt.odn-backup').exists(): shutil.copyfile(self.cmakef, self.proj / 'CMakeLists.txt.odn-backup'); rep.add('Backup kept: CMakeLists.txt.odn-backup')
            t = self.cmake_text(); t = self.strip_block(t).rstrip('\n') + '\n\n' + block; self.cmakef.write_text(t, 'utf-8'); rep.add('CMakeLists.txt: added ' + ', '.join(self.pieces_text(pc)) + '.')
        else: rep.add('CMakeLists.txt already has everything needed.')
        if pc['embed'] and not self.embed_function():
            rep.warn('target_embed_binaries() is not defined in your CMake files (it comes with cmake/SwitchTools.cmake of the SMO exlaunch base): the shader file cannot be embedded until it is.')
        self.manifest.parent.mkdir(parents=True, exist_ok=True); self.manifest.write_text(json.dumps(dict(plugin=self.pl.id, version=self.pl.version, added=added, hashes=hashes, block=bool(block) or mf.get('block', False)), indent=1), 'utf-8')
        for u in self.unresolved(): rep.warn(f'#include "{u[0]}" in {u[1]} is not found in the include folders of your project.')
        rep.add('Rebuild: CMake picks up the new files at the next build.'); return rep

    def pieces_text(self, pc):
        return [x for x in ((f"{len(pc['defs'])} definition(s)" if pc['defs'] else ''), (f"{len(pc['dirs'])} include folder(s)" if pc['dirs'] else ''), ('sources ' + ', '.join(pc['globs']) if pc['globs'] else ''), ('embedded ' + ', '.join(os.path.basename(e) for e in pc['embed']) if pc['embed'] else '')) if x]

    def block(self, pc):
        if not (pc['defs'] or pc['dirs'] or pc['globs'] or pc['embed']): return ''
        L, tg = [BEGIN.format(self.pl.id) + f'  (rev {REV}, added by the plugin "' + self.pl.title + '"; remove it from the Plugin explorer)'], pc['target']
        for i, g in enumerate(pc['globs']): L += [f'file(GLOB ODN_{self.pl.id.upper().replace("-", "_")}_SRC{i} ${{PROJECT_SOURCE_DIR}}/{g})', f'target_sources({tg} PRIVATE ${{ODN_{self.pl.id.upper().replace("-", "_")}_SRC{i}}})']
        if pc['dirs']: L.append(f'target_include_directories({tg} PRIVATE ' + ' '.join(f'${{PROJECT_SOURCE_DIR}}/{d}' for d in pc['dirs']) + ')')
        if pc['defs']: L.append(f'target_compile_definitions({tg} PRIVATE ' + ' '.join(d.replace('"', '\\"') for d in pc['defs']) + ')')
        for e in pc['embed']:
            e = self.find_file(os.path.basename(e)) or e
            kw = self.link_keyword(tg)  # same library name as target_embed_binaries; linked with the SAME signature the project uses (CMake forbids mixing them)
            L += ['if (COMMAND __add_binary_library)', f'    __add_binary_library(__{tg}_embed_{os.path.basename(e)} "${{PROJECT_SOURCE_DIR}}/{e}")', f'    target_link_libraries({tg} {kw}__{tg}_embed_{os.path.basename(e)})',
                  'elseif (COMMAND target_embed_binaries)', f'    target_embed_binaries({tg} "${{PROJECT_SOURCE_DIR}}/{e}")', 'else ()', f'    message(WARNING "No way to embed {os.path.basename(e)} (cmake/SwitchTools.cmake not found): ImGui will not start")', 'endif ()']
        L.append(END.format(self.pl.id)); return '\n'.join(L) + '\n'

    def target_name(self, body):
        """Name of the executable target. add_executable(${SUBSDKX}) is resolved through set(SUBSDKX subsdk9)."""
        m = re.search(r'add_executable\(\s*([^\s)]+)', body); name = m[1] if m else 'subsdk9'
        for _ in range(3):
            v = re.fullmatch(r'\$\{(\w+)\}', name)
            if not v: break
            s = re.search(r'set\(\s*' + v[1] + r'\s+"?([\w.\-]+)"?\s*\)', body)
            if not s: return 'subsdk9'
            name = s[1]
        return name if re.fullmatch(r'[\w.\-]+', name) else 'subsdk9'

    def link_keyword(self, tg):
        """The keyword the project uses in its own target_link_libraries(<any target> PRIVATE ...) calls ('PRIVATE ', 'PUBLIC '...), '' for the plain form.
        CMake forbids mixing both signatures on one target, and the target is often written as a variable (${SUBSDKX}), so any call is looked at."""
        body = self.strip_block(self.cmake_text())
        kw = re.search(r'target_link_libraries\(\s*[^\s)]+\s+(PRIVATE|PUBLIC|INTERFACE)\b', body)
        if kw: return kw[1] + ' '
        return ''

    def strip_block(self, t):
        return re.sub(r'\n*' + re.escape(BEGIN.format(self.pl.id)) + r'.*?' + re.escape(END.format(self.pl.id)) + r'\n?', '\n', t, flags=re.S)

    def find_file(self, name):
        for d, dirs, files in os.walk(self.proj):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            if name in files: return (Path(d) / name).relative_to(self.proj).as_posix()

    def embed_function(self):
        for p in list(self.proj.glob('*.cmake')) + list(self.proj.glob('cmake/*.cmake')) + [self.cmakef]:
            try:
                if re.search(r'(function|macro)\s*\(\s*(target_embed_binaries|__add_binary_library)', p.read_text('utf-8', 'replace'), re.I): return True
            except Exception: pass
        return False

    # ---------- remove ----------
    def load_manifest(self):
        try: return json.loads(self.manifest.read_text('utf-8'))
        except Exception: return {}

    def revert(self):
        rep = Report(); mf = self.load_manifest(); gone = kept = 0
        for rel in mf.get('added', []):
            p = self.proj / rel
            if not p.is_file(): continue
            if sha1(p) == mf.get('hashes', {}).get(rel): p.unlink(); gone += 1
            else: kept += 1; rep.warn(f'{rel} was edited after it was added: left in place.')
        for rel in sorted(mf.get('added', []), key=len, reverse=True):  # remove the folders that became empty
            d = (self.proj / rel).parent
            while d != self.proj and d.is_dir() and not any(d.iterdir()): d.rmdir(); d = d.parent
        if self.has_block():
            self.cmakef.write_text(self.strip_block(self.cmake_text()).rstrip('\n') + '\n', 'utf-8'); rep.add('CMakeLists.txt: the plugin block was removed.')
            bk = self.proj / 'CMakeLists.txt.odn-backup'
            if bk.is_file() and bk.read_text('utf-8', 'replace').rstrip() == self.cmake_text().rstrip(): shutil.copyfile(bk, self.cmakef); bk.unlink()  # CMakeLists.txt is exactly as before: the backup is not needed any more
        if self.manifest.is_file(): self.manifest.unlink()
        if self.manifest.parent.is_dir() and not any(self.manifest.parent.iterdir()): self.manifest.parent.rmdir()
        rep.add(f'{gone} file(s) removed' + (f', {kept} kept' if kept else '') + '. Files that were already in your project were never touched.'); return rep

    # ---------- verification ----------
    def include_dirs(self):
        t = self.cmake_text(); dirs = {''}
        for m in re.finditer(r'\$\{(?:PROJECT_SOURCE_DIR|CMAKE_SOURCE_DIR|CMAKE_CURRENT_SOURCE_DIR)\}/([\w./\-]+)', t): dirs.add(m[1].rstrip('/'))
        return dirs

    def unresolved(self):
        """Quoted includes of the plugin's own source files that no include folder of the project can resolve (max 8)."""
        dirs = self.include_dirs(); bad = []; mf = self.load_manifest()
        for rel in mf.get('added', []):
            if not rel.endswith(('.cpp', '.h', '.hpp', '.c')) or rel.startswith(self.exact): continue
            try: txt = (self.proj / rel).read_text('utf-8', 'replace')
            except Exception: continue
            for m in re.finditer(r'#\s*include\s*"([^"]+)"', txt):
                h = m[1]
                if STD.match(h) or h == 'imgui_bin.h' or h == 'imgui.h': continue
                if any((self.proj / d / h).is_file() for d in dirs) or (self.proj / Path(rel).parent / h).is_file(): continue
                if not any(b[0] == h for b in bad): bad.append((h, rel))
        return bad[:8]
