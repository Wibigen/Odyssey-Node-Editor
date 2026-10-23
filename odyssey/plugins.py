"""Plugin manager: finds, loads, enables / disables, installs and removes plugins (Qt-independent).

A plugin is a folder (or a .zip / .odnp file holding that folder) with a plugin.json:

    {"id": "stdio", "title": "Standard I/O", "author": "WibiDev", "version": "1.0.0", "description": "...", "icon": "icon.png",
     "nodes": [ ... ], "themes": [ ... ]}

nodes can also live in nodes.json (a list) or nodes/*.json; see plugnodes.py for the node format. A theme is
{"id": "midnight", "name": "Midnight", "base": "dark", "accent": "#5b8def", "colors": {"bg": "#0b0f1a", "node": "#151b2b"}}.
An optional plugin.py with  def register(api)  can do more (api.add_node, api.add_theme, api.add_action, api.log).
Every missing piece of information gets a default (title = folder name, author "Unknown author", version "0.0.0"...).
"""
from .i18n import tr, tr_n
import importlib.util, json, re, shutil, sys, zipfile
from pathlib import Path

from . import graph as G
from . import plugnodes as PN
from .config import DATA, resource
from .theme import PLUGIN_THEMES, register_theme

USER_DIR = DATA / 'plugins'
BUILTIN_DIR = resource('plugins')
DEFAULT_TITLE_FMT, DEFAULT_AUTHOR, DEFAULT_DESC, DEFAULT_VERSION = '{}', 'Unknown author', 'No description provided.', '0.0.0'
IMAGE_NAMES = ('icon.png', 'icon.jpg', 'icon.jpeg', 'icon.svg', 'logo.png', 'image.png')
SLUG = re.compile(r'[^a-z0-9_\-]+')


def slug(s):
    return SLUG.sub('-', (s or '').strip().lower()).strip('-') or 'plugin'


class Plugin:
    def __init__(self, path: Path, builtin: bool):
        self.path, self.builtin = Path(path), builtin
        self.id = slug(self.path.name); self.title, self.author, self.description, self.version = self.id, DEFAULT_AUTHOR, DEFAULT_DESC, DEFAULT_VERSION
        self.color = ''; self.image = None; self.nodes, self.themes, self.actions = [], [], []   # nodes: normalised defs, themes: (key, name)
        self.errors, self.enabled, self.loaded, self.has_python, self.shadowed = [], True, False, False, False
        self.read_manifest()

    # ---- manifest (every field is optional) ----
    def read_manifest(self):
        m = {}
        f = self.path / 'plugin.json'
        if f.is_file():
            try: m = json.loads(f.read_text('utf-8'))
            except Exception as e: self.errors.append(f'plugin.json: {e}')
        else: self.errors.append('plugin.json not found (defaults used)')
        if not isinstance(m, dict): self.errors.append('plugin.json must hold an object'); m = {}
        self.manifest = m; g = lambda k, d: (m.get(k) if isinstance(m.get(k), str) and m.get(k).strip() else d)
        self.id = slug(g('id', self.path.name)); self.title = g('title', g('name', self.id)); self.author = g('author', DEFAULT_AUTHOR)
        self.description = g('description', DEFAULT_DESC); self.version = str(m.get('version')) if m.get('version') not in (None, '') else DEFAULT_VERSION; self.color = g('color', '')
        names = ([m['icon']] if isinstance(m.get('icon'), str) else []) + list(IMAGE_NAMES)
        self.image = next((self.path / n for n in names if (self.path / n).is_file()), None)
        self.has_python = (self.path / 'plugin.py').is_file(); self.default_enabled = m.get('default_enabled', True) is not False
        self.catalog_file = next((self.path / n for n in ([m['catalog']] if isinstance(m.get('catalog'), str) else []) + ['catalog.json', 'functions.json'] if (self.path / n).is_file()), None); self.catalog_size = 0
        self.templates = self._templates(m); self.base = m.get('base') if isinstance(m.get('base'), dict) else None
        self.help = self._help(m)
        self.raw_nodes = self._raw_nodes(m); self.raw_themes = [t for t in (m.get('themes') or []) if isinstance(t, dict)]

    def _templates(self, m):
        out = []
        for t in m.get('templates') or []:
            if isinstance(t, dict) and isinstance(t.get('file'), str) and (self.path / t['file']).is_file(): out.append((str(t.get('name') or Path(t['file']).stem), self.path / t['file'], str(t.get('description') or '')))
        if not out and (self.path / 'templates').is_dir(): out = [(f.stem.replace('_', ' '), f, '') for f in sorted((self.path / 'templates').glob('*.odn'))]
        return out

    def _help(self, m):
        """Help pages: [(title, path to a .md file, [(button label, action)])]. From "help" in plugin.json, or every help/*.md."""
        out = []
        for h in m.get('help') or []:
            if isinstance(h, dict) and isinstance(h.get('file'), str) and (self.path / h['file']).is_file():
                btn = [(str(b.get('label')), str(b.get('do'))) for b in h.get('buttons') or [] if isinstance(b, dict) and b.get('label') and b.get('do')]
                out.append((str(h.get('title') or Path(h['file']).stem.replace('_', ' ')), self.path / h['file'], btn))
        if not out and (self.path / 'help').is_dir(): out = [(f.stem.replace('_', ' '), f, []) for f in sorted((self.path / 'help').glob('*.md'))]
        return out

    def _raw_nodes(self, m):
        raw = list(m.get('nodes') or [])
        try:
            if (self.path / 'nodes.json').is_file(): raw += json.loads((self.path / 'nodes.json').read_text('utf-8'))
            for f in sorted((self.path / 'nodes').glob('*.json')) if (self.path / 'nodes').is_dir() else []:
                j = json.loads(f.read_text('utf-8')); raw += j if isinstance(j, list) else [j]
        except Exception as e: self.errors.append(f'nodes: {e}')
        return raw

    def summary(self):
        bits = []
        if self.catalog_size: bits.append(tr('{0} catalog functions', self.catalog_size))
        if self.nodes: bits.append(tr_n('{0} node', '{0} nodes', len(self.nodes)))
        if self.templates: bits.append(tr_n('{0} template', '{0} templates', len(self.templates)))
        if self.help: bits.append(tr_n('{0} help page', '{0} help pages', len(self.help)))
        if self.themes: bits.append(tr_n('{0} theme', '{0} themes', len(self.themes)))
        if self.actions: bits.append(tr_n('{0} menu action', '{0} menu actions', len(self.actions)))
        return ' · '.join(bits) or ('nothing loaded' if not self.enabled else 'no content')

    def can_template(self): return bool(self.templates)


