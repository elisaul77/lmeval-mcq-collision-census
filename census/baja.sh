#!/bin/sh
# Descarga los archivos públicos de P-CHOQUE-1 (código fijado de lm-evaluation-harness y MMLU). Se ejecuta desde la raíz del proyecto.
set -e
C=d6de81643928d653435c431bae19945d41d32520
B=https://raw.githubusercontent.com/EleutherAI/lm-evaluation-harness/$C/lm_eval
D=ext/lmeval_d6de816
mkdir -p $D ext/mmlu
curl -sSfL -o $D/extraction.py $B/filters/extraction.py
curl -sSfL -o $D/cot_zeroshot.yaml $B/tasks/mmlu/flan_cot_zeroshot/_mmlu_flan_cot_zeroshot_template_yaml
curl -sSfL -o $D/cot_fewshot.yaml $B/tasks/mmlu/flan_cot_fewshot/_mmlu_flan_cot_fewshot_template_yaml
curl -sSfL -o $D/generative.yaml $B/tasks/mmlu/flan_n_shot/generative/_mmlu_flan_generative_template_yaml
curl -sSfL -o $D/tree.json "https://api.github.com/repos/EleutherAI/lm-evaluation-harness/git/trees/$C?recursive=1"
for s in test validation dev; do curl -sSfL -o ext/mmlu/$s.parquet https://huggingface.co/datasets/cais/mmlu/resolve/main/all/$s-00000-of-00001.parquet; done
ls -la $D ext/mmlu
