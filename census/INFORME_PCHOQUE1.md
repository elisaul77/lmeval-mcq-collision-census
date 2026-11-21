# INFORME P-CHOQUE-1 — el fallo #4509 de lm-evaluation-harness toca 51 preguntas reales de MMLU; el techo es bajo en el total y pasa de un punto en once materias

2026-11-21. Protocolo `PROTOCOL_PCHOQUE1.md`, registrado antes del código; una enmienda (qué partición evalúa cada tarea) antes de abrir el examen. Una sola corrida, sin modelo. Auditoría independiente (`audit_choque1.py`): **PASA** (193 comprobaciones), a la segunda: ver apartado 4.

El fallo y su corrección son de otros (aviso #4509, corrección propuesta #4522). Aquí solo se cuenta lo que el autor del aviso dijo que no había contado.

## Veredicto registrado
- Tarea generativa (`mmlu_flan_n_shot_generative`, partición test): **«puede importar»**.
- Tarea de razonamiento paso a paso (`mmlu_flan_cot_zeroshot`, partición validation): **«puede importar»**.

«Puede importar» significa solo que el techo pasa de un punto en alguna materia. **No demuestra que ninguna nota publicada cambie.**

## 1. Medido
| | Generativa (test) | Paso a paso (validation) |
|---|---|---|
| Preguntas | 14 042 | 1 531 |
| Con opciones que chocan | 82 | 8 |
| Expuestas (la correcta está en el choque) | 51 | 7 |
| — tipo A (acierto literal puntuado como fallo) | 26 | 3 |
| — tipo B (fallo literal puntuado como acierto) | 25 | 4 |
| Techo sobre la nota total | 0,363 % | 0,457 % |
| Materias con techo ≥ 1 punto | 11 de 57 | 6 de 57 |
| Techo máximo | 3,70 % (matemáticas de instituto) | 9,09 % (matemáticas de universidad) |

Techo por materia en test (%, solo las que tienen alguna): matemáticas de instituto 3,70; lógica formal 3,17; álgebra abstracta 3,00; matemáticas elementales 2,91; datos globales 2,00; informática de instituto 2,00; estadística de instituto 1,85; ingeniería eléctrica 1,38; física de instituto 1,32; macroeconomía de instituto 1,03; química de universidad 1,00; biología de instituto 0,65; conocimiento clínico 0,38; contabilidad profesional 0,35; miscelánea 0,26.

Qué choca, en las 51 de test: 26 son números que solo difieren en el signo menos o la coma decimal («−19» y «19», «156» y «15.6»); 20, otra puntuación («1.5 KV.» y «15 KV.»); 3, solo mayúsculas; 2, opciones hechas solo de signos.

En validation las materias tienen entre 5 y 30 preguntas: el 9,09 % es una pregunta de once.

## 2. Controles
- **Filtro real sobre respuestas construidas:** en las preguntas con choque, 234 respuestas literales salen con la letra equivocada, tal como predice el recuento. 735 de 752 coinciden con lo predicho.
- Las 17 que no coinciden son tres preguntas: dos con opciones hechas solo de signos («/», «//», «**»), que al limpiarse quedan vacías y el filtro no las reconoce; y una con una opción repetida tal cual y otra entre paréntesis.
- **Ejemplo del aviso** (matemáticas de instituto, validation, fila 8): reproducido.
- **Control negativo** (500 preguntas sin choque, 2 000 opciones): el filtro acierta la letra en 1 990–1 994. Los 6–10 fallos son otras cosas, no este fallo (apartado 3).

## 3. Otros dos defectos vistos de paso (descriptivo, no registrado, no sé si están avisados)
1. **Opciones repetidas tal cual** en el propio examen («0.015 joule.» dos veces): el filtro da siempre la letra de la última. Es un defecto del dato, no del filtro.
2. **Opciones que al limpiarse empiezan o acaban en espacio** («. . . asthma.», «'Rocky '»): el filtro encuentra el texto, le quita los espacios y ya no lo reconoce como opción; devuelve el texto en vez de la letra y la respuesta cuenta como fallo. Es otro mecanismo distinto del #4509.

## 4. La auditoría falló a la primera
Mi reimplementación corta del filtro, en la auditoría, daba letra cuando el texto limpio quedaba vacío; el filtro real no. Eran 29 diferencias de 1 504, todas en las dos preguntas de signos. El error era de la auditoría, no del estudio: los recuentos coincidían pregunta a pregunta desde la primera pasada. Corregida esa línea, pasa. Lo dejo dicho porque la auditoría se tocó después de ver resultados.

## 5. Lo que queda establecido
1. El fallo no está dormido: hay 51 preguntas reales de test y 7 de validation donde una respuesta dada con el texto de la opción se puntúa al revés.
2. Va en los dos sentidos casi por igual (26 quita aciertos, 25 regala aciertos), así que en la nota total tiende a compensarse.
3. Sobre la nota total de MMLU el techo es de 0,36 puntos, y solo si el modelo contesta siempre con el texto y nunca con la letra.
4. Se concentra en materias de números. En once materias el techo pasa de un punto.
5. Mi predicción: entre 20 y 200 preguntas con choque (salieron 82) y menos del 0,5 % expuestas (0,36 %): acertó. Al veredicto que salió le daba un 40 %.

## 6. Límites
- Es un techo, no un efecto. No se ha pasado ningún modelo; no sé cuántas veces un modelo real contesta con el texto en vez de con la letra.
- Un examen (MMLU) y una versión del código (commit `d6de8164`). GPQA y BBH no se han mirado.
- No se ha comprobado qué hace la corrección propuesta (#4522) con estas 58 preguntas.
- La lista de materias con techo alto depende de pocas preguntas (3 a 10 por materia).
- Un autor, una corrida.

## 7. Borrador de comentario para la incidencia #4509 — NO ENVIADO
> I counted real exposure on `cais/mmlu` at d6de8164 (no model runs, census only).
> - `mmlu_flan_n_shot_generative` (test, 14,042 questions): 82 questions have choices that collide after normalisation; in 51 the gold answer is inside the colliding group (26 where a correct literal answer is scored wrong, 25 where a wrong literal answer is scored right).
> - `mmlu_flan_cot_zeroshot` (validation, 1,531): 8 colliding, 7 with gold inside.
> - Upper bound on aggregate accuracy: 0.36 points (test). Per subject it exceeds 1 point in 11 of 57 subjects, highest in high_school_mathematics (10 of 270, 3.7 %).
> - 26 of the 51 are numbers differing only by a minus sign or decimal point.
> - These are ceilings: they are only reached when the model answers with the choice text instead of the letter. I have not measured how often that happens.
> - Two side observations: choices that normalise to an empty string («/», «//») are never matched; choices whose normalised text has leading or trailing whitespace («. . . asthma.») are matched and then lost by the `.strip()` before the dictionary lookup.
> I can share the list of affected (subject, split, row) as regression cases.

## 8. Archivos
`results/censo.json` (incluye la lista de preguntas afectadas), `results/eval.json`, `config_frozen.json`, `choque1.py`, `audit_choque1.py`, `diag.py` (resumen descriptivo posterior), `baja.sh`, `Dockerfile`.
