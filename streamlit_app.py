
import hashlib
import streamlit as st

from rag_main import process_document, answer_question


# -----------------------------------------
# 1. Page configuration
# -----------------------------------------

st.set_page_config(
    page_title="Technical Documentation Assistant",
    page_icon="📚",
    layout="wide"
)


# -----------------------------------------
# 2. Professional UI styling
# -----------------------------------------

st.markdown(
    """
    <style>
    /* Page background */
    .stApp {
        background-color: #f1f3f7;
        color: #374151;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Headings */
    .stApp h1 {
        color: #303846 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    .stApp h2,
    .stApp h3 {
        color: #3c4555 !important;
        font-weight: 650 !important;
    }

    /* Normal text */
    .stApp p,
    .stApp li {
        color: #4b5563;
    }

    /* Subtitle */
    .app-subtitle {
        color: #737b8b !important;
        font-size: 1rem;
        margin-top: -0.4rem;
        margin-bottom: 1.4rem;
    }

    /* Captions */
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: #737b8b !important;
        opacity: 1 !important;
    }

    /* -------------------------------------
       Standard buttons
    ------------------------------------- */

    .stButton > button {
        background-color: #e3e6ee !important;
        color: #303846 !important;
        border: 1px solid #c5cad6 !important;
        border-radius: 9px;
        min-height: 43px;
        font-weight: 600 !important;
        opacity: 1 !important;
        transition: background-color 0.2s ease;
    }

    .stButton > button p,
    .stButton > button span {
        color: #303846 !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    .stButton > button:hover {
        background-color: #d7dce7 !important;
        border-color: #aeb6c6 !important;
        color: #252c39 !important;
    }

    /* -------------------------------------
       Primary buttons
    ------------------------------------- */

    .stButton > button[kind="primary"] {
        background-color: #5b5fc7 !important;
        color: #ffffff !important;
        border: none !important;
    }

    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #4d51ad !important;
        color: #ffffff !important;
    }

    /* -------------------------------------
       File uploader
    ------------------------------------- */

    div[data-testid="stFileUploader"] {
        background-color: #f6f7fa;
        border: 1px dashed #c8cdd8;
        border-radius: 11px;
        padding: 0.7rem;
    }

    div[data-testid="stFileUploader"] section {
        background-color: transparent;
    }

    /* Browse files button */
    [data-testid="stFileUploader"] button {
        background-color: #e3e6ee !important;
        color: #303846 !important;
        border: 1px solid #c5cad6 !important;
        border-radius: 8px !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }

    [data-testid="stFileUploader"] button p,
    [data-testid="stFileUploader"] button span {
        color: #303846 !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background-color: #d7dce7 !important;
        border-color: #aeb6c6 !important;
    }

    /* Upload instructions and labels */
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] section span,
    [data-testid="stFileUploader"] section small,
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] label p {
        color: #4b5563 !important;
        opacity: 1 !important;
    }

    /* -------------------------------------
       Question input
    ------------------------------------- */

    div[data-testid="stTextInput"] input {
        color: #303846 !important;
        background-color: #f8f9fb !important;
        border: 1px solid #cbd1dd !important;
        border-radius: 9px;
        min-height: 43px;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #858d9c !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #8589d5 !important;
        box-shadow: 0 0 0 1px #8589d5 !important;
    }

    /* Input labels */
    .stTextInput label,
    .stFileUploader label {
        color: #3c4555 !important;
    }

    /* -------------------------------------
       Status messages
    ------------------------------------- */

    div[data-testid="stAlert"] {
        border-radius: 9px;
    }

    /* Dividers */
    hr {
        border-color: #dfe3ea;
    }

    /* Responsive layout */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem;
        }

        .stApp h1 {
            font-size: 1.65rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------------------
# 3. Session state
# -----------------------------------------

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "processed_signature" not in st.session_state:
    st.session_state.processed_signature = None

if "document_name" not in st.session_state:
    st.session_state.document_name = None

if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0


# -----------------------------------------
# 4. App heading
# -----------------------------------------

st.title("📚 Technical Documentation Assistant")

st.markdown(
    '<div class="app-subtitle">'
    'Upload your documentation and get answers grounded in its content.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# -----------------------------------------
# 5. Two-column layout
# -----------------------------------------

left_col, right_col = st.columns(
    [1, 2],
    gap="large"
)


# -----------------------------------------
# LEFT COLUMN: Document upload
# -----------------------------------------

with left_col:

    st.subheader("📄 Knowledge Source")

    st.write(
        "Upload a PDF or TXT document to use as your knowledge source."
    )

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "txt"],
        help="Text-based PDFs and TXT files are supported."
    )

    if uploaded_file is not None:

        file_bytes = uploaded_file.getvalue()

        current_signature = (
            uploaded_file.name,
            hashlib.sha256(file_bytes).hexdigest()
        )

        current_document_name = uploaded_file.name

        st.caption(f"Selected: {uploaded_file.name}")

    else:

        file_bytes = None
        current_signature = "default-document"
        current_document_name = "documents/rag_notes.txt"

        st.caption("Using the default sample document.")

    # Check whether the selected document is processed
    document_is_ready = (
        st.session_state.vector_store is not None
        and st.session_state.processed_signature == current_signature
    )

    if document_is_ready:

        st.success("Document ready")

        st.caption(
            f"{st.session_state.chunk_count} text chunks indexed"
        )

    else:

        st.info("Process the document before asking questions.")

    if st.button(
        "⚙️ Process Document",
        type="primary",
        use_container_width=True
    ):

        try:

            with st.spinner("Processing document..."):

                vector_store, chunk_count = process_document(
                    file_name=(
                        uploaded_file.name
                        if uploaded_file is not None
                        else None
                    ),
                    file_bytes=file_bytes
                )

                st.session_state.vector_store = vector_store

                st.session_state.processed_signature = (
                    current_signature
                )

                st.session_state.document_name = (
                    current_document_name
                )

                st.session_state.chunk_count = chunk_count

            st.success("Document processed successfully!")

            st.rerun()

        except Exception as error:

            st.error(f"Processing failed: {error}")

    st.divider()

    st.caption("Supported formats: PDF and TXT")

    st.caption(
        "Process the document again whenever you select a different file."
    )


# -----------------------------------------
# RIGHT COLUMN: AI assistant
# -----------------------------------------

with right_col:

    st.subheader("💬 AI Assistant")

    st.write(
        "Ask a question about the document you have processed."
    )

    question = st.text_input(
        "Your question",
        placeholder="e.g. What are embeddings?",
        label_visibility="collapsed"
    )

    ask_button = st.button(
        "✦ Get Answer",
        type="primary",
        use_container_width=True
    )

    if ask_button:

        # Check that the selected document is processed
        document_is_ready = (
            st.session_state.vector_store is not None
            and st.session_state.processed_signature
            == current_signature
        )

        if not question.strip():

            st.warning("Please enter a question.")

        elif not document_is_ready:

            st.warning(
                "Please process the currently selected document first."
            )

        else:

            try:

                with st.spinner(
                    "Searching document and generating answer..."
                ):

                    answer, sources = answer_question(
                        st.session_state.vector_store,
                        question.strip()
                    )

                st.markdown("### Answer")
                st.markdown(answer)

                # Display source citations
                if sources:

                    st.markdown("### 📚 Sources")

                    for source in sources:

                        source_name = source["source"]
                        page_number = source["page"]
                        labels = ", ".join(source["labels"])

                        if page_number is not None:

                            st.markdown(
                                f"- **{source_name}** — "
                                f"PDF page {page_number} "
                                f"(`{labels}`)"
                            )

                        else:

                            st.markdown(
                                f"- **{source_name}** "
                                f"(`{labels}`)"
                            )

                else:

                    st.caption("No source chunks were retrieved.")

            except Exception as error:

                st.error(
                    f"Could not generate an answer: {error}"
                )