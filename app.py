"""
AI-Powered Resume Screening & Candidate Ranking System with RAG.
Single-page Streamlit application.
"""

import base64
import atexit
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote
from uuid import uuid4

import pandas as pd
import streamlit as st

from core.candidate_extractor import CandidateExtractor
from core.chroma_manager import ChromaManager
from core.chunking import ChunkingEngine
from core.embeddings import EmbeddingModel
from core.evaluation import EvaluationFramework
from core.jd_extractor import JDExtractor
from core.ranking import RankingEngine
from core.retrieval import RetrievalEngine
from core.session_manager import SessionManager
from config import EVALUATION_EXPORT_PATH


TEMP_DATA_PARENT = "data"
MAX_UPLOAD_SIZE_BYTES = 1024 * 1024 * 1024


st.set_page_config(
    page_title="Resume Screening & Ranking System",
    page_icon="DOC",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
    .block-container { padding-top: 1.25rem; max-width: 1280px; }
    .section-header {
        background: #f7f9fc;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 20px 0 14px;
    }
    .section-header h2 { margin: 0; font-size: 1.25rem; }
    .success-box, .error-box, .info-box {
        border-radius: 6px;
        margin: 10px 0;
        padding: 12px 14px;
    }
    .success-box { background: #dcfce7; color: #14532d; }
    .error-box { background: #fee2e2; color: #7f1d1d; }
    .info-box { background: #e0f2fe; color: #0c4a6e; }
    .chat-nav-row {
        position: sticky;
        top: 12px;
        z-index: 999;
        background: rgba(255,255,255,.96);
        padding: 8px 0 10px;
        border-bottom: 1px solid #eef2f7;
    }
    .chat-nav-row div[data-testid="column"]:last-child button {
        min-height: 44px;
        width: 44px;
        padding: 0;
        border-radius: 999px;
        font-size: 1.25rem;
        line-height: 1;
        float: right;
        transform: translateY(14px);
        box-shadow: 0 10px 24px rgba(15, 23, 42, .18);
    }
    div[data-testid="stMetricValue"] { font-size: 1.25rem; }
    div[data-testid="stFileUploader"] small { display: none; }
</style>
""",
    unsafe_allow_html=True,
)


def section_header(title: str, subtitle: Optional[str] = None) -> None:
    body = f"<h2>{title}</h2>"
    if subtitle:
        body += f"<div>{subtitle}</div>"
    st.markdown(f'<div class="section-header">{body}</div>', unsafe_allow_html=True)


def reset_runtime_state() -> None:
    preserved = {
        "embedding_model": st.session_state.get("embedding_model"),
        "chunking_engine": st.session_state.get("chunking_engine"),
        "file_uploader_key": st.session_state.get("file_uploader_key", 0) + 1,
        "jd_uploader_key": st.session_state.get("jd_uploader_key", 0) + 1,
    }
    st.session_state.clear()
    for key, value in preserved.items():
        if value is not None:
            st.session_state[key] = value


def initialize_session() -> None:
    if "run_session_id" not in st.session_state:
        SessionManager.cleanup_session_dirs(TEMP_DATA_PARENT)
        st.session_state.run_session_id = uuid4().hex
        st.session_state.session_data_dir = str(Path(TEMP_DATA_PARENT) / f"session_{st.session_state.run_session_id}")
        atexit.register(SessionManager.cleanup_session_dirs, TEMP_DATA_PARENT)

    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager(st.session_state.session_data_dir)

    if "embedding_model" not in st.session_state:
        with st.spinner("Loading embedding model..."):
            st.session_state.embedding_model = EmbeddingModel()

    if "chunking_engine" not in st.session_state:
        st.session_state.chunking_engine = ChunkingEngine(chunk_size=700, chunk_overlap=100)

    if "chroma_manager" not in st.session_state:
        chroma_path = str(Path(st.session_state.session_data_dir) / "chroma_db")
        st.session_state.chroma_manager = ChromaManager(db_path=chroma_path, collection_name="resumes")

    if "evaluation_framework" not in st.session_state:
        st.session_state.evaluation_framework = EvaluationFramework(EVALUATION_EXPORT_PATH)

    defaults = {
        "candidates": [],
        "jd_data": {},
        "processed_jd_text": "",
        "ranking_data": [],
        "selected_candidate": None,
        "chat_sessions": {},
        "active_chat_id": None,
        "ground_truth_qa": [],
        "retrieval_engine": None,
        "processed_upload_names": set(),
        "resume_processing_done": False,
        "jd_processing_done": False,
        "ranking_done": False,
        "show_resume_pdf": False,
        "last_error": "",
        "last_resume_remove_message": "",
        "file_uploader_key": 0,
        "jd_uploader_key": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session()


def apply_resume_query_param() -> None:
    resume_file = st.query_params.get("resume")
    if not resume_file:
        return

    if isinstance(resume_file, list):
        resume_file = resume_file[0] if resume_file else ""
    if not resume_file:
        return

    def normalize_resume_ref(value: Any) -> str:
        decoded = unquote(str(value or "")).replace("\\", "/").split("/")[-1]
        return " ".join(decoded.strip().lower().split())

    resume_key = normalize_resume_ref(resume_file)
    for candidate in st.session_state.get("ranking_data", []) + st.session_state.get("candidates", []):
        if normalize_resume_ref(candidate.get("pdf_file")) == resume_key:
            st.session_state.selected_candidate = candidate
            st.session_state.show_resume_pdf = True
            st.session_state.last_error = ""
            return
    st.session_state.last_error = f"Could not open resume '{resume_file}'. It was not found in the current session."


def clear_session() -> None:
    try:
        if "chroma_manager" in st.session_state:
            st.session_state.chroma_manager.clear_database()
        if "session_manager" in st.session_state:
            st.session_state.session_manager.clear_session()
    finally:
        reset_runtime_state()
        SessionManager.cleanup_session_dirs(TEMP_DATA_PARENT)
        st.rerun()


def render_top_bar() -> None:
    st.markdown('<div class="chat-nav-row">', unsafe_allow_html=True)
    left, right = st.columns([8, 0.5])
    with left:
        st.title("AI Resume Screening System")
    with right:
        if st.button("💬", key="open_chatbot_page", help="Open Candidate Intelligence Assistant"):
            st.switch_page("pages/chatbot_engine.py")
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.header("Session")
        st.metric("Candidates", len(st.session_state.candidates))
        st.metric("JD Loaded", "Yes" if st.session_state.jd_data else "No")
        st.metric("Rankings", len(st.session_state.ranking_data))
        st.divider()
        if st.button("Clear Session", type="primary", use_container_width=True):
            clear_session()


def validated_candidate_phone(candidate: Dict[str, Any]) -> str:
    phone = candidate.get("phone")
    if CandidateExtractor.is_valid_phone(phone):
        return " ".join(str(phone).strip().split())

    extracted = CandidateExtractor.extract_phone(candidate.get("full_text", ""))
    return extracted or ""


def remove_resume(candidate: Dict[str, Any]) -> None:
    """Remove one uploaded resume and invalidate dependent resume/ranking state."""
    pdf_file = candidate.get("pdf_file", "")
    candidate_name = candidate.get("candidate_name", "")

    st.session_state.candidates = [
        item for item in st.session_state.candidates
        if item.get("pdf_file") != pdf_file
    ]
    st.session_state.processed_upload_names.discard(pdf_file)

    session_manager = st.session_state.get("session_manager")
    if session_manager is not None:
        resume_path = session_manager.temp_resumes_dir / pdf_file
        candidate_path = session_manager.extracted_candidates_dir / f"{candidate_name}.json"
        for path in [resume_path, candidate_path]:
            if path.exists():
                path.unlink()

    selected_candidate = st.session_state.get("selected_candidate") or {}
    if selected_candidate.get("pdf_file") == pdf_file:
        st.session_state.selected_candidate = None
        st.session_state.show_resume_pdf = False

    if st.session_state.get("chroma_manager") is not None:
        try:
            st.session_state.chroma_manager.clear_collection()
        except Exception as exc:
            st.session_state.last_error = f"Could not clear resume index after removal: {exc}"

    st.session_state.resume_processing_done = False
    st.session_state.ranking_done = False
    st.session_state.ranking_data = []
    st.session_state.retrieval_engine = None
    st.session_state.ground_truth_qa = []
    st.session_state.file_uploader_key += 1
    st.session_state.last_resume_remove_message = f"Removed {pdf_file}."


def render_upload_table() -> None:
    if not st.session_state.candidates:
        st.info("No resumes uploaded yet.")
        return

    if st.session_state.last_resume_remove_message:
        st.success(st.session_state.last_resume_remove_message)
        st.session_state.last_resume_remove_message = ""

    rows = [
        {
            "Candidate Name": c.get("candidate_name", "N/A"),
            "Email": c.get("email") or "N/A",
            "Contact Number": validated_candidate_phone(c) or "N/A",
            "Resume": c.get("pdf_file", "N/A"),
        }
        for c in st.session_state.candidates
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    resume_options = {
        f"{candidate.get('candidate_name', 'N/A')} - {candidate.get('pdf_file', 'N/A')}": candidate
        for candidate in st.session_state.candidates
    }
    selected_resume = st.selectbox(
        "Select a resume to remove",
        list(resume_options.keys()),
        key="remove_resume_select",
    )
    if st.button("Remove Selected Resume", key="remove_selected_resume"):
        remove_resume(resume_options[selected_resume])
        st.rerun()


def render_resume_upload() -> None:
    section_header("Section 1: Resume Upload", "Upload PDF resumes. Same filename uploads are blocked; different filenames are allowed.")

    uploaded_files = st.file_uploader(
        "Choose PDF resumes",
        type="pdf",
        accept_multiple_files=True,
        key=f"resume_uploader_{st.session_state.file_uploader_key}",
    )

    if uploaded_files:
        pending_files = [f for f in uploaded_files if f.name not in st.session_state.processed_upload_names]
        if pending_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            added = 0

            for idx, uploaded_file in enumerate(pending_files, 1):
                status_text.text(f"Processing {idx}/{len(pending_files)}: {uploaded_file.name}")
                progress_bar.progress(idx / len(pending_files))

                file_bytes = uploaded_file.read()
                if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
                    st.warning(f"{uploaded_file.name} - File exceeds the 1GB upload limit.")
                    st.session_state.processed_upload_names.add(uploaded_file.name)
                    continue

                success, message = st.session_state.session_manager.save_uploaded_resume(file_bytes, uploaded_file.name)
                st.session_state.processed_upload_names.add(uploaded_file.name)

                if success:
                    pdf_path = st.session_state.session_manager.temp_resumes_dir / uploaded_file.name
                    extracted = CandidateExtractor.extract_from_resume(str(pdf_path), uploaded_file.name)
                    st.session_state.session_manager.save_candidate_data(extracted["candidate_name"], extracted)
                    st.session_state.candidates.append(extracted)
                    added += 1
                    st.success(f"{extracted['candidate_name']} - {message}")
                else:
                    st.warning(f"{uploaded_file.name} - {message}")

            status_text.text("Upload processing complete.")
            st.session_state.resume_processing_done = False
            st.session_state.jd_processing_done = False
            st.session_state.ranking_done = False
            st.session_state.ranking_data = []
            st.session_state.selected_candidate = None
            st.markdown(
                f'<div class="success-box"> {added} new resumes added.</div>',
                unsafe_allow_html=True,
            )

    st.subheader("Uploaded Candidates")
    render_upload_table()


def render_resume_processing() -> None:
    if not st.session_state.candidates:
        return

    section_header("Section 2: Resume Processing", "Index uploaded resumes for search and chatbot retrieval.")
    st.metric("Resume Count", len(st.session_state.candidates))

    if st.session_state.resume_processing_done:
        st.success("Resumes are processed and indexed.")
        return

    if st.button("Start Processing", key="start_processing", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_chunks: List[Dict[str, Any]] = []

        try:
            for idx, candidate in enumerate(st.session_state.candidates, 1):
                status_text.text(f"Processing {idx}/{len(st.session_state.candidates)}: {candidate['candidate_name']}")
                progress_bar.progress(idx / len(st.session_state.candidates))

                chunks = st.session_state.chunking_engine.chunk_by_sections(
                    candidate.get("full_text", ""),
                    candidate_name=candidate["candidate_name"],
                    email=candidate.get("email", ""),
                    phone=validated_candidate_phone(candidate),
                )
                chunks_with_embeddings = st.session_state.embedding_model.encode_chunks(chunks)
                all_chunks.extend(chunks_with_embeddings)

            status_text.text("Storing resume embeddings in vector database...")
            st.session_state.chroma_manager.clear_collection()
            st.session_state.chroma_manager.create_collection()
            st.session_state.chroma_manager.add_chunks(all_chunks)
            st.session_state.resume_processing_done = True
            st.session_state.jd_processing_done = False
            st.session_state.ranking_done = False
            st.session_state.ranking_data = []
            st.markdown(
                '<div class="success-box">Processing complete. Resumes are ready for job matching.</div>',
                unsafe_allow_html=True,
            )
            st.rerun()
        except Exception as exc:
            st.session_state.last_error = str(exc)
            st.error(f"Resume processing failed: {exc}")
    else:
        st.info("Click Start Processing to index the uploaded resumes.")


def extract_jd_from_upload(jd_file) -> Dict[str, Any]:
    jd_path = st.session_state.session_manager.base_data_dir / "temp_jd.pdf"
    jd_path.write_bytes(jd_file.read())
    try:
        return JDExtractor.extract_from_pdf(str(jd_path))
    finally:
        if jd_path.exists():
            os.remove(jd_path)


def run_ranking() -> None:
    if not st.session_state.candidates:
        raise ValueError("Upload resumes before generating rankings.")
    if not st.session_state.jd_data:
        raise ValueError("Process a valid job description before generating rankings.")

    for candidate in st.session_state.candidates:
        candidate["phone"] = validated_candidate_phone(candidate)

    semantic_similarities: Dict[str, float] = {}
    jd_required_skills = st.session_state.jd_data.get("required_skills", [])
    jd_preferred_skills = st.session_state.jd_data.get("preferred_skills", [])
    jd_education = st.session_state.jd_data.get("education_requirements", [])
    jd_experience = st.session_state.jd_data.get("experience_requirement", "")
    jd_full_text = st.session_state.jd_data.get("full_text", "")
    jd_embedding_text = " ".join([
        " ".join(jd_required_skills),
        " ".join(jd_preferred_skills),
        jd_experience,
        " ".join(jd_education),
        jd_full_text,
    ]).strip()
    jd_embedding = st.session_state.embedding_model.encode_text(jd_embedding_text)

    progress_bar = st.progress(0)
    status_text = st.empty()
    for idx, candidate in enumerate(st.session_state.candidates, 1):
        status_text.text(f"Scoring {idx}/{len(st.session_state.candidates)}: {candidate['candidate_name']}")
        progress_bar.progress(idx / len(st.session_state.candidates))
        candidate_text = " ".join([
            " ".join(candidate.get('skills', [])),
            candidate.get('experience_summary', ''),
            " ".join(candidate.get('education', [])),
            candidate.get('full_text', ''),
        ]).strip()
        candidate_embedding = st.session_state.embedding_model.encode_text(candidate_text)
        semantic_similarities[candidate["candidate_name"]] = max(
            st.session_state.embedding_model.similarity(jd_embedding, candidate_embedding),
            0.0,
        )

    ranking_data = RankingEngine.rank_candidates_with_bm25(
        st.session_state.candidates,
        st.session_state.jd_data,
        semantic_similarities,
        bm25_weight=0.40,
    )

    st.session_state.ranking_data = ranking_data
    st.session_state.ranking_done = True
    ground_truth = st.session_state.evaluation_framework.generate_ground_truth_qa(
        st.session_state.candidates,
        st.session_state.jd_data,
        st.session_state.ranking_data,
    )
    st.session_state.ground_truth_qa = ground_truth
    st.session_state.session_manager.save_ground_truth(ground_truth)
    st.session_state.retrieval_engine = RetrievalEngine(
        st.session_state.chroma_manager,
        st.session_state.embedding_model,
        st.session_state.ranking_data,
    )


def render_job_description() -> None:
    if not st.session_state.resume_processing_done:
        return

    section_header("Section 3: Job Description", "Upload a JD PDF or paste job description text, then generate rankings.")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Upload JD PDF")
        jd_file = st.file_uploader("Choose a JD PDF", type="pdf", key=f"jd_uploader_{st.session_state.jd_uploader_key}")
        if jd_file and st.button("Process Uploaded JD", key="process_jd_pdf"):
            with st.spinner("Extracting job description..."):
                try:
                    st.session_state.jd_data = extract_jd_from_upload(jd_file)
                    st.session_state.processed_jd_text = st.session_state.jd_data.get("full_text", "")
                    st.session_state.jd_processing_done = True
                    st.success("Job description extracted successfully.")
                except Exception as exc:
                    st.error(f"Could not process JD PDF: {exc}")

    with col2:
        st.subheader("Paste JD Text")
        jd_text = st.text_area("Job description text", height=210, key="jd_text_area")
        if st.button("Process Text JD", key="process_jd_text"):
            cleaned = jd_text.strip()
            if len(cleaned) < 40:
                st.error("Please enter a meaningful job description before processing.")
            else:
                with st.spinner("Processing job description..."):
                    try:
                        st.session_state.jd_data = JDExtractor.extract_from_text(cleaned)
                        st.session_state.processed_jd_text = cleaned
                        st.session_state.jd_processing_done = True
                        st.success("Job description processed successfully.")
                    except Exception as exc:
                        st.error(f"Could not process JD text: {exc}")

    if st.session_state.jd_data:
        processed_text = st.session_state.get("processed_jd_text") or st.session_state.jd_data.get("full_text", "")
        if processed_text:
            st.subheader("Processed Job Description")
            st.text_area(
                "JD description",
                value=processed_text,
                height=210,
                disabled=True,
            )

        st.subheader("Extracted Job Requirements")
        req, pref = st.columns(2)
        with req:
            st.write("Required Skills")
            st.write(", ".join(st.session_state.jd_data.get("required_skills", [])) or "Not specified")
        with pref:
            st.write("Preferred Skills")
            st.write(", ".join(st.session_state.jd_data.get("preferred_skills", [])) or "Not specified")
        st.write("Experience Requirement")
        st.write(st.session_state.jd_data.get("experience_requirement", "Not specified"))

        if st.button("Generate Rankings", key="generate_rankings", type="primary"):
            try:
                with st.spinner("Calculating candidate rankings..."):
                    run_ranking()
                st.success("Rankings generated successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Ranking failed: {exc}")


def get_filtered_rankings() -> List[Dict[str, Any]]:
    data = list(st.session_state.ranking_data)
    query = st.text_input("Filter by candidate name or resume filename", key="ranking_filter").strip().lower()
    min_score = st.slider("Minimum match score", 0, 100, 0, key="min_score_filter")
    top_n_label = st.selectbox(
        "Show Top Candidates",
        [f"Top {value}" for value in range(5, 55, 5)],
        index=1,
        key="top_candidates_filter",
    )
    top_n = int(top_n_label.split()[-1])

    if query:
        data = [
            item for item in data
            if query in item.get("candidate_name", "").lower() or query in item.get("pdf_file", "").lower()
        ]
    data = [item for item in data if item.get("final_score", 0) >= min_score]
    data.sort(key=lambda item: item.get("final_score", 0), reverse=True)

    return data[:top_n]


def select_candidate(candidate: Dict[str, Any]) -> None:
    st.session_state.selected_candidate = candidate
    st.session_state.show_resume_pdf = False
    st.rerun()


def render_rankings() -> None:
    if not st.session_state.ranking_done:
        return

    section_header("Section 4: Candidate Rankings", "Filter and open details from the highest-ranked candidates.")
    filtered = get_filtered_rankings()

    if not filtered:
        st.warning("No candidates match the current filters.")
        return

    for candidate in filtered:
        name_col, score_col, resume_col = st.columns([3, 1, 2])
        with name_col:
            if st.button(candidate.get("candidate_name", "N/A"), key=f"name_{candidate.get('rank')}_{candidate.get('pdf_file')}"):
                select_candidate(candidate)
        with score_col:
            st.metric("Match Score", f"{candidate.get('final_score', 0):.1f}%")
        with resume_col:
            if st.button(candidate.get('pdf_file', 'Resume'), key=f"resume_{candidate.get('rank')}_{candidate.get('pdf_file')}"):
                select_candidate(candidate)


def find_candidate_source(candidate: Dict[str, Any]) -> Dict[str, Any]:
    pdf_file = candidate.get("pdf_file", "")
    for item in st.session_state.candidates:
        if item.get("pdf_file") == pdf_file:
            merged = dict(item)
            merged.update(candidate)
            return merged
    return candidate


def render_pdf_viewer(pdf_path: Path) -> None:
    pdf_bytes = pdf_path.read_bytes()
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{encoded}" width="100%" height="720" type="application/pdf"></iframe>',
        unsafe_allow_html=True,
    )


def render_candidate_details() -> None:
    if not st.session_state.selected_candidate:
        return

    candidate = find_candidate_source(st.session_state.selected_candidate)
    section_header("Candidate Details")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Candidate Name", candidate.get("candidate_name", "N/A"))
    with col2:
        st.metric("Email Address", candidate.get("email") or "N/A")
    with col3:
        st.metric("Contact Number", validated_candidate_phone(candidate) or "N/A")

    st.write("Skills")
    st.write(", ".join(candidate.get("skills", [])[:20]) or "No skills extracted.")

    bottom_left, bottom_right = st.columns([1, 4])
    with bottom_left:
        if st.button("Open Resume", key="open_resume", type="primary"):
            st.session_state.show_resume_pdf = True
    with bottom_right:
        if st.button("Close Details", key="close_candidate_details"):
            st.session_state.selected_candidate = None
            st.session_state.show_resume_pdf = False
            if "resume" in st.query_params:
                del st.query_params["resume"]
            st.rerun()

    if st.session_state.show_resume_pdf:
        pdf_file = candidate.get("pdf_file", "")
        pdf_path = st.session_state.session_manager.temp_resumes_dir / pdf_file
        if pdf_path.exists():
            render_pdf_viewer(pdf_path)
        else:
            st.error("Resume file not found. It may have been cleared from the session.")


def main() -> None:
    apply_resume_query_param()
    render_top_bar()
    render_sidebar()
    if st.session_state.get("last_error"):
        st.error(st.session_state.last_error)
    render_resume_upload()
    render_resume_processing()
    render_job_description()
    render_rankings()
    render_candidate_details()


if __name__ == "__main__":
    main()
