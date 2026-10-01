import json
import os
from pathlib import Path
from urllib import request


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PROMPTS = BASE_DIR / "prompts"
BRIEFS = BASE_DIR / "briefs"
RUNS = BASE_DIR / "runs"


# ============================================================
# OLLAMA SETTINGS
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


# ============================================================
# FILE HELPERS
# ============================================================

def read_text(path):
    return path.read_text(encoding="utf-8")


def render(template, **values):
    result = template

    for key, value in values.items():
        result = result.replace("{{" + key + "}}", value)

    return result


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(text):
    """
    Extract JSON from the model response.
    Handles responses containing markdown fences.
    """

    text = text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # First try the complete response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting the first JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from model response.")


# ============================================================
# OLLAMA CALL
# ============================================================

def call_ollama(prompt):
    """
    Send a prompt to the local Ollama server.
    """

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1
        }
    }

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["message"]["content"]


# ============================================================
# STEP 1 VALIDATION
# ============================================================

def validate_attributes(attributes):
    """
    Validate the structured product attributes.
    """

    if not isinstance(attributes, dict):
        return "Step 1 output must be a JSON object."

    required_keys = {
        "product_name",
        "category",
        "key_features",
        "target_audience"
    }

    actual_keys = set(attributes.keys())

    missing = required_keys - actual_keys

    if missing:
        return (
            "Step 1 is missing required fields: "
            + ", ".join(sorted(missing))
        )

    product_name = attributes["product_name"]
    category = attributes["category"]
    key_features = attributes["key_features"]
    target_audience = attributes["target_audience"]

    if not isinstance(product_name, str) or not product_name.strip():
        return "Step 1 product_name is empty."

    if not isinstance(category, str) or not category.strip():
        return (
            "Step 1 category is empty. "
            "The product category must be extracted from the product brief."
        )

    if not isinstance(key_features, list):
        return "Step 1 key_features must be a list."

    if len(key_features) == 0:
        return "Step 1 key_features cannot be empty."

    for feature in key_features:
        if not isinstance(feature, str) or not feature.strip():
            return "Step 1 contains an empty key feature."

    if not isinstance(target_audience, str) or not target_audience.strip():
        return "Step 1 target_audience is empty."

    return None


# ============================================================
# STEP 2 VALIDATION
# ============================================================

def validate_variants(variants):
    """
    Validate the three generated advertising variants.
    """

    if not isinstance(variants, dict):
        return "Step 2 output must be a JSON object."

    if "variants" not in variants:
        return "Step 2 output must contain a 'variants' field."

    items = variants["variants"]

    if not isinstance(items, list):
        return "Step 2 'variants' must be a list."

    if len(items) != 3:
        return (
            f"Step 2 must contain exactly 3 variants, "
            f"found {len(items)}."
        )

    expected_ids = {1, 2, 3}
    actual_ids = set()

    forbidden_words = [
        "ultimate",
        "innovative",
        "revolutionary",
        "number one",
        "best",
        "perfect",
        "most powerful",
        "premium",
        "guaranteed",
        "guarantee"
    ]

    for item in items:

        if not isinstance(item, dict):
            return "Each variant must be a JSON object."

        if "id" not in item:
            return "Each variant must contain an 'id'."

        if "copy" not in item:
            return "Each variant must contain a 'copy'."

        variant_id = item["id"]

        if variant_id not in expected_ids:
            return f"Invalid variant id: {variant_id}"

        actual_ids.add(variant_id)

        copy = item["copy"]

        if not isinstance(copy, str):
            return (
                f"Variant {variant_id} copy must be a string."
            )

        if not copy.strip():
            return (
                f"Variant {variant_id} copy is empty."
            )

        lower_copy = copy.lower()

        for word in forbidden_words:

            if word in lower_copy:
                return (
                    f"Step 2 variant {variant_id} contains "
                    f"unsupported marketing language: '{word}'."
                )

    if actual_ids != expected_ids:
        return (
            "Variant IDs must be exactly 1, 2, and 3. "
            f"Found: {sorted(actual_ids)}"
        )

    return None


# ============================================================
# STEP 3 VALIDATION
# ============================================================

def validate_selection(selection):
    """
    Validate the selected winning variant.
    """

    if not isinstance(selection, dict):
        return "Step 3 output must be a JSON object."

    required_keys = {
        "winner_id",
        "reason",
        "selected_copy"
    }

    missing = required_keys - set(selection.keys())

    if missing:
        return (
            "Step 3 is missing required fields: "
            + ", ".join(sorted(missing))
        )

    winner_id = selection["winner_id"]

    if winner_id not in {1, 2, 3}:
        return (
            f"Step 3 winner_id must be 1, 2, or 3. "
            f"Found: {winner_id}"
        )

    if not isinstance(selection["reason"], str):
        return "Step 3 reason must be a string."

    if not selection["reason"].strip():
        return "Step 3 reason cannot be empty."

    if not isinstance(selection["selected_copy"], str):
        return "Step 3 selected_copy must be a string."

    if not selection["selected_copy"].strip():
        return "Step 3 selected_copy cannot be empty."

    return None


# ============================================================
# STEP 1
# ============================================================

