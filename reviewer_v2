import json
import os
import time
import streamlit as st
from google import genai
from prompt_library import SOP_CONFIG

ACTIVE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]

def evaluate_content(
    category: str,
    subject: str,
    content: str,
    api_key: str = None,
    syllabus_text: str = None,
    custom_prompt: str = None,
    max_retries_per_model: int = 3,
) -> dict:
    config = SOP_CONFIG.get(category)
    if not config:
        raise ValueError(f"Category '{category}' is not configured.")

    if not api_key:
        api_key = st.secrets.get("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    api_key = str(api_key).strip().replace('"', "").replace("'", "")

    if not api_key:
        raise ValueError("API Key is missing.")

    client = genai.Client(api_key=api_key)

    # 1. Inject Optional Syllabus Instruction
    syllabus_instruction = ""
    if syllabus_text:
        syllabus_instruction = f"\n\nSYLLABUS FOR COMPARISON:\n{syllabus_text[:10000]}\n\n-> CRITICAL: Cross-check the document against the syllabus. Deduct points if mandatory syllabus topics are missing, or if out-of-syllabus content is present."

    # 2. Inject Optional Custom AI Prompt
    custom_prompt_instruction = ""
    if custom_prompt:
        custom_prompt_instruction = f"\n\nCUSTOM AI CHECKER RULES:\n{custom_prompt}\n\n-> CRITICAL: You must strictly enforce these additional rules during your evaluation."

    system_instruction = f"""You are an elite QA and SME auditor reviewing educational content for '{subject}'.
Category: {category}

SOP RUBRIC TO ENFORCE:
{config['rubric']}{syllabus_instruction}{custom_prompt_instruction}

AUDIT INSTRUCTIONS:
1. Check every date, figure, and formula for typographical errors.
2. Check for duplicate headings or repetitive paragraphs across sections.
3. Check for mandatory ending sections: Summary, Keywords, Self-Assessment Questions (SAQs), and References.
4. Verify there are zero mentions of 'AI', 'ChatGPT', or discriminatory language.
5. If errors exist, you MUST deduct points and detail them in the Required Corrections.

Output strictly valid JSON matching this schema:
{{
  "opening_statement": "1-2 sentences summarizing overall quality and critical issues.",
  "executive_summary": {{
    "overall_compliance_score": 97.8,
    "critical_risks": "0% (Clean)",
    "structural_integrity": "100% (All mandatory sections present)",
    "factual_accuracy": "98% (One major date typo found)",
    "primary_area_for_improvement": "Correction of the year '20100'."
  }},
  "detailed_review_matrix": [
    {{"criterion": "a. Grammar & Sentence Formation", "score": "90%", "status": "Minor Issue", "observation": "Detail specific typo and section."}},
    {{"criterion": "b. Syllabus Alignment", "score": "100%", "status": "Pass", "observation": "Aligns perfectly with syllabus."}}
  ],
  "required_corrections": [
    {{
      "title": "Correct Critical Date Typo",
      "priority": "High Priority",
      "location": "Section 3.2.5",
      "error": "global mean sea level would likely rise by 20100",
      "correction": "Change 20100 to 2100."
    }}
  ]
}}
"""

    user_message = f"Subject: {subject}\n\nDOCUMENT CONTENT TO EVALUATE:\n{content}"
    error_log = []

    for model_name in ACTIVE_MODELS:
        for attempt in range(max_retries_per_model):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_message,
                    config={
                        "system_instruction": system_instruction,
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                    },
                )
                return json.loads(response.text)

            except Exception as e:
                err_text = str(e)
                if "503" in err_text or "429" in err_text or "UNAVAILABLE" in err_text:
                    time.sleep(2 * (attempt + 1))
                    continue
                else:
                    error_log.append(f"[{model_name}]: {err_text}")
                    break

    raise RuntimeError("All candidate models failed. Details:\n" + "\n".join(error_log))
