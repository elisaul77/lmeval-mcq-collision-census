"""Diagnóstico posterior (no forma parte de la corrida registrada): resumen descriptivo de las preguntas afectadas."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_choque1 import norma
A = os.path.dirname(os.path.abspath(__file__)); C = json.load(open(os.path.join(A, 'results', 'censo.json'))); E = json.load(open(os.path.join(A, 'results', 'eval.json')))
for t, q in E['tareas'].items():
    print(t, {k: round(v, 2) for k, v in sorted(q['techo_por_materia'].items(), key=lambda x: -x[1])})
for parte in ('test', 'validation'):
    X = [a for a in C['afectadas'] if a['parte'] == parte and a['tipo']]; vac = [a for a in X if any(a['correcta'] in g and norma(a['opciones'][g[0]]) == '' for g in a['grupos'])]
    clase = collections.Counter()
    for a in X:
        g = next(g for g in a['grupos'] if a['correcta'] in g); o = [a['opciones'][i].strip() for i in g]; k = norma(o[0])
        clase['vacío (solo signos)' if k == '' else 'signo menos o decimal en números' if k.replace(' ', '').isdigit() else 'solo mayúsculas' if len({x.lower() for x in o}) == 1 else 'otra puntuación'] += 1
    print(parte, 'expuestas', len(X), '| con texto limpio vacío', len(vac), '| clases', dict(clase))
    for a in X[:6]: print('   ', a['materia'], a['fila'], a['opciones'], 'correcta', a['correcta'], a['tipo'])
print('dev:', E['dev']['con_choque'], 'con choque,', E['dev']['expuestas'], 'expuestas')
c2 = C['control2']
for t in c2:
    print(t, 'control 2, ejemplos de fallo sin choque:')
    for e in c2[t]['texto']['ejemplos'][:7]: print('   ', e['materia'], e['opciones'], 'opción', e['opcion'], '→', e['sale'])