def run_step1(brief):
    """
    Step 1:
    Extract structured attributes from the product brief.
    """

    base_prompt = render(
        read_text(PROMPTS / "extract.txt"),
        INPUT=brief
    )

    last_error = None

    for attempt in range(1, 4):

        if attempt == 1:
            prompt = base_prompt

        else:
            prompt = f"""
You are correcting a previous extraction.

Read the product brief carefully and return ONLY valid JSON.

The JSON must contain exactly:

{{
  "product_name": "string",
  "category": "string",
  "key_features": ["string"],
  "target_audience": "string"
}}

IMPORTANT:
- product_name must be the product name.
- category MUST describe what the product actually is.
- key_features must contain only facts explicitly supported by the brief.
- target_audience must come from the brief.
- Do not invent information.
- Do not leave category empty.
- Do not use marketing language.

PRODUCT BRIEF:

{brief}

PREVIOUS VALIDATION ERROR:

{last_error}
"""

        try:
            result = call_ollama(prompt)

            attributes = extract_json(result)

            error = validate_attributes(attributes)

            if error:
                last_error = error

                print(
                    f"Step 1 validation failed "
                    f"(attempt {attempt}/3): {error}"
                )

                continue

            return attributes

        except Exception as e:

            last_error = str(e)

            print(
                f"Step 1 validation failed "
                f"(attempt {attempt}/3): {last_error}"
            )

    raise RuntimeError(
        f"Step 1 failed after 3 attempts. "
        f"Last error: {last_error}"
    )


# ============================================================
# STEP 2
# ============================================================

def run_step2(attributes):
    """
    Step 2:
    Generate exactly three advertising variants.
    """

    base_prompt = render(
        read_text(PROMPTS / "generate.txt"),
        ATTRIBUTES=json.dumps(
            attributes,
            indent=2
        )
    )

    last_error = None

    for attempt in range(1, 6):

        if attempt == 1:

            prompt = base_prompt

        else:

            prompt = f"""
Generate exactly 3 advertising variants.

Return ONLY valid JSON:

{{
  "variants": [
    {{
      "id": 1,
      "copy": "..."
    }},
    {{
      "id": 2,
      "copy": "..."
    }},
    {{
      "id": 3,
      "copy": "..."
    }}
  ]
}}

STRICT RULES:

1. Use only facts from the product attributes.
2. Do not invent features.
3. Do not invent benefits.
4. Do not invent performance claims.
5. Do not use unsupported adjectives.
6. Do not use:
   - ultimate
   - innovative
   - revolutionary
   - number one
   - best
   - perfect
   - most powerful
   - premium
   - guaranteed
   - guarantee
7. Keep the language simple and factual.
8. Each variant must have an id of 1, 2, or 3.
9. There must be exactly three variants.
10. Return JSON only.

PRODUCT ATTRIBUTES:

{json.dumps(attributes, indent=2)}

PREVIOUS VALIDATION ERROR:

{last_error}

Generate the variants again from scratch.
"""

        try:

            result = call_ollama(prompt)

            variants = extract_json(result)

            error = validate_variants(variants)

            if error:

                last_error = error

                print(
                    f"Step 2 validation failed "
                    f"(attempt {attempt}/5): {error}"
                )

                continue

            return variants

        except Exception as e:

            last_error = str(e)

            print(
                f"Step 2 validation failed "
                f"(attempt {attempt}/5): {last_error}"
            )

    raise RuntimeError(
        f"Step 2 failed after 5 attempts. "
        f"Last error: {last_error}"
    )


# ============================================================
# STEP 3
# ============================================================

def run_step3(attributes, variants):
    """
    Step 3:
    Select one variant according to the brand rules.
    """

    brand_rules = read_text(
        BASE_DIR / "brand_rules.md"
    )

    prompt = f"""
You are selecting the best compliant advertising variant.

Use ONLY the supplied information.

PRODUCT ATTRIBUTES:

{json.dumps(attributes, indent=2)}

AD VARIANTS:

{json.dumps(variants, indent=2)}

BRAND RULES:

{brand_rules}

Choose one variant.

Return ONLY valid JSON in exactly this format:

{{
  "winner_id": 1,
  "reason": "short explanation",
  "selected_copy": "exact copy of the selected variant"
}}

The selected_copy MUST exactly match the copy
of the chosen variant.
"""

    result = call_ollama(prompt)

    selection = extract_json(result)

    error = validate_selection(selection)

    if error:
        raise RuntimeError(error)

    return selection


# ============================================================
# RUN ONE BRIEF
# ============================================================

def run_one(brief_path):
    """
    Run all three steps for one product brief.
    """

    brief_name = brief_path.stem

    output_dir = RUNS / brief_name

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    brief = read_text(brief_path)

    # Save original input
    (
        output_dir / "input_brief.txt"
    ).write_text(
        brief,
        encoding="utf-8"
    )

    # -------------------------
    # STEP 1
    # -------------------------

    attributes = run_step1(brief)

    (
        output_dir / "step1_attributes.json"
    ).write_text(
        json.dumps(
            attributes,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Step 1 OK: "
        f"{attributes['product_name']}"
    )

    # -------------------------
    # STEP 2
    # -------------------------

    variants = run_step2(attributes)

    (
        output_dir / "step2_variants.json"
    ).write_text(
        json.dumps(
            variants,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        "Step 2 OK: generated 3 variants"
    )

    # -------------------------
    # STEP 3
    # -------------------------

    selection = run_step3(
        attributes,
        variants
    )

    (
        output_dir / "step3_winner.json"
    ).write_text(
        json.dumps(
            selection,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"Step 3 OK: "
        f"winner {selection['winner_id']}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(f"Model: {MODEL}")

    brief_files = sorted(
        BRIEFS.glob("*.txt")
    )

    if not brief_files:
        print("No product briefs found.")
        return

    print(
        f"Running {len(brief_files)} product briefs..."
    )

    for brief_path in brief_files:

        print(
            f"\n=== {brief_path.name} ==="
        )

        try:

            run_one(brief_path)

        except Exception as e:

            print(
                f"PIPELINE FAILED: {e}"
            )

            print(
                "Intermediate files from "
                "completed steps were preserved."
            )

    print(
        "\nDone. Check chaining/runs/ "
        "for all intermediate outputs."
    )


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()