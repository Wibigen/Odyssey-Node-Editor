#!/usr/bin/env python3
"""Builds functions.json (the function catalog of the Dear ImGui plugin) from imgui.h.

    python gen_catalog.py [path/to/imgui.h] [path/to/functions.json]

Defaults: ../base/imgui/imgui.h  ->  ../functions.json
Reads the public API of ImGui:: (IMGUI_API declarations with their section comments and default values), the
public methods of ImDrawList (kind "m", first input = the draw list) and the enums (kind "c", constants).
Dear ImGui is MIT licensed (c) Omar Cornut - https://github.com/ocornut/imgui
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'base' / 'imgui' / 'imgui.h'
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE.parent / 'functions.json'

SKIP = {'CreateContext', 'DestroyContext', 'GetCurrentContext', 'SetCurrentContext', 'NewFrame', 'EndFrame', 'Render', 'GetDrawData', 'SetAllocatorFunctions', 'GetAllocatorFunctions',
        'MemAlloc', 'MemFree', 'DebugCheckVersionAndDataLayout', 'LoadIniSettingsFromDisk', 'LoadIniSettingsFromMemory', 'SaveIniSettingsToDisk', 'SaveIniSettingsToMemory',
        'GetPlatformIO', 'UpdatePlatformWindows', 'RenderPlatformWindowsDefault', 'DestroyPlatformWindows', 'FindViewportByID', 'FindViewportByPlatformHandle', 'GetMainViewport',
        'SetClipboardText', 'GetClipboardText'}
SKIP_DL = {'CloneOutput', 'AddCallback', 'AddDrawCmd', 'ChannelsSplit', 'ChannelsMerge', 'ChannelsSetCurrent', 'GetClipRectMin', 'GetClipRectMax'}


def split_top(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '(<[': depth += 1
        elif ch in ')>]': depth -= 1
        if ch == ',' and depth == 0: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out


def clean_type(t):
    t = t.strip()
    t = re.sub(r'\bconst\s+(Im\w+)\s*&', r'\1', t)       # const ImVec2&  -> ImVec2
    t = re.sub(r'\b(Im\w+)\s*&', r'\1*', t) if not t.startswith('const') and False else t
    t = re.sub(r'\s+', ' ', t).replace(' *', '*').replace(' &', '&')
    return t


def parse_param(p):
    """-> [type, name, default] or None for '...'"""
    if p == '...': return None
    dflt = ''
    if '=' in p:
        p, dflt = p.split('=', 1); p, dflt = p.strip(), dflt.strip()
    m = re.match(r'^(.*?\(\s*\*\s*(\w+)\s*\)\s*\(.*\))$', p)        # function pointer
    if m: return [re.sub(r'\(\s*\*\s*\w+\s*\)', '(*)', p), m[2], dflt]
    m = re.match(r'^(.*?)(\w+)\s*(\[[^\]]*\])?$', p.strip())
    if not m: return [p.strip(), '', dflt]
    t, n, arr = m[1].strip(), m[2], m[3]
    if arr: t += '*'
    if not t:   # a lone type without a name (e.g. "void")
        return [n, '', dflt]
    return [clean_type(t), n, dflt]


def parse_decl(text):
    """'bool Begin(const char* name, bool* p_open = NULL, ImGuiWindowFlags flags = 0)' -> (ret, name, params, variadic)"""
    text = re.sub(r'IM_FMT(ARGS|LIST)\(\d+\)', '', text)
    m = re.match(r'^(.*?)\b(\w+)\s*\((.*)\)\s*(const)?\s*$', text.strip())
    if not m: return None
    ret, name, args = clean_ret(m[1]), m[2], m[3].strip()
    ps, va = [], False
    for p in split_top(args):
        if p == 'void' and len(split_top(args)) == 1: continue
        r = parse_param(p)
        if r is None: va = True
        else: ps.append(r)
    return ret, name, ps, va


def clean_ret(r):
    r = re.sub(r'\b(inline|static|IMGUI_API)\b', '', r)
    return re.sub(r'\s+', ' ', r).replace(' *', '*').replace(' &', '&').strip()


def category_of(line):
    t = line.strip()[2:].strip()
    t = re.split(r'\s+-\s+|\s*\(|\s*\[', t)[0].strip(' .:')
    return t


def ids(entries):
    seen = {}
    for e in entries:
        base = e['id']
        if base in seen:
            seen[base] += 1
            names = [p[1] for p in e.get('p', [])]
            e['label'] = f"{e['label']} ({', '.join(names[:3])}{'…' if len(names) > 3 else ''})" if names else f"{e['label']} ({seen[base]})"
            e['id'] = f'{base}_{seen[base]}'
        else: seen[base] = 1


def main():
    lines = SRC.read_text('utf-8').split('\n')
    # ---- ImGui:: functions ----
    start = next(i for i, l in enumerate(lines) if l.startswith('namespace ImGui'))
    end = next(i for i in range(start, len(lines)) if lines[i].startswith('} // namespace ImGui'))
    cat, funcs, i = 'General', [], start + 1
    while i < end:
        l = lines[i]
        s = l.strip()
        prev_blank = lines[i - 1].strip() == '' or lines[i - 1].strip() == '{'
        if re.match(r'^    // [A-Z]', l) and prev_blank and not s.startswith('// -'):
            cat = category_of(l) or cat
        elif s.startswith('IMGUI_API'):
            full, doc = s, ''
            while ';' not in full and i + 1 < end: i += 1; full += ' ' + lines[i].strip()
            body, _, doc = full.partition(';')[0], '', full.partition(';')[2]
            doc = doc.strip().lstrip('/').strip()
            d = parse_decl(body.replace('IMGUI_API', '', 1))
            if d:
                ret, name, ps, va = d
                if name not in SKIP and not any('va_list' in p[0] for p in ps) and not any(p[0].startswith('ImGuiContext') for p in ps) and not name.startswith('_'):
                    funcs.append(dict(id=name, label=name, call=f'ImGui::{name}', kind='f', r=ret or 'void', p=ps, c=cat, d=doc, va=va))
        i += 1
    ids(funcs)
    # ---- ImDrawList methods ----
    a = next(i for i, l in enumerate(lines) if l.rstrip() == 'struct ImDrawList')
    b = next(i for i in range(a, len(lines)) if lines[i].startswith('};'))
    dl, cat = [], 'Draw list'
    for i in range(a, b):
        s = lines[i].strip()
        mm = re.match(r'^// (Primitives|Stateful path API|Advanced|Render-level|Clip|Texture)', s)
        m = re.match(r'^(IMGUI_API|inline)\s+(.*?\))\s*(const)?\s*(\{.*|;.*)?$', s)
        if m: m = re.match(r'^(IMGUI_API|inline)\s+(.*?\))\s*(const)?\s*(\{.*|;.*)?$', re.sub(r'\{.*$', '', s) if m[1] == 'inline' else s)
        if s.startswith('//') and re.match(r'^// [A-Z]', s) and not s.startswith('// -'):
            c = category_of('    ' + s)
            if c and len(c) < 40: cat = c
        if not m: continue
        text = (m[2]).strip()
        doc = ''
        if '//' in s: doc = s.split('//', 1)[1].strip()
        d = parse_decl(text)
        if not d: continue
        ret, name, ps, va = d
        if name.startswith('_') or name.startswith('Prim') or name in SKIP_DL: continue
        cat = ('Clipping & textures' if name.startswith(('Push', 'Pop')) else 'Path' if name.startswith('Path') else 'Images' if 'Image' in name else 'Polygons' if 'Poly' in name else 'Shapes & text')
        dl.append(dict(id=f'DL_{name}', label=name, call=name, kind='m', r=ret or 'void', p=ps, c='ImDrawList: ' + cat, d=doc, va=va, self='ImDrawList*'))
    ids(dl)
    # ---- enums (constants) ----
    consts, cur = [], None
    for l in lines:
        m = re.match(r'^enum (\w+?)_?\s*(?::\s*\w+)?\s*$', l)
        if m and (m[1].startswith('ImGui') or m[1].startswith('ImDraw')): cur = m[1]; continue
        if cur:
            if l.startswith('};'): cur = None; continue
            m = re.match(r'^\s+((?:ImGui|ImDraw)\w+)\s*(=|,)', l)
            if m:
                n = m[1]
                if n.endswith(('_COUNT', '_BEGIN', '_END', '_COUNT_')) or '_Obsolete' in n or 'KeysData' in n or n.endswith('_NamedKey_COUNT'): continue
                if re.search(r'_(Mask_|MaskUnused)$', n) or n.endswith('_'): continue
                tn = cur if cur != 'ImGuiKey' else 'ImGuiKey'
                doc = l.split('//', 1)[1].strip() if '//' in l else ''
                consts.append(dict(id=n, label=n, call=n, kind='c', r=tn, p=[], c='Constants: ' + tn, d=doc))
    seen = set(); consts = [c for c in consts if not (c['id'] in seen or seen.add(c['id']))]
    entries = funcs + dl + consts
    ver = re.search(r'#define IMGUI_VERSION\s+"([^"]+)"', '\n'.join(lines))
    out = dict(title='Dear ImGui', version=ver[1] if ver else '', includes=['"imgui.h"'], color='#4a8fd9', entries=entries)
    DST.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), 'utf-8')
    print(f'{len(funcs)} functions, {len(dl)} ImDrawList methods, {len(consts)} constants -> {DST}')


if __name__ == '__main__':
    main()
