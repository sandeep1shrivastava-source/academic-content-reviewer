import json
import streamlit as st
from google import genai
from prompt_library import SOP_CONFIG

# Read key strictly from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is missing in Streamlit App Settings -> Secrets."
    )

client = genai.Client(api_key=api_key)
# 1. Fetch API key safely from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY", None)

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is missing. Please add it to your Streamlit App Settings -> Secrets."
    )

client = genai.Client(api_key=api_key)

# 2. Only active, production models (no retired 2.x versions)
ACTIVE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
]


def evaluate_content(category: str, subject: str, content: str) -> dict:
    config = SOP_CONFIG.get(category)
    if not config:
        raise ValueError(f"Category '{category}' is not configured.")

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
            error_log.append(f"[{model_name}]: {str(e)}")
            continue

    raise RuntimeError(
        "Cloud model call failed. Details:\n" + "\n".join(error_log)
    )
