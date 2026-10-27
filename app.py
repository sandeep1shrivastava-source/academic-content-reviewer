import streamlit as st
import pandas as pd
from prompt_library import SOP_CONFIG
from parser import extract_document_text
from reviewer import evaluate_content

st.set_page_config(page_title="Academic Content QA Reviewer", page_icon="📝", layout="wide")

st.title("📝 Content Review & Percentage Reporting System")
st.markdown("Automated rubric-based QA assessment across educational assets.")

# Left sidebar controls
with st.sidebar:
    st.header("Upload Parameters")
    category = st.selectbox(
        "Content Category",
        options=list(SOP_CONFIG.keys()),
        index=0,
        help="Select the exact review pipeline according to SOP specifications."
    )
    subject = st.text_input("Subject / Course Title", placeholder="e.g., Database Management Systems")
    uploaded_file = st.file_uploader(
        "Upload File", 
        type=["docx", "xlsx", "xls", "pdf", "txt"],
        help="Upload document in standard format (Word, Excel, or PDF)."
    )
    run_btn = st.button("Generate Review", type="primary", use_container_width=True)

# Main evaluation window
if run_btn:
    if not subject.strip():
        st.warning("Please provide the subject name.")
    elif not uploaded_file:
        st.warning("Please upload a file to evaluate.")
    else:
        with st.spinner("Parsing file and scoring against SOP rubrics..."):
            try:
                # Ingest document
                extracted_text = extract_document_text(uploaded_file)
                if not extracted_text.strip():
                    st.error("No readable text found in the uploaded file.")
                    st.stop()
                
                # Call LLM evaluation
                result = evaluate_content(category, subject, extracted_text)
                
                # Top Metrics
                st.subheader("Executive Outcome Report")
                score = result.get("final_score_percentage", 0)
                status = result.get("status", "FAIL")
                
                m1, m2, m3 = st.columns([1, 1, 3])
                m1.metric("Final Score", f"{score}%")
                
                if status == "AUTO-FAIL":
                    m2.error(f"Status: {status}")
                elif score >= 75:
                    m2.success(f"Status: {status}")
                else:
                    m2.warning(f"Status: {status}")
                
                m3.info(result.get("executive_summary", "No summary provided."))
                
                st.divider()
                
                # Deductions Table
                st.subheader("Percentage-Wise Deductions")
                deductions = result.get("deductions", [])
                if deductions:
                    records = []
                    for d in deductions:
                        records.append({
                            "Rubric Item": d.get("category"),
                            "Points Deducted": f"-{d.get('deduction_points')}%",
                            "Reason": d.get("rationale"),
                            "Evidence / Snippets": ", ".join(d.get("evidence", []))
                        })
                    st.table(pd.DataFrame(records))
                else:
                    st.success("No deductions identified. 100% compliance.")
                
                # Actionable Corrections
                st.subheader("Actionable Recommendations & Fixes")
                corrections = result.get("actionable_corrections", [])
                if corrections:
                    for i, item in enumerate(corrections, start=1):
                        with st.expander(f"Item {i}: {item.get('location', 'General')}"):
                            st.write(f"**Issue:** {item.get('issue')}")
                            st.success(f"**Recommended Correction:** {item.get('suggested_fix')}")
                else:
                    st.write("No specific corrections required.")
                    
            except Exception as e:
                st.error(f"Review failed: {str(e)}")