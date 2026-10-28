import streamlit as st
from services.llm_client import run_maker_generation, run_stage_3_audits
from services.deterministic_qa import run_pre_checks
from services.report_generator import build_audit_excel

st.set_page_config(page_title="SLM AI Maker-Checker Pipeline", layout="wide")
st.title("University Quadrant-II SLM Maker–Checker Hub")

# Session state initialization
if "stage" not in st.session_state:
    st.session_state.stage = "INPUT"
if "draft_text" not in st.session_state:
    st.session_state.draft_text = ""
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None

# Sidebar Configuration
st.sidebar.header("Configuration")
academic_level = st.sidebar.selectbox("Academic Level", ["Postgraduate (PG)", "Undergraduate (UG)"])

# Step 1: Input Setup
col1, col2 = st.columns(2)
with col1:
    syllabus_input = st.text_area("Approved Syllabus (JSON or List)", height=250, 
                                  placeholder='["1.1 Microeconomics", "1.2 Demand Elasticity"...]')
with col2:
    reference_input = st.text_area("Prescribed References & Sources", height=250,
                                   placeholder="Paste authoritative textbook excerpts or approved source text...")

# Step 2: Content Generation (Maker)
if st.button("Step 1: Run AI Maker (Draft SLM)", type="primary"):
    if not syllabus_input or not reference_input:
        st.error("Please provide both syllabus and reference inputs.")
    else:
        with st.spinner("Authoring SLM unit according to prescribed university standards..."):
            st.session_state.draft_text = run_maker_generation(syllabus_input, reference_input, academic_level)
            st.session_state.stage = "DRAFT_READY"

if st.session_state.draft_text:
    with st.expander("View Generated Draft (Markdown)", expanded=False):
        st.markdown(st.session_state.draft_text)

# Step 3: Automated QA & Independent Checking
if st.session_state.stage in ["DRAFT_READY", "AUDITED"]:
    if st.button("Step 2: Run Stage 2 & 3 Audits (Automated QA + AI Checker)"):
        with st.spinner("Executing Deterministic Pre-checks and Parallel AI Checkers..."):
            # Stage 2: Deterministic QA
            qa_res = run_pre_checks(st.session_state.draft_text)
            if not qa_res["passed"]:
                st.warning(f"Deterministic QA Flags: {qa_res['flags']}")
            
            # Stage 3: Parallel AI Audits
            audit_res = run_stage_3_audits(st.session_state.draft_text, syllabus_input, reference_input)
            st.session_state.audit_results = audit_res
            st.session_state.stage = "AUDITED"

# Step 4: Display Audit Dashboard & Export
if st.session_state.audit_results:
    res = st.session_state.audit_results
    st.divider()
    st.subheader("Stage 3: Independent Audit Results")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Gate Decision", res["decision"])
    m2.metric("Weighted Quality Score", f"{res['score']:.1f}%")
    m3.metric("Syllabus Coverage", f"{res['coverage_pct']:.1f}%")
    m4.metric("Prompt Adherence Status", res["prompt_status"])

    # Tabs for Details
    tab_err, tab_syl, tab_prompt = st.tabs(["Error Register", "Syllabus Matrix", "Prompt Adherence"])
    with tab_err:
        st.dataframe(res["error_register"], use_container_width=True)
    with tab_syl:
        st.dataframe(res["syllabus_mapping"], use_container_width=True)
    with tab_prompt:
        st.dataframe(res["prompt_adherence_logs"], use_container_width=True)

    # Downloadable Excel Artifact
    excel_bytes = build_audit_excel(res)
    st.download_button(
        label="Download Comprehensive Audit Report (.xlsx)",
        data=excel_bytes,
        file_name="SLM_Comprehensive_Audit_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
