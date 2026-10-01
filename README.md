# Prompt Chaining Task

This project implements the 3-step prompt chain from the training task.

## Structure

- `prompts/extract.txt` — Step 1: free text -> structured JSON
- `prompts/generate.txt` — Step 2: attributes -> 3 ad variants
- `prompts/select.txt` — Step 3: variants + brand rules -> winner
- `pipeline.py` — runs Step 1 -> Step 2 -> Step 3
- `brand_rules.md` — rules used by Step 3
- `briefs/` — 5 fictional product briefs
- `runs/` — generated outputs for each brief
- `learning_notes.md` — reflection on errors and task chaining

## Run

This version uses Ollama locally.

1. Start Ollama.
2. Make sure a model is installed, for example:
   `ollama pull gemma3:4b`
3. From this folder run:
   `python3 pipeline.py`

If your model has a different name:
`OLLAMA_MODEL=your-model-name python3 pipeline.py`

The pipeline saves:
- `input_brief.txt`
- `step1_attributes.json`
- `step2_variants.json`
- `step3_winner.json`

for each brief under `runs/`.
