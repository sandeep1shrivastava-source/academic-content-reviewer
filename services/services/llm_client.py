import json
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def call_llm(system_prompt: str, user_content: str, response_format=None) -> str:
    params = {
        "model": "gpt-4o",
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    }
    if response_format:
        params["response_format"] = response_format
    
    response = client.chat.completions.create(**params)
    return response.choices[0].message.content

def run_maker_generation(syllabus: str, reference: str, level: str) -> str:
    from prompts.maker_prompts import MAKER_SYSTEM_PROMPT, MAKER_USER_TEMPLATE
    user_payload = MAKER_USER_TEMPLATE.format(
        academic_level=level, syllabus=syllabus, reference=reference
    )
    # Use higher temperature for content drafting
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.35,
        messages=[
            {"role": "system", "content": MAKER_SYSTEM_PROMPT},
            {"role": "user", "content": user_payload}
        ]
    )
    return response.choices[0].message.content

def run_stage_3_audits(draft: str, syllabus: str, reference: str) -> dict:
    from prompts.checker_prompts import CHECKER_SYSTEM_PROMPT
    from prompts.mapping_prompts import MAPPING_SYSTEM_PROMPT
    from prompts.meta_prompts import META_SYSTEM_PROMPT

    def run_checker():
        payload = f"Syllabus:\n{syllabus}\n\nReferences:\n{reference}\n\nDraft:\n{draft}"
        res = call_llm(CHECKER_SYSTEM_PROMPT, payload, {"type": "json_object"})
        return json.loads(res)

    def run_mapping():
        payload = f"Syllabus:\n{syllabus}\n\nDraft:\n{draft}"
        res = call_llm(MAPPING_SYSTEM_PROMPT, payload, {"type": "json_object"})
        return json.loads(res)

    def run_meta():
        payload = f"Draft to analyze:\n{draft}"
        res = call_llm(META_SYSTEM_PROMPT, payload, {"type": "json_object"})
        return json.loads(res)

    # Execute all 3 checks in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_checker = executor.submit(run_checker)
        f_mapping = executor.submit(run_mapping)
        f_meta = executor.submit(run_meta)

        checker_data = f_checker.result()
        mapping_data = f_mapping.result()
        meta_data = f_meta.result()

    # Aggregate results and compute decision gate
    score = checker_data.get("audit_metadata", {}).get("overall_score", 0.0)
    errors = checker_data.get("error_register", [])
    critical_errors = [e for e in errors if e.get("severity", "").lower() == "critical"]
    coverage_pct = mapping_data.get("coverage_percentage", 0.0)
    prompt_status = meta_data.get("prompt_adherence_status", "FAIL")

    decision = "PASS"
    if score < 95.0 or len(critical_errors) > 0 or coverage_pct < 100.0 or prompt_status == "FAIL":
        decision = "REVISE" if score >= 85.0 else "SME REVIEW REQUIRED"

    return {
        "decision": decision,
        "score": score,
        "coverage_pct": coverage_pct,
        "prompt_status": prompt_status,
        "critical_count": len(critical_errors),
        "error_register": errors,
        "syllabus_mapping": mapping_data.get("syllabus_mapping", []),
        "prompt_adherence_logs": meta_data.get("adherence_logs", [])
    }
