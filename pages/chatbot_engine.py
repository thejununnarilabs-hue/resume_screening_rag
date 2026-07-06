"""Dedicated Candidate Intelligence Assistant page."""

from datetime import datetime
import html
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit as st

from config import (
    CHATBOT_NUM_PREDICT,
    CHATBOT_TEMPERATURE,
    EVALUATION_EXPORT_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    RETRIEVAL_TOP_K,
)
from core.chatbot import AI_ASSISTANT_UNAVAILABLE_MESSAGE, OllamaChatbot
from core.evaluation import EvaluationFramework
from core.retrieval import RetrievalEngine


st.set_page_config(
    page_title="Candidate Intelligence Assistant",
    page_icon="Chat",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
    .block-container {
        max-width: 1180px;
        padding-top: 1.25rem;
        padding-bottom: 5rem;
    }
    section[data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e5e7eb;
    }
    .assistant-header {
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 0.75rem;
        margin-bottom: 1rem;
    }
    .assistant-header h1 {
        font-size: 1.45rem;
        margin: 0;
    }
    .assistant-subtitle {
        color: #64748b;
        margin-top: 0.2rem;
    }
    .chat-shell {
        min-height: 66vh;
        max-height: 72vh;
        overflow-y: auto;
        padding: 0.5rem 0.25rem 1.25rem;
        scroll-behavior: smooth;
    }
    .empty-chat {
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        border-radius: 8px;
        padding: 1rem;
        color: #475569;
    }
    div[data-testid="stSidebar"] button {
        border-radius: 7px;
    }
    .history-title {
        color: #475569;
        font-size: 0.82rem;
        font-weight: 700;
        margin: 1rem 0 0.35rem;
        text-transform: uppercase;
    }
    .history-panel {
        max-height: 54vh;
        overflow-y: auto;
        padding-right: 0.2rem;
    }
    div[data-testid="stChatMessage"] button {
        background: transparent;
        border: 0;
        box-shadow: none;
        color: #2563eb;
        display: inline;
        font-weight: 600;
        min-height: 0;
        padding: 0;
        text-align: left;
        text-decoration: underline;
        width: auto;
    }
    div[data-testid="stChatMessage"] button:hover {
        background: transparent;
        border: 0;
        color: #1d4ed8;
    }
</style>
""",
    unsafe_allow_html=True,
)


def create_chat(title: str = "New chat") -> str:
    chat_id = uuid4().hex
    st.session_state.chat_sessions[chat_id] = {
        "title": title,
        "messages": [],
        "created_at": datetime.now().isoformat(),
    }
    st.session_state.active_chat_id = chat_id
    persist_chat_state()
    return chat_id


def persist_chat_state() -> None:
    session_manager = st.session_state.get("session_manager")
    if session_manager is not None:
        session_manager.save_chat_sessions(
            st.session_state.get("chat_sessions", {}),
            st.session_state.get("active_chat_id"),
        )


def ensure_chat_state() -> None:
    if "chat_sessions" not in st.session_state or not isinstance(st.session_state.chat_sessions, dict):
        session_manager = st.session_state.get("session_manager")
        saved = session_manager.load_chat_sessions() if session_manager is not None else {}
        st.session_state.chat_sessions = saved.get("chat_sessions", {}) if isinstance(saved, dict) else {}
        st.session_state.active_chat_id = saved.get("active_chat_id") if isinstance(saved, dict) else None

    if "active_chat_id" not in st.session_state:
        st.session_state.active_chat_id = None

    if not st.session_state.chat_sessions:
        create_chat()
    elif st.session_state.active_chat_id not in st.session_state.chat_sessions:
        st.session_state.active_chat_id = next(iter(st.session_state.chat_sessions))


def get_active_chat() -> Dict[str, Any]:
    ensure_chat_state()
    return st.session_state.chat_sessions[st.session_state.active_chat_id]


def delete_active_chat() -> None:
    ensure_chat_state()
    active_chat_id = st.session_state.active_chat_id
    if active_chat_id in st.session_state.chat_sessions:
        del st.session_state.chat_sessions[active_chat_id]

    if st.session_state.chat_sessions:
        st.session_state.active_chat_id = next(iter(st.session_state.chat_sessions))
    else:
        create_chat()
    persist_chat_state()


def ensure_chatbot() -> OllamaChatbot:
    chatbot = st.session_state.get("chatbot")
    if chatbot is None:
        chatbot = OllamaChatbot(
            model_name=OLLAMA_MODEL,
            ollama_base_url=OLLAMA_BASE_URL,
            warm_up=False,
        )
        st.session_state.chatbot = chatbot
    return chatbot


def ensure_evaluation_framework() -> EvaluationFramework:
    framework = st.session_state.get("evaluation_framework")
    if framework is None:
        framework = EvaluationFramework(EVALUATION_EXPORT_PATH)
        st.session_state.evaluation_framework = framework
    return framework


def ensure_retrieval_engine() -> Optional[RetrievalEngine]:
    chroma_manager = st.session_state.get("chroma_manager")
    embedding_model = st.session_state.get("embedding_model")
    ranking_data = st.session_state.get("ranking_data", [])

    if chroma_manager is None or embedding_model is None:
        return None

    try:
        if getattr(chroma_manager, "collection", None) is None:
            chroma_manager.create_collection()
    except Exception as exc:
        st.session_state.last_error = f"Could not access ChromaDB collection: {exc}"
        return None

    retrieval_engine = st.session_state.get("retrieval_engine")
    if retrieval_engine is None or getattr(retrieval_engine, "ranking_data", None) != ranking_data:
        retrieval_engine = RetrievalEngine(chroma_manager, embedding_model, ranking_data)
        st.session_state.retrieval_engine = retrieval_engine
    else:
        retrieval_engine.ranking_data = ranking_data

    return retrieval_engine


def pipeline_status() -> Dict[str, Any]:
    candidates = st.session_state.get("candidates", [])
    ranking_data = st.session_state.get("ranking_data", [])
    chroma_manager = st.session_state.get("chroma_manager")
    embedding_model = st.session_state.get("embedding_model")

    issues = []
    if not candidates:
        issues.append("Upload and process resumes on the dashboard before asking candidate questions.")
    if chroma_manager is None or embedding_model is None or not st.session_state.get("resume_processing_done", False):
        issues.append("Resume embeddings are not ready yet. Run resume processing on the dashboard.")
    if not ranking_data:
        issues.append("Generate rankings on the dashboard to enable ranking and comparison questions.")

    return {
        "ready": not issues,
        "issues": issues,
        "candidate_count": len(candidates),
        "ranking_count": len(ranking_data),
    }


def enhance_chatbot_response(response: str, ranking_data: List[Dict[str, Any]]) -> str:
    enhanced = response
    for candidate in ranking_data:
        name = candidate.get("candidate_name", "")
        resume = candidate.get("pdf_file", "")
        if not name or not resume:
            continue

        resume_link = html.escape(resume)
        enhanced = re.sub(
            rf"\(`?{re.escape(resume)}`?\)",
            f"({resume_link})",
            enhanced,
            flags=re.IGNORECASE,
        )

        name_before_resume = rf"(?<![\w*]){re.escape(name)}(?![\w.-])(?=\s*\({re.escape(resume_link)}\))"
        if re.search(name_before_resume, enhanced, flags=re.IGNORECASE):
            enhanced = re.sub(
                name_before_resume,
                f"**{html.escape(name)}**",
                enhanced,
                count=1,
                flags=re.IGNORECASE,
            )
            continue

        if resume_link in enhanced and re.search(rf"\*\*{re.escape(name)}\*\*\s*\(", enhanced):
            continue

        enhanced = re.sub(
            rf"(?<![\w]){re.escape(name)}(?![\w.-])",
            f"**{html.escape(name)}** ({resume_link})",
            enhanced,
            count=1,
            flags=re.IGNORECASE,
        )
    return enhanced


def resume_links_for_response(content: str, ranking_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Find mentioned resumes so Streamlit-native navigation can open them."""
    plain_content = re.sub(r"<[^>]+>", " ", content or "")
    plain_content = html.unescape(plain_content).lower()
    links = []
    seen = set()

    for candidate in ranking_data:
        name = str(candidate.get("candidate_name", "")).strip()
        resume = str(candidate.get("pdf_file", "")).strip()
        if not name or not resume or resume.lower() in seen:
            continue

        if name.lower() in plain_content or resume.lower() in plain_content:
            seen.add(resume.lower())
            links.append({
                "candidate_name": name,
                "pdf_file": resume,
            })

    return links


def open_resume_from_chat(pdf_file: str) -> None:
    """Open a resume using Streamlit state navigation, not a browser reload."""
    target = str(pdf_file or "").replace("\\", "/").split("/")[-1].strip().lower()
    for candidate in st.session_state.get("ranking_data", []) + st.session_state.get("candidates", []):
        candidate_file = str(candidate.get("pdf_file", "")).replace("\\", "/").split("/")[-1].strip().lower()
        if candidate_file == target:
            st.session_state.selected_candidate = candidate
            st.session_state.show_resume_pdf = True
            st.switch_page("app.py")
            return

    st.session_state.last_error = f"Could not open resume '{pdf_file}'. It was not found in the current session."


def render_assistant_message(content: str, resume_links: List[Dict[str, str]], message_index: int) -> None:
    """Render assistant text with the resume link beside the candidate name."""
    rendered = content
    inline_links = []

    for link in resume_links:
        candidate_name = link.get("candidate_name", "")
        pdf_file = link.get("pdf_file", "")
        if not candidate_name or not pdf_file:
            continue

        rendered = re.sub(
            rf"\n?\s*-?\s*Resume File Name:\s*`?{re.escape(pdf_file)}`?",
            "",
            rendered,
            flags=re.IGNORECASE,
        )
        rendered = re.sub(
            rf"\(\s*`?{re.escape(pdf_file)}`?\s*\)",
            "",
            rendered,
            flags=re.IGNORECASE,
        )

        name_match = re.search(
            rf"-?\s*Name:\s*\**{re.escape(candidate_name)}\**",
            rendered,
            flags=re.IGNORECASE,
        )
        if name_match:
            inline_links.append({
                "name_start": name_match.start(),
                "insert_after": name_match.end(),
                "candidate_name": candidate_name,
                "pdf_file": pdf_file,
            })

    if not inline_links:
        st.markdown(rendered, unsafe_allow_html=True)
        return

    inline_links.sort(key=lambda item: item["name_start"])
    cursor = 0
    for index, link in enumerate(inline_links):
        before = rendered[cursor:link["name_start"]]
        name_text = rendered[link["name_start"]:link["insert_after"]]
        next_start = inline_links[index + 1]["name_start"] if index + 1 < len(inline_links) else len(rendered)
        after = rendered[link["insert_after"]:next_start]

        if before.strip():
            st.markdown(before, unsafe_allow_html=True)

        name_col, file_col = st.columns([0.28, 0.72], gap="small")
        with name_col:
            st.markdown(name_text, unsafe_allow_html=True)
        with file_col:
            if st.button(
                f"({link['pdf_file']})",
                key=f"chat_resume_{message_index}_{index}_{link['pdf_file']}",
                help=f"Open {link['candidate_name']} on the resume details page",
            ):
                open_resume_from_chat(link["pdf_file"])
        if after.strip():
            st.markdown(after, unsafe_allow_html=True)
        cursor = next_start


def make_chat_title(user_input: str) -> str:
    title = " ".join(user_input.strip().split())
    return title[:48] + ("..." if len(title) > 48 else "")


def record_chat_evaluation(question: str, response: str, context: Dict[str, Any]) -> None:
    try:
        framework = ensure_evaluation_framework()
        retrieved_docs = context.get("retrieved_documents", [])

        ground_truth_qa = st.session_state.get("ground_truth_qa", [])
        session_manager = st.session_state.get("session_manager")
        if not ground_truth_qa and session_manager is not None:
            ground_truth_qa = session_manager.load_latest_ground_truth()

        ground_truth = framework.find_ground_truth_for_question(question, ground_truth_qa)
        precision_recall = framework.calculate_answer_precision_recall(response, ground_truth, k=5)
        if not ground_truth:
            precision_recall = framework.calculate_precision_recall(retrieved_docs, retrieved_docs, k=5)

        faithfulness = framework.evaluate_faithfulness(response, retrieved_docs)
        relevancy = framework.evaluate_answer_relevancy(question, response)
        ranking_quality = framework.evaluate_ranking_quality(response, context.get("ranking_data", []))
        framework.record_evaluation(
            timestamp=datetime.now().isoformat(),
            question=question,
            ground_truth=ground_truth,
            generated_answer=response,
            precision_k=precision_recall.get("precision_at_k", 0.0),
            recall_k=precision_recall.get("recall_at_k", 0.0),
            faithfulness=faithfulness,
            relevancy=relevancy,
            ranking_quality=ranking_quality,
        )
    except Exception as exc:
        st.session_state.last_error = f"Chat evaluation logging failed: {exc}"


def render_sidebar() -> None:
    with st.sidebar:
        st.header("Assistant")
        if st.button("Back to Dashboard", use_container_width=True):
            st.switch_page("app.py")

        st.divider()

        if st.button("New Chat", type="primary", use_container_width=True):
            create_chat()
            st.rerun()

        if st.button("Delete Current Chat", use_container_width=True):
            delete_active_chat()
            st.rerun()

        st.divider()
        st.markdown('<div class="history-title">Chat History</div>', unsafe_allow_html=True)
        st.markdown('<div class="history-panel">', unsafe_allow_html=True)
        for chat_id, chat in list(st.session_state.chat_sessions.items()):
            title = chat.get("title") or "New chat"
            selected = chat_id == st.session_state.active_chat_id
            label = f"> {title}" if selected else title
            if st.button(label, key=f"chat_history_{chat_id}", use_container_width=True):
                st.session_state.active_chat_id = chat_id
                persist_chat_state()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_pipeline_message(status: Dict[str, Any]) -> None:
    if status["ready"]:
        return

    for issue in status["issues"]:
        st.warning(issue)


def render_conversation(chat: Dict[str, Any]) -> None:
    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
    messages = chat.get("messages", [])

    if not messages:
        st.markdown(
            """
<div class="empty-chat">
Ask about candidate skills, ranking reasons, comparisons, contact details, experience, education, or JD fit after rankings are generated.
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        for message_index, message in enumerate(messages):
            with st.chat_message(message.get("role", "assistant")):
                content = message.get("content", "")
                resume_links = message.get("resume_links") or resume_links_for_response(
                    content,
                    st.session_state.get("ranking_data", []),
                )
                if message.get("role") == "assistant" and resume_links:
                    render_assistant_message(content, resume_links, message_index)
                else:
                    st.markdown(content, unsafe_allow_html=True)

    st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<script>
const bottom = window.parent.document.querySelector('#chat-bottom');
if (bottom) bottom.scrollIntoView({behavior: 'smooth', block: 'end'});
</script>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def answer_question(user_input: str, chat: Dict[str, Any]) -> None:
    retrieval_engine = ensure_retrieval_engine()
    if retrieval_engine is None:
        chat["messages"].append({
            "role": "assistant",
            "content": "I cannot access the resume vector store yet. Please process resumes on the dashboard, then return here.",
        })
        return

    try:
        context = retrieval_engine.build_context_for_answer(user_input, top_k=RETRIEVAL_TOP_K)
        formatted_context = retrieval_engine.format_context_for_llm(context)
    except Exception as exc:
        chat["messages"].append({
            "role": "assistant",
            "content": f"I could not retrieve resume evidence for that question. Details: {exc}",
        })
        return

    if not formatted_context.strip():
        chat["messages"].append({
            "role": "assistant",
            "content": "I could not find enough resume or ranking context to answer that from the current session.",
        })
        return

    response = retrieval_engine.direct_answer(user_input, context)
    if response:
        enhanced = enhance_chatbot_response(response, st.session_state.get("ranking_data", []))
        chat["messages"].append({
            "role": "assistant",
            "content": enhanced,
            "resume_links": resume_links_for_response(enhanced, st.session_state.get("ranking_data", [])),
        })
        persist_chat_state()
        record_chat_evaluation(user_input, response, context)
        return

    chatbot = ensure_chatbot()
    response = chatbot.generate_response(
        user_input,
        formatted_context,
        temperature=CHATBOT_TEMPERATURE,
        num_predict=CHATBOT_NUM_PREDICT,
    )
    if not response:
        chat["messages"].append({
            "role": "assistant",
            "content": AI_ASSISTANT_UNAVAILABLE_MESSAGE,
        })
        persist_chat_state()
        return

    enhanced = enhance_chatbot_response(response, st.session_state.get("ranking_data", []))
    chat["messages"].append({
        "role": "assistant",
        "content": enhanced,
        "resume_links": resume_links_for_response(enhanced, st.session_state.get("ranking_data", [])),
    })
    persist_chat_state()
    record_chat_evaluation(user_input, response, context)


def main() -> None:
    ensure_chat_state()
    ensure_chatbot()
    render_sidebar()

    status = pipeline_status()
    st.markdown(
        """
<div class="assistant-header">
  <h1>Candidate Intelligence Assistant</h1>
  <div class="assistant-subtitle">Ask questions against the current resume corpus, ranking table, and JD analysis.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    render_pipeline_message(status)

    chat = get_active_chat()
    render_conversation(chat)

    user_input = st.chat_input(
        "Ask about ranked candidates...",
        key="candidate_assistant_input",
        disabled=not status["ready"],
    )
    if user_input:
        if not chat.get("messages"):
            chat["title"] = make_chat_title(user_input)

        chat["messages"].append({"role": "user", "content": user_input})
        persist_chat_state()
        with st.spinner("Retrieving evidence and generating answer..."):
            answer_question(user_input, chat)
        st.rerun()


if __name__ == "__main__":
    main()
