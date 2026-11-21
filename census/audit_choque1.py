"""Auditoría independiente de P-CHOQUE-1. No importa el código del estudio ni el filtro: lector, limpieza y recuento propios."""
import os, json, hashlib, re, unicodedata
import pyarrow.parquet as pq
AQUI = os.path.dirname(os.path.abspath(__file__)); EXT = os.path.join(AQUI, '..', 'ext'); N = [0]; FALLOS = []
def ok(c, msg):
    N[0] += 1
    if not c: FALLOS.append(msg); print('  FALLA:', msg)
def h(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def norma(s):
    # limpieza escrita de otra manera: carácter a carácter, por categoría Unicode
    return ''.join(c for c in s.strip().lower() if not unicodedata.category(c).startswith('P'))
def mini_filtro(ch, resp, gs):
    """Reimplementación corta del comportamiento descrito en el aviso #4509 (una letra por texto limpio, gana la última)."""
    m = re.findall(r'(\([A-Z]\))', resp)
    if m: return m[gs]
    d = {}; pats = []
    for i, c in enumerate(ch): k = norma(c); d[k] = f'({"ABCDEFGH"[i]})'; pats.append(re.escape(k))
    m = re.findall('|'.join(sorted(pats, key=len, reverse=True)), norma(resp))
    if m and m[gs].strip():  # corregido tras la primera pasada: un texto limpio vacío (opciones hechas solo de signos) no cuenta como acierto en el filtro real y sigue al paso siguiente
        x = m[gs].strip(); return d.get(x, x)
    m = re.findall(r':[\s]*(' + '|'.join('ABCDEFGH'[:len(ch)]) + ')', resp)
    return f'({m[gs]})' if m else '[invalid]'

if __name__ == '__main__':
    Fz = json.load(open(os.path.join(AQUI, 'config_frozen.json'))); C = json.load(open(os.path.join(AQUI, 'results', 'censo.json'))); E = json.load(open(os.path.join(AQUI, 'results', 'eval.json')))
    ok(h(os.path.join(AQUI, 'choque1.py')) == Fz['hashes']['choque1.py'], 'hash del código'); ok(h(os.path.join(EXT, 'lmeval_d6de816', 'extraction.py')) == Fz['hashes']['extraction.py'], 'hash del filtro')
    src = open(os.path.join(EXT, 'lmeval_d6de816', 'extraction.py')).read(); ok('choice_to_alpha[m] = f"({next_alpha})"' in src, 'la línea del fallo está en el archivo fijado')
    for y, claves in (('generative.yaml', ('group_select: 0', 'ignore_case: true', 'ignore_punctuation: true', 'test_split: test', 'multi_choice_regex')), ('cot_zeroshot.yaml', ('group_select: -1', 'ignore_case: true', 'ignore_punctuation: true', 'validation_split: validation', 'multi_choice_regex'))):
        t = open(os.path.join(EXT, 'lmeval_d6de816', y)).read(); ok(h(os.path.join(EXT, 'lmeval_d6de816', y)) == Fz['hashes'][y] and all(k in t for k in claves), f'{y}: configuración');
    ok('test_split' not in open(os.path.join(EXT, 'lmeval_d6de816', 'cot_zeroshot.yaml')).read(), 'paso a paso no declara test'); ok('multi_choice_regex' not in open(os.path.join(EXT, 'lmeval_d6de816', 'cot_fewshot.yaml')).read(), 'la tarea con ejemplos no usa el filtro')
    mias = {}; tot = {}
    for parte in ('test', 'validation', 'dev'):
        p = os.path.join(EXT, 'mmlu', parte + '.parquet'); ok(h(p) == Fz['hashes'][parte + '.parquet'], f'{parte}: hash'); T = pq.read_table(p).to_pydict(); cnt = {}; pos = {}
        for s, ch, a in zip(T['subject'], T['choices'], T['answer']):
            i = pos.get(s, 0); pos[s] = i + 1; q = cnt.setdefault(s, [0, 0, 0, 0]); q[0] += 1; nn = [norma(c) for c in ch]; tipo = None; choca = False
            for k in set(nn):
                ix = [j for j in range(len(ch)) if nn[j] == k]
                if len(ix) > 1 and len(set(ch[j].strip() for j in ix)) > 1:
                    choca = True
                    if a in ix: tipo = 'A' if a != max(ix) else 'B'
            if choca: q[1] += 1; mias[(parte, s, i)] = tipo; q[2] += tipo == 'A'; q[3] += tipo == 'B'
        tot[parte] = cnt; ok(set(cnt) == set(C['partes'][parte]) and len(cnt) == 57, f'{parte}: 57 materias')
        for s, q in cnt.items(): z = C['partes'][parte][s]; ok([z['n'], z['choque'], z['A'], z['B']] == q, f'{parte}/{s}: recuento')
    suyas = {(a['parte'], a['materia'], a['fila']): a['tipo'] for a in C['afectadas']}; ok(suyas == mias, 'las preguntas afectadas coinciden una a una'); ok(len(pq.read_table(os.path.join(EXT, 'mmlu', 'test.parquet'))) == 14042, 'test tiene 14 042 preguntas')
    for t, parte in (('generativa', 'test'), ('paso_a_paso', 'validation')):
        cnt = tot[parte]; z = E['tareas'][t]; n = sum(q[0] for q in cnt.values()); e = sum(q[2] + q[3] for q in cnt.values()); techo = {s: 100.0 * (q[2] + q[3]) / q[0] for s, q in cnt.items()}; mx = max(techo.values()); v = 'dormido' if e == 0 else 'puede importar' if mx >= 1.0 else 'alcanzable, techo bajo'
        ok(z['n'] == n and z['expuestas'] == e and z['con_choque'] == sum(q[1] for q in cnt.values()) and abs(z['techo_max'] - mx) < 1e-9 and abs(z['techo_total'] - 100.0 * e / n) < 1e-9, f'{t}: cifras'); ok(E['control3'] and E['control1']['respuestas_mal_puntuadas_por_el_choque'] > 0 and z['veredicto'] == v, f'{t}: veredicto'); print(f'{t}: veredicto recalculado «{v}» | expuestas {e} de {n} | techo máximo {mx:.2f} %')
    # las salidas guardadas del filtro real, contra la reimplementación corta
    idx = {(a['parte'], a['materia'], a['fila']): a for a in C['afectadas']}; dif = 0
    for c in C['control1']:
        a = idx[(c['parte'], c['materia'], c['fila'])]; ch = a['opciones']; resp = f"The answer is {ch[c['opcion']]}." if c['forma'] == 'frase' else ch[c['opcion']]; dif += mini_filtro(ch, resp, c['gs']) != c['sale']
    ok(dif == 0, f'control 1: la reimplementación coincide con el filtro real ({dif} diferencias de {len(C["control1"])})')
    e = idx.get(('validation', 'high_school_mathematics', 8)); ok(e is not None and e['tipo'] == 'B', 'ejemplo del aviso'); ok(mini_filtro(['2', '-4', '6', '-2'], 'The result is 2.', -1) == '(D)', 'ejemplo del aviso con la reimplementación')
    print(f'{N[0]} comprobaciones, {len(FALLOS)} fallos →', 'PASA' if not FALLOS else 'NO PASA')
