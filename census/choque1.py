"""P-CHOQUE-1: recuento de preguntas de MMLU expuestas al fallo #4509 de lm-evaluation-harness. Protocolo: PROTOCOL_PCHOQUE1.md."""
import os, sys, json, hashlib, types, importlib.util, random, unicodedata, collections
import pyarrow.parquet as pq
AQUI = os.path.dirname(os.path.abspath(__file__)); EXT = os.path.join(AQUI, '..', 'ext'); FILTRO = os.path.join(EXT, 'lmeval_d6de816', 'extraction.py'); RES = os.path.join(AQUI, 'results')
PARTES = ('test', 'validation', 'dev'); TAREAS = {'generativa': ('test', 0), 'paso_a_paso': ('validation', -1)}; SEMILLA = 20261121; LETRAS = 'ABCD'
PUNT = dict.fromkeys(i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith('P'))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def limpia(s): return s.strip().lower().translate(PUNT)
def lee(parte): return pq.read_table(os.path.join(EXT, 'mmlu', parte + '.parquet')).to_pylist()

def carga_filtro():
    """Carga el archivo del filtro tal cual, con dos módulos de relleno para sus importaciones."""
    class Filter:
        def __init__(self, **kw): pass
    for n, d in (('lm_eval', {}), ('lm_eval.api', {}), ('lm_eval.api.filter', {'Filter': Filter}), ('lm_eval.api.registry', {'register_filter': lambda nombre: (lambda c: c)})):
        m = types.ModuleType(n); m.__dict__.update(d); sys.modules[n] = m
    sp = importlib.util.spec_from_file_location('extraction_fijado', FILTRO); mod = importlib.util.module_from_spec(sp); sp.loader.exec_module(mod); return mod.MultiChoiceRegexFilter

def analiza(ch, gold):
    """Devuelve (grupos que chocan, duplicados exactos, tipo de exposición o None, pares contenidos)."""
    g = collections.defaultdict(list)
    for i, c in enumerate(ch): g[limpia(c)].append(i)
    choques = [ix for ix in g.values() if len({ch[i].strip() for i in ix}) > 1]; dup = [ix for ix in g.values() if len(ix) > 1 and len({ch[i].strip() for i in ix}) == 1]
    tipo = None
    for ix in choques:
        if gold in ix: tipo = 'A' if gold != ix[-1] else 'B'
    L = [limpia(c) for c in ch]; cont = sum(1 for i in range(len(L)) for j in range(len(L)) if i != j and L[i] and L[i] != L[j] and L[i] in L[j])
    return choques, dup, tipo, cont

def pasa_filtro(F, gs, ch, resp):
    f = F(regex_pattern=r'(\([A-Z]\))', group_select=gs, ignore_case=True, ignore_punctuation=True); return f.apply([[resp]], [{'choices': ch}])[0][0]

