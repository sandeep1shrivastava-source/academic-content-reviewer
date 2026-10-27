import pandas as pd
import streamlit as st
from parser import extract_document_text
from prompt_library import SOP_CONFIG
from reviewer import evaluate_content

st.set_page_config(
    page_title="Academic Content Reviewer", page_icon="📝", layout="wide"
)

st.title("📝 Content Review & Quality Audit System")
st.caption(
    "Automated rubric-based QA assessment across educational assets against departmental SOPs."
)

with st.sidebar:
    st.header("Settings & Credentials")
    api_key_input = st.text_input(
        "Gemini API Key (Optional)",
        type="password",
        help="Leave blank to use the key from Streamlit Secrets",
    )

    st.header("Upload Parameters")
    category = st.selectbox("Content Category", options=list(SOP_CONFIG.keys()))
    subject = st.text_input(
        "Subject / Course Title", placeholder="e.g., Environmental Science"
    )
    uploaded_file = st.file_uploader(
        "Upload Content Document", type=["docx", "xlsx", "xls", "pdf", "txt"]
    )
    run_btn = st.button("Generate Review", type="primary", use_container_width=True)

if run_btn:
    if not subject.strip():
        st.warning("Please enter the subject name.")
    elif not uploaded_file:
        st.warning("Please upload a document to evaluate.")
    else:
        with st.spinner("Analyzing document against SOP criteria..."):
            try:
                raw_text = extract_document_text(uploaded_file)
                key_to_pass = (
                    api_key_input.strip() if api_key_input.strip() else None
                )
                report = evaluate_content(
                    category, subject, raw_text, api_key=key_to_pass
                )

                st.divider()

                # --- 1. OPENING STATEMENT ---
                opening = report.get("opening_statement", "")
                if opening:
                    st.info(f"📌 **Overview:** {opening}")

                # --- 2. EXECUTIVE SUMMARY METRICS ---
                exec_sum = report.get("executive_summary", {})

                # Extract score reliably whether numeric or string
                score = exec_sum.get(
                    "overall_compliance_score",
                    report.get("final_score_percentage", 0),
                )
                try:
                    score_val = float(str(score).replace("%", "").strip())
                except ValueError:
                    score_val = 0.0

                # Determine status and color
                verdict_data = report.get("final_verdict", {})
                verdict = (
                    verdict_data.get("verdict")
                    if isinstance(verdict_data, dict)
                    else report.get("status", "Review Completed")
                )

                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    st.metric("Overall Compliance", f"{score_val}%")
                with col2:
                    if (
                        "Pass" in str(verdict)
                        or "Approved" in str(verdict)
                        or score_val >= 85
                    ):
                        st.success(f"Status: {verdict}")
                    else:
                        st.error(f"Status: {verdict}")
                with col3:
                    st.markdown(
                        f"**Primary Focus:** {exec_sum.get('primary_area_for_improvement', 'N/A')}"
                    )

                st.markdown(
                    f"""
                * **Critical Risks:** {exec_sum.get('critical_risks', 'Clean')}
                * **Structural Integrity:** {exec_sum.get('structural_integrity', '100%')}
                * **Factual Accuracy:** {exec_sum.get('factual_accuracy', 'Verified')}
                """
                )

                st.divider()

                # --- 3. DETAILED REVIEW MATRIX ---
                st.subheader("Detailed Review Matrix")
                matrix = report.get("detailed_review_matrix", [])
                if matrix and isinstance(matrix, list):
                    df = pd.DataFrame(matrix)
                    # Rename columns cleanly
                    col_map = {
                        "criterion": "Criterion",
                        "score": "Score (%)",
                        "status": "Status",
                        "observation": "Observation / Statement",
                    }
                    df = df.rename(
                        columns={k: v for k, v in col_map.items() if k in df}
                    )
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.write("No detailed matrix items returned.")

                st.divider()

                # --- 4. REQUIRED CORRECTIONS (ACTION LIST) ---
                st.subheader("Required Corrections (Action List)")
                corrections = report.get("required_corrections", [])
                if corrections and isinstance(corrections, list):
                    for i, corr in enumerate(corrections, 1):
                        priority = corr.get("priority", "Medium Priority")
                        title = corr.get("title", f"Correction #{i}")

                        if "High" in priority:
                            p_tag = "🔴 **[High Priority]**"
                        elif "Medium" in priority:
                            p_tag = "🟡 **[Medium Priority]**"
                        else:
                            p_tag = "🟢 **[Low Priority]**"

                        st.markdown(f"#### {i}. {title} {p_tag}")
                        st.markdown(
                            f"**Location:** `{corr.get('location', 'N/A')}`"
                        )
                        st.markdown(f"**Error:** {corr.get('error', 'N/A')}")
                        st.markdown(
                            f"**Required Fix:** {corr.get('correction', 'N/A')}"
                        )
                        st.write("---")
                else:
                    st.success("No critical corrections required.")

                # --- 5. FINAL VERDICT ---
                if isinstance(verdict_data, dict) and verdict_data.get(
                    "reason"
                ):
                    st.subheader("Final Verdict")
                    st.info(
                        f"**{verdict_data.get('verdict', 'Completed')}:** {verdict_data.get('reason')}"
                    )

            except Exception as e:
                st.error(f"Review failed: {str(e)}")
