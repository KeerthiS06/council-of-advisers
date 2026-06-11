import os
import sys

# Ensure the local code.py is found before the stdlib 'code' module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import code as yt_scraper
import streamlit as st
from gemini import ask_gemini, DEFAULT_GEMINI_API_KEY

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Transcript Fetcher",
    page_icon="🎬",
    layout="centered",
)

# ── Session state defaults ─────────────────────────────────────────────────────
if "transcript_file_path" not in st.session_state:
    st.session_state.transcript_file_path = None
if "gemini_response" not in st.session_state:
    st.session_state.gemini_response = None

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🎬 YouTube Transcript Fetcher")
st.markdown(
    "Fetch and save transcripts for **every video** on a YouTube channel "
    "into a single text file."
)
st.divider()

# ── Sidebar – API keys & advanced options ─────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    api_key = st.text_input(
        "YouTube Data API Key",
        value=yt_scraper.DEFAULT_API_KEY,
        type="password",
        help="Get yours at https://console.cloud.google.com/",
    )

    gemini_api_key = st.text_input(
        "Gemini API Key",
        value=DEFAULT_GEMINI_API_KEY,
        type="password",
        help="Your Google Gemini API key.",
    )

    output_dir = st.text_input(
        "Output Directory",
        value="transcripts",
        help="Folder where the transcript file will be saved.",
    )

    st.divider()
    st.subheader("🧪 Test Mode")
    test_mode = st.toggle(
        "Enable Test Mode",
        value=False,
        help="Skip the full API call and use a single hard-coded test video.",
    )
    if test_mode:
        test_video_id = st.text_input(
            "Test Video ID",
            value=yt_scraper.DEFAULT_TEST_VIDEO["video_id"],
            help="YouTube video ID to use in test mode.",
        )
    else:
        test_video_id = yt_scraper.DEFAULT_TEST_VIDEO["video_id"]

# ── Main form ──────────────────────────────────────────────────────────────────
with st.form("fetch_form"):
    col1, col2 = st.columns(2)

    with col1:
        channel_id = st.text_input(
            "Channel ID",
            placeholder=yt_scraper.DEFAULT_CHANNEL_ID,
            help="The channel's unique identifier (starts with 'UC…').",
        )

    with col2:
        channel_name = st.text_input(
            "Channel Name",
            placeholder=yt_scraper.DEFAULT_CHANNEL_NAME,
            help="Used as the output filename (e.g. 'Buddha Motivation').",
        )

    submitted = st.form_submit_button(
        "🚀 Fetch Transcripts", use_container_width=True, type="primary"
    )

# ── Execution ──────────────────────────────────────────────────────────────────
if submitted:
    errors = []
    if not channel_id.strip():
        errors.append("**Channel ID** is required.")
    if not channel_name.strip():
        errors.append("**Channel Name** is required.")
    if not api_key.strip():
        errors.append("**YouTube Data API Key** is required.")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    st.divider()
    status_box = st.empty()
    progress_bar = st.progress(0, text="Starting…")
    log_expander = st.expander("📋 Live Logs", expanded=True)
    log_placeholder = log_expander.empty()
    log_lines: list[str] = []

    def progress_callback(current: int, total: int, message: str) -> None:
        fraction = current / total if total > 0 else 0
        progress_bar.progress(fraction, text=f"{current}/{total} – {message[:80]}")
        log_lines.append(message)
        log_placeholder.code("\n".join(log_lines), language=None)

    status_box.info("⏳ Fetching transcripts — this may take a while for large channels…")
    try:
        test_video = {"title": "Test Video", "video_id": test_video_id}

        file_path = yt_scraper.run_pipeline(
            channel_id=channel_id.strip(),
            channel_name=channel_name.strip(),
            api_key=api_key.strip(),
            output_dir=output_dir.strip() or "transcripts",
            test_mode=test_mode,
            test_video=test_video if test_mode else None,
            progress_callback=progress_callback,
        )

        progress_bar.progress(1.0, text="Done!")
        status_box.success(f"✅ All transcripts saved to **`{file_path}`**")

        # Persist the file path so the Q&A section stays visible
        st.session_state.transcript_file_path = file_path
        st.session_state.gemini_response = None  # reset any previous answer

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as fh:
                file_bytes = fh.read()

            st.download_button(
                label="⬇️ Download Transcript File",
                data=file_bytes,
                file_name=os.path.basename(file_path),
                mime="text/plain",
                use_container_width=True,
            )

    except Exception as exc:
        progress_bar.empty()
        status_box.error(f"❌ An error occurred: {exc}")
        st.exception(exc)

# ── Q&A Section (shown once a transcript has been fetched) ─────────────────────
if st.session_state.transcript_file_path:
    st.divider()
    st.subheader("💬 Ask Gemini About the Transcripts")

    with st.form("qa_form"):
        user_question = st.text_area(
            "Your Question",
            placeholder="e.g. What are the key teachings discussed across these videos?",
            height=100,
        )
        ask_submitted = st.form_submit_button(
            "✨ Ask Gemini", use_container_width=True, type="primary"
        )

    if ask_submitted:
        if not user_question.strip():
            st.warning("Please enter a question before submitting.")
        elif not gemini_api_key.strip():
            st.error("A **Gemini API Key** is required. Add it in the sidebar.")
        else:
            with st.spinner("🤖 Gemini is thinking…"):
                try:
                    answer = ask_gemini(
                        file_path=st.session_state.transcript_file_path,
                        user_question=user_question.strip(),
                        api_key=gemini_api_key.strip(),
                    )
                    st.session_state.gemini_response = answer
                except Exception as exc:
                    st.error(f"❌ Gemini error: {exc}")
                    st.exception(exc)

    if st.session_state.gemini_response:
        st.markdown("**✨ Gemini's Response:**")
        st.markdown(st.session_state.gemini_response)