def censo():
    os.makedirs(RES, exist_ok=True); F = carga_filtro(); out = {'partes': {}, 'afectadas': [], 'control1': [], 'control2': {}}
    for parte in PARTES:
        D = lee(parte); por = collections.defaultdict(lambda: dict(n=0, choque=0, A=0, B=0, dup=0, contenida=0)); fila = collections.Counter()
        for d in D:
            s = d['subject']; i = fila[s]; fila[s] += 1; q = por[s]; q['n'] += 1; ch = list(d['choices']); gold = int(d['answer']); cq, dup, tipo, cont = analiza(ch, gold)
            q['dup'] += bool(dup); q['contenida'] += bool(cont)
            if cq:
                q['choque'] += 1
                if tipo: q[tipo] += 1
                out['afectadas'].append(dict(parte=parte, materia=s, fila=i, opciones=ch, correcta=gold, grupos=cq, tipo=tipo))
        out['partes'][parte] = {s: por[s] for s in sorted(por)}
    # control 1: filtro real sobre respuestas construidas, en cada pregunta con choque
    for a in out['afectadas']:
        ch = a['opciones']
        for k, c in enumerate(ch):
            for forma, resp in (('frase', f'The answer is {c}.'), ('texto', c)):
                for gs in (0, -1): out['control1'].append(dict(parte=a['parte'], materia=a['materia'], fila=a['fila'], opcion=k, forma=forma, gs=gs, sale=pasa_filtro(F, gs, ch, resp), en_choque=any(k in g for g in a['grupos'])))
    # control 2: 500 preguntas sin choque al azar, por tarea
    for tarea, (parte, gs) in TAREAS.items():
        D = lee(parte); lim = [d for d in D if not analiza(list(d['choices']), int(d['answer']))[0]]; rnd = random.Random(SEMILLA); M = rnd.sample(lim, min(500, len(lim))); r = {}
        for forma in ('frase', 'texto'):
            bien = mal = 0; ej = []
            for d in M:
                ch = list(d['choices'])
                for k, c in enumerate(ch):
                    s = pasa_filtro(F, gs, ch, f'The answer is {c}.' if forma == 'frase' else c)
                    if s == f'({LETRAS[k]})': bien += 1
                    else:
                        mal += 1
                        if len(ej) < 40: ej.append(dict(materia=d['subject'], opciones=ch, opcion=k, sale=s))
            r[forma] = dict(bien=bien, mal=mal, ejemplos=ej)
        out['control2'][tarea] = dict(preguntas=len(M), **r)
    json.dump(out, open(os.path.join(RES, 'censo.json'), 'w'), ensure_ascii=False, indent=1); print('censo guardado:', len(out['afectadas']), 'preguntas con choque')

def veredicto(por):
    exp = {s: q['A'] + q['B'] for s, q in por.items()}; N = sum(q['n'] for q in por.values()); E = sum(exp.values()); techo = {s: 100.0 * exp[s] / por[s]['n'] for s in por}; tt = 100.0 * E / N; mx = max(techo.values())
    v = 'dormido' if E == 0 else 'puede importar' if mx >= 1.0 else 'alcanzable, techo bajo'
    return dict(n=N, con_choque=sum(q['choque'] for q in por.values()), expuestas=E, A=sum(q['A'] for q in por.values()), B=sum(q['B'] for q in por.values()), techo_total=tt, techo_max=mx, materia_max=max(techo, key=techo.get), techo_por_materia={s: t for s, t in techo.items() if t > 0}, veredicto=v)

def evalua():
    C = json.load(open(os.path.join(RES, 'censo.json'))); R = {'tareas': {}}
    # control 1: en cada grupo que choca, las opciones no últimas deben salir con la letra de la última (el fallo); las demás, con la suya
    fallo = ok1 = otro = 0; idx = {(a['parte'], a['materia'], a['fila']): a for a in C['afectadas']}
    for c in C['control1']:
        if c['forma'] != 'texto': continue
        a = idx[(c['parte'], c['materia'], c['fila'])]; g = next((g for g in a['grupos'] if c['opcion'] in g), None); espera = f"({LETRAS[g[-1]]})" if g else f"({LETRAS[c['opcion']]})"
        if c['sale'] == espera: ok1 += 1; fallo += bool(g and c['opcion'] != g[-1])
        else: otro += 1
    R['control1'] = dict(coinciden_con_lo_predicho=ok1, respuestas_mal_puntuadas_por_el_choque=fallo, no_coinciden=otro)
    e = idx.get(('validation', 'high_school_mathematics', 8)); R['control3'] = bool(e and e['tipo'] == 'B' and [o.strip() for o in e['opciones']] == ['2', '-4', '6', '-2'])
    R['control2'] = {t: {f: {k: v[f][k] for k in ('bien', 'mal')} for f in ('frase', 'texto')} for t, v in C['control2'].items()}
    valido = R['control3'] and fallo > 0
    for t, (parte, gs) in TAREAS.items():
        q = veredicto(C['partes'][parte]); q['parte'] = parte; q['group_select'] = gs
        if not valido: q['veredicto'] = 'no evaluable'
        R['tareas'][t] = q
    R['dev'] = veredicto(C['partes']['dev'])
    json.dump(R, open(os.path.join(RES, 'eval.json'), 'w'), ensure_ascii=False, indent=1)
    for t, q in R['tareas'].items(): print(f"{t} ({q['parte']}): {q['n']} preguntas | con choque {q['con_choque']} | expuestas {q['expuestas']} (A {q['A']}, B {q['B']}) | techo total {q['techo_total']:.3f} % | máximo {q['techo_max']:.2f} % en {q['materia_max']} | {q['veredicto']}")
    print('control 1:', R['control1'], '| control 3:', R['control3']); print('control 2:', R['control2'])

