# PROTOCOLO P-CHOQUE-1 — ¿a cuántas preguntas reales afecta el fallo #4509 de lm-evaluation-harness?

Registrado el 2026-11-21, antes de escribir código y antes de descargar o mirar ningún dato del examen. Contexto y decisión en `RONDA_LLM.md`.

## 1. El fallo (ya avisado por otro; no es hallazgo nuestro)
En `lm_eval/filters/extraction.py`, commit `d6de81643928d653435c431bae19945d41d32520`, `MultiChoiceRegexFilter` limpia el texto de cada opción (minúsculas y quitar puntuación, según la configuración) y guarda una sola letra por texto limpio. Si dos opciones quedan iguales al limpiarlas («5» y «−5»), la última pisa a las anteriores. Solo actúa cuando la respuesta del modelo no trae la letra en el formato esperado y el corrector busca el texto de la opción.

El autor del aviso dice que no ha contado cuántas preguntas reales lo sufren. Eso es lo que se mide aquí.

## 2. Pregunta
En MMLU, ¿cuántas preguntas tienen opciones que chocan, en cuántas la respuesta correcta está dentro del choque, y cuál es el techo del efecto sobre la nota?

## 3. Alcance
- **Etapa única, sin modelo:** recuento sobre `cais/mmlu`, las 57 materias. Partición principal: `test`. `validation` y `dev` se informan aparte.
- **Configuración:** la del filtro `flexible-extract` de las tareas `mmlu/flan_*` en el commit fijado. Antes de contar se anota de los archivos de tarea qué opciones de limpieza lleva cada una (mayúsculas, puntuación, expresiones a ignorar) y si usa el filtro compartido o una copia local. Si las copias locales difieren, se cuentan por separado.
- **Fuera:** GPQA (acceso restringido) y BBH (copias locales); solo se anotan como pendientes. Ningún modelo. Ninguna nota publicada se recalcula.

## 4. Definiciones (fijadas ahora)
- **Choque:** dos o más opciones de una pregunta con textos originales distintos y el mismo texto limpio.
- **Duplicado exacto:** opciones con el mismo texto original. Se cuenta aparte; no es este fallo.
- **Pregunta expuesta:** la respuesta correcta pertenece a un grupo que choca.
  - **Tipo A:** la correcta no es la última del grupo → una respuesta literal correcta se puntúa mal.
  - **Tipo B:** la correcta es la última del grupo → una respuesta literal equivocada (otra del grupo) se puntúa bien.
- **Techo por materia:** preguntas expuestas / preguntas de la materia. Es lo máximo que el fallo puede mover la nota de esa materia, y solo si el modelo contesta siempre con el texto y nunca con la letra.
- Segundo recuento, informativo: opciones cuyo texto limpio está contenido en otra (parentesco con #3884 y #4230). No entra en el veredicto.

## 5. Controles
1. **Filtro real:** se ejecuta el código fijado, sin tocar, sobre respuestas construidas («The answer is <texto de la opción>.») para cada opción de cada pregunta con choque. Debe reproducir el tipo A y el tipo B que predice el recuento.
2. **Control negativo:** lo mismo sobre 500 preguntas sin choque elegidas al azar (semilla 20261121). Se informa de cuántas letras salen bien; las que no, se clasifican (no se esconden).
3. **Ejemplo conocido:** matemáticas de instituto, `validation`, fila 8 (opciones 2, −4, 6, −2) debe salir como choque de tipo B.
4. **Auditoría independiente:** otro guion, con lector y limpieza propios y sin importar el del estudio, repite los recuentos. Deben coincidir pregunta a pregunta.

## 6. Veredicto (fijado ahora, sobre `test`)
- **«dormido»:** ninguna pregunta expuesta.
- **«alcanzable, techo bajo»:** hay al menos una expuesta, y el techo es menor de 1 punto porcentual en todas las materias y en el total.
- **«puede importar»:** alguna materia tiene un techo de 1 punto o más. No demuestra que una nota publicada cambie: solo que haría falta una segunda etapa con respuestas reales de modelos, con protocolo propio.
- **«no evaluable»:** falla el control 1 o el 3, o la auditoría no coincide.

## 7. Mi predicción
- Preguntas con choque en `test` (14 042): entre 20 y 200. Casi todas en materias de números y química.
- Expuestas en el total: menos del 0,5 %.
- «dormido» 5 %, «alcanzable, techo bajo» 55 %, «puede importar» 40 % (por alguna materia de matemáticas).

## 8. Qué se entrega
- Tabla por materia: preguntas, con choque, expuestas A y B, techo.
- Lista de las preguntas afectadas (materia, partición, fila), para que los mantenedores la usen de prueba.
- Si procede, un comentario para la incidencia #4509. **No se envía sin permiso de Eli.**

## 9. Límites conocidos de antemano
- Es un techo, no un efecto: cuánto se alcanza depende de cuántas veces el modelo contesta con el texto en vez de con la letra, y eso no se mide.
- Un examen, una versión del código.
- El mecanismo y la corrección son de otros; aquí solo se cuenta.
- Un autor, una corrida.

## 9 bis. Enmienda del 2026-11-21, antes del código y antes de abrir el examen
Leídas las configuraciones del commit fijado (lo que pedía el apartado 3):
- `mmlu_flan_n_shot_generative_*`: usa el filtro compartido, mayúsculas y puntuación ignoradas, `group_select: 0`, partición **test**.
- `mmlu_flan_cot_zeroshot_*`: usa el filtro compartido, mismas opciones, `group_select: -1`. No declara partición de test, así que se evalúa en **validation** (1 531 preguntas). El ejemplo del aviso sale de ahí.
- `mmlu_flan_cot_fewshot_*`: no usa este filtro. Fuera.
- Existen `utils.py` locales en esas carpetas, pero las plantillas llaman al filtro registrado (`multi_choice_regex`), no a la copia.

Consecuencias:
1. El veredicto del apartado 6 se da para la tarea generativa (test), como estaba. Se da además, con las mismas reglas y etiquetado aparte, para la tarea de razonamiento paso a paso (validation). Si difieren, se informan los dos; ninguno sustituye al otro.
2. En el control 1 las respuestas construidas son dos por opción: la frase «The answer is <texto>.» y el texto solo. Cada una se pasa con `group_select` 0 y −1.
3. El filtro real se carga desde su archivo sin instalar el paquete: se le dan dos módulos de relleno para sus dos importaciones (`Filter` y `register_filter`), sin tocar una línea del archivo. La imagen de Docker es `pchoque:env` (Python 3.12, pyarrow 17), porque `pfuera:env` no lee parquet.
4. El techo se calcula por materia sobre la partición que evalúa cada tarea.

## 10. Medios
Docker (`pfuera:env` o una imagen mínima de Python), descarga solo de `cais/mmlu` (decenas de MB) a `ext/mmlu/`, y `extraction.py` del commit fijado con su sha256 en la configuración congelada.
