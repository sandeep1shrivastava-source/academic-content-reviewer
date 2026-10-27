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
    "gemini-2.5-flash-lite",
]


def evaluate_content(
    category: str,
    subject: str,
    content: str,
    api_key: str = None,
    max_retries_per_model: int = 3,
) -> dict:
    config = SOP_CONFIG.get(category)
    if not config:
        raise ValueError(f"Category '{category}' is not configured.")

    # If no key passed from UI, fetch automatically from Streamlit Secrets or environment
    if not api_key:
        api_key = st.secrets.get("GEMINI_API_KEY", "") or os.getenv(
            "GEMINI_API_KEY", ""
        )

    api_key = str(api_key).strip().replace('"', "").replace("'", "")

    if not api_key:
        raise ValueError(
            "API Key is missing. Please provide it in the sidebar or configure GEMINI_API_KEY in Streamlit Secrets."
        )

    client = genai.Client(api_key=api_key)

    system_instruction = f"""You are an elite QA and SME auditor reviewing educational content for the subject '{subject}'.
Category: {category}

SOP RUBRIC TO ENFORCE:
{config['rubric']}

AUDIT INSTRUCTIONS:
1. Check every date, figure, and formula for typographical errors (e.g., impossible years like '20100').
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
    "primary_area_for_improvement": "Correction of the year '20100' and removal of redundant headings."
  }},
  "detailed_review_matrix": [
    {{"criterion": "a. Grammar & Sentence Formation", "score": "90%", "status": "Minor Issue", "observation": "Detail specific typo and section."}},
    {{"criterion": "b. Paragraph Repetition", "score": "95%", "status": "Minor Issue", "observation": "Detail duplicated heading or paragraph."}},
    {{"criterion": "c. SME Factual Accuracy", "score": "98%", "status": "Pass", "observation": "Factual verification notes."}},
    {{"criterion": "d. Bias/Discrimination", "score": "100%", "status": "Pass", "observation": "Zero instances found."}},
    {{"criterion": "e. Disability & Profession", "score": "100%", "status": "Pass", "observation": "No offensive references."}},
    {{"criterion": "f. TOC vs. Body Consistency", "score": "100%", "status": "Pass", "observation": "Structure verified."}},
    {{"criterion": "g. Structural Requirements", "score": "100%", "status": "Pass", "observation": "Mandatory sections verified."}},
    {{"criterion": "h. AI/ChatGPT Mentions", "score": "100%", "status": "Pass", "observation": "No prohibited terms found."}},
    {{"criterion": "i. Subject/E-book Consistency", "score": "100%", "status": "Pass", "observation": "Title and material aligned."}}
  ],
  "required_corrections": [
    {{
      "title": "Correct Critical Date Typo",
      "priority": "High Priority",
      "location": "Section 3.2.5",
      "error": "global mean sea level would likely rise by 20100",
      "correction": "Change 20100 to 2100."
    }}
  ],
  "final_verdict": {{
    "verdict": "Approved with Minor Edits",
    "reason": "Clear explanation of audit decision."
  }}
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

                # Retry on temporary traffic surges (503 / 429)
                if (
                    "503" in err_text
                    or "429" in err_text
                    or "UNAVAILABLE" in err_text
                ):
                    wait_time = 2 * (attempt + 1)
                    time.sleep(wait_time)
                    if attempt == max_retries_per_model - 1:
                        error_log.append(
                            f"[{model_name}]: Spikes persisted after {max_retries_per_model} retries."
                        )
                    continue
                else:
                    error_log.append(f"[{model_name}]: {err_text}")
                    break

    raise RuntimeError(
        "All candidate models failed. Details:\n" + "\n".join(error_log)
    )