def prueba():
    """Pruebas con datos inventados; no abre el examen."""
    F = carga_filtro()
    assert analiza(['-5', '5', '10', '-10'], 0)[2] == 'A' and analiza(['-5', '5', '10', '-10'], 1)[2] == 'B' and analiza(['-5', '5', '10', '-10'], 2)[2] == 'A' and analiza(['-5', '5', '7', '8'], 2)[2] is None
    assert analiza(['a', 'a', 'b', 'c'], 0)[0] == [] and len(analiza(['a', 'a', 'b', 'c'], 0)[1]) == 1
    assert len(analiza(['Na', 'NA', 'K', 'Li'], 0)[0]) == 1 and analiza(['uno', 'dos', 'tres', 'cuatro'], 0)[0] == []
    assert pasa_filtro(F, -1, ['-5', '5', '10', '-10'], 'So x = -5.') == '(B)' and pasa_filtro(F, -1, ['Na', 'NA', 'K', 'Li'], 'The element is Na') == '(B)'
    assert pasa_filtro(F, 0, ['uno', 'dos', 'tres', 'cuatro'], 'tres') == '(C)' and pasa_filtro(F, 0, ['uno', 'dos', 'tres', 'cuatro'], 'creo que (D)') == '(D)'
    v = veredicto({'m': dict(n=100, choque=2, A=1, B=0, dup=0, contenida=0), 'k': dict(n=1000, choque=0, A=0, B=0, dup=0, contenida=0)}); assert v['veredicto'] == 'puede importar' and abs(v['techo_max'] - 1.0) < 1e-12
    assert veredicto({'m': dict(n=101, choque=2, A=1, B=0, dup=0, contenida=0)})['veredicto'] == 'alcanzable, techo bajo' and veredicto({'m': dict(n=5, choque=1, A=0, B=0, dup=0, contenida=0)})['veredicto'] == 'dormido'
    print('pruebas inventadas: bien')

def congela():
    f = {'commit': 'd6de81643928d653435c431bae19945d41d32520', 'semilla': SEMILLA, 'tareas': TAREAS, 'hashes': {'choque1.py': sha(os.path.abspath(__file__)), 'extraction.py': sha(FILTRO), **{p + '.parquet': sha(os.path.join(EXT, 'mmlu', p + '.parquet')) for p in PARTES}, **{y: sha(os.path.join(EXT, 'lmeval_d6de816', y)) for y in ('cot_zeroshot.yaml', 'generative.yaml', 'cot_fewshot.yaml')}}}
    json.dump(f, open(os.path.join(AQUI, 'config_frozen.json'), 'w'), indent=1); print('congelado')

if __name__ == '__main__':
    o = sys.argv[1] if len(sys.argv) > 1 else 'prueba'
    if o == 'censo':
        Fz = json.load(open(os.path.join(AQUI, 'config_frozen.json'))); assert Fz['hashes']['choque1.py'] == sha(os.path.abspath(__file__)), 'el código cambió tras congelar'; assert not os.path.exists(os.path.join(RES, 'censo.json')), 'ya hay una corrida'
    {'prueba': prueba, 'congela': congela, 'censo': censo, 'evalua': evalua}[o]()