class PluginAPI:
    """What plugin.py receives in register(api)."""
    def __init__(self, mgr, plugin):
        self._m, self._p = mgr, plugin

    @property
    def window(self): return self._m.window
    @property
    def plugin_id(self): return self._p.id
    @property
    def data(self):  # a small dict saved for this plugin in the editor settings
        return self._m.data.setdefault(self._p.id, {}) if self._m.data is not None else {}

    def add_node(self, raw):
        try: d = PN.normalise(raw, self._p.id, self._p.title, self._p.color); G.register_plugin_node(d); self._p.nodes.append(d)
        except Exception as e: self._p.errors.append(f'node: {e}')

    def add_theme(self, theme_id, name, base='dark', colors=None, accent=''):
        k = f'{self._p.id}.{slug(theme_id)}'; register_theme(k, name, base, colors, accent, self._p.id); self._p.themes.append((k, name))

    def add_action(self, label, callback, shortcut=''):
        """A menu entry in the Plugins menu; callback(window) is called when it is chosen."""
        self._p.actions.append((label, callback, shortcut))

    def log(self, msg): self._m.log.append(f'[{self._p.id}] {msg}')


class PluginManager:
    def __init__(self):
        self.plugins, self.window, self.data, self.disabled, self.enabled_extra, self.log = [], None, None, set(), set(), []
        USER_DIR.mkdir(parents=True, exist_ok=True)

    # ---- discovery / loading ----
    def discover(self):
        found = {}
        for base, builtin in ((BUILTIN_DIR, True), (USER_DIR, False)):
            if not base.is_dir(): continue
            for p in sorted(base.iterdir()):
                if p.is_dir() and not p.name.startswith(('.', '_')):
                    pl = Plugin(p, builtin)
                    if pl.id in found: found[pl.id].shadowed = True  # an installed plugin replaces the bundled one with the same id
                    found[pl.id] = pl
        return list(found.values())

    def load_all(self, disabled=(), window=None, data=None, enabled=()):
        """(Re)load everything. disabled = ids switched off; enabled = ids switched on among the plugins that are off by default; data = dict kept in the settings for the plugins."""
        self.disabled, self.enabled_extra, self.window, self.data = set(disabled), set(enabled), window or self.window, data if data is not None else self.data
        G.clear_plugin_nodes(); PN.clear_catalogs(); PLUGIN_THEMES.clear(); self.log = []
        self.plugins = self.discover()
        for pl in self.plugins:
            pl.enabled = (pl.id in self.enabled_extra) if not pl.default_enabled else (pl.id not in self.disabled)
            if pl.enabled: self._load(pl)
        G.rebuild_palette()
        return self.plugins

    def _load(self, pl):
        for raw in pl.raw_nodes:
            try: d = PN.normalise(raw, pl.id, pl.title, pl.color); G.register_plugin_node(d); pl.nodes.append(d)
            except Exception as e: pl.errors.append(f'node "{raw.get("id") if isinstance(raw, dict) else "?"}": {e}')
        for t in pl.raw_themes:
            try:
                k = f"{pl.id}.{slug(t.get('id') or t.get('name'))}"; register_theme(k, str(t.get('name') or t.get('id') or k), t.get('base', 'dark'), t.get('colors'), t.get('accent', ''), pl.id); pl.themes.append((k, PLUGIN_THEMES[k]['name']))
            except Exception as e: pl.errors.append(f'theme: {e}')
        if pl.catalog_file:
            try:
                data = json.loads(pl.catalog_file.read_text('utf-8')); PN.add_catalog(pl.id, pl.title, data, pl.color); pl.catalog_size = len(PN.CATALOG[pl.id]['entries'])
            except Exception as e: pl.errors.append(f'catalog: {e}')
        if pl.has_python:
            try:
                spec = importlib.util.spec_from_file_location(f'odn_plugin_{pl.id.replace("-", "_")}', pl.path / 'plugin.py'); mod = importlib.util.module_from_spec(spec)
                sys.path.insert(0, str(pl.path))
                try: spec.loader.exec_module(mod)
                finally: sys.path.remove(str(pl.path))
                if hasattr(mod, 'register'): mod.register(PluginAPI(self, pl))
            except Exception as e: pl.errors.append(f'plugin.py: {type(e).__name__}: {e}')
        pl.loaded = True

    def set_enabled(self, cfg, pid, on):
        """Remember in the settings dict that a plugin is on / off (plugins that are off by default are listed in plugins_enabled, the others in plugins_disabled)."""
        pl = self.get(pid); off, extra = set(cfg.get('plugins_disabled', [])), set(cfg.get('plugins_enabled', []))
        if pl and not pl.default_enabled: (extra.add if on else extra.discard)(pid)
        else: (off.discard if on else off.add)(pid)
        cfg['plugins_disabled'], cfg['plugins_enabled'] = sorted(off), sorted(extra)

    def get(self, pid):
        return next((p for p in self.plugins if p.id == pid), None)

    # ---- install / remove / create ----
    def install(self, src):
        """Copy a plugin folder or .zip / .odnp into the user plugin folder. Returns the plugin id. Raises ValueError."""
        src = Path(src); USER_DIR.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            if not zipfile.is_zipfile(src): raise ValueError('this file is not a plugin archive (.zip / .odnp)')
            tmp = USER_DIR / '_incoming'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
            try:
                with zipfile.ZipFile(src) as z:
                    for name in z.namelist():  # refuse paths leaving the folder
                        if Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('unsafe path in the archive: ' + name)
                    z.extractall(tmp)
                roots = [p for p in tmp.iterdir()]
                root = roots[0] if len(roots) == 1 and roots[0].is_dir() and not (tmp / 'plugin.json').exists() else tmp
                return self._adopt(root, src.stem)
            finally: shutil.rmtree(tmp, ignore_errors=True)
        if src.is_dir(): return self._adopt(src, src.name)
        raise ValueError('nothing to install at ' + str(src))

    @staticmethod
    def has_python(src):
        """True when a plugin folder / archive contains Python code (it runs with the rights of the editor)."""
        src = Path(src)
        try:
            if src.is_dir(): return any(src.rglob('plugin.py'))
            with zipfile.ZipFile(src) as z: return any(n.endswith('plugin.py') for n in z.namelist())
        except Exception: return False

    def _adopt(self, root, fallback):
        pl = Plugin(root, False)
        if not (root / 'plugin.json').is_file() and not (root / 'nodes.json').is_file() and not (root / 'plugin.py').is_file(): raise ValueError('no plugin.json in this folder')
        pid = slug(pl.manifest.get('id') or fallback); dst = USER_DIR / pid
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(root, dst, ignore=shutil.ignore_patterns('__pycache__', '.git')); return pid

    def remove(self, pid):
        pl = self.get(pid)
        if not pl or pl.builtin or not str(pl.path).startswith(str(USER_DIR)): raise ValueError('only installed plugins can be removed (a bundled one can be disabled)')
        shutil.rmtree(pl.path)

    def create(self, title, author, description='', pid=''):
        """Make a ready-to-edit plugin skeleton in the user folder and return its id."""
        pid = slug(pid or title); d = USER_DIR / pid; n = 2
        while d.exists(): d = USER_DIR / f'{pid}-{n}'; n += 1
        d.mkdir(parents=True)
        man = dict(id=d.name, title=title or 'My plugin', author=author or DEFAULT_AUTHOR, version='1.0.0', description=description or 'Describe what your plugin adds.', icon='icon.png',
                   nodes=[dict(id='hello', label='Print hello', category=title or 'My plugin', description='Example node: writes a line to the console.', flow=True,
                               inputs=[dict(id='name', type='const char*', label='name', default='"world"')], template='printf("hello %s\\n", $name)', includes=['<cstdio>'])],
                   themes=[dict(id='mine', name=(title or 'My plugin') + ' theme', base='dark', accent='#5b8def', colors=dict(bg='#10131a', pn='#1a1f2b'))])
        (d / 'plugin.json').write_text(json.dumps(man, indent=2), 'utf-8')
        return d.name


MANAGER = PluginManager()  # the one instance shared by the window and the explorer
