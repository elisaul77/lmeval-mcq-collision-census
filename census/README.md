# Census code (P-CHOQUE-1)

Comments and variable names are in Spanish; a glossary is at the end.

| File | Role |
|---|---|
| `PROTOCOL_PCHOQUE1.md` | Protocol and its one amendment, committed before code and data (Spanish) |
| `INFORME_PCHOQUE1.md` | Original report (Spanish) |
| `config_frozen.json` | Pinned commit, seed, SHA-256 of code, filter, YAMLs and data |
| `baja.sh` | Downloads the pinned filter, the task YAMLs and `cais/mmlu` |
| `choque1.py` | Census, controls with the real filter, verdict |
| `audit_choque1.py` | Independent audit; imports nothing from `choque1.py` or from the filter |
| `diag.py` | Descriptive summary written after the run (not part of the registered run) |
| `Dockerfile`, `run.sh` | Environment (Python 3.12, pyarrow 17) and launcher |

## Layout the scripts expect

The scripts were written inside a larger project and keep its paths. Run them from a root that looks like this:

```text
root/
├── choque/        ← the contents of this census/ folder
└── ext/
    ├── lmeval_d6de816/   (created by baja.sh)
    └── mmlu/             (created by baja.sh)
```

So, from a fresh clone: `mkdir work && cp -r census work/choque && cd work && sh choque/baja.sh && sh choque/run.sh prueba`.

The real filter is loaded from its own file without installing the package: two stub modules stand in for its two imports (`Filter`, `register_filter`). Not one line of the filter is modified.

## Glossary

| Spanish | English |
|---|---|
| `choque` | collision |
| `expuesta` | exposed (gold answer inside a colliding group) |
| `tipo A` | a correct literal answer is scored wrong |
| `tipo B` | a wrong literal answer is scored right |
| `techo` | ceiling (upper bound on the accuracy shift) |
| `materia` | subject |
| `parte` | split |
| `generativa` / `paso_a_paso` | the generative task / the zero-shot chain-of-thought task |
| `dormido` / `alcanzable, techo bajo` / `puede importar` | verdicts: dormant / reachable with a low ceiling / may matter |
