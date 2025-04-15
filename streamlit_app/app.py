import streamlit as st
import requests
from fpdf import FPDF
from docx import Document
from pptx import Presentation
from pptx.util import Inches
from io import BytesIO

# --- Streamlit App Layout ---
st.set_page_config(page_title="CAFBrain Generator", layout="centered")
st.title("🧠 CAFBrain: Smart Document Generator")
st.markdown("Generate, edit, save, and download grant proposals, blogs, social media posts, presentations, Canva visuals, and YouTube scripts.")

# --- Export Helpers ---
def generate_pdf(text: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='ignore')
    return BytesIO(pdf_bytes)

def generate_txt(text: str) -> BytesIO:
    return BytesIO(text.encode('utf-8'))

def generate_docx(text: str) -> BytesIO:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_ppt(text: str) -> BytesIO:
    prs = Presentation()
    for block in text.split("\n\n"):
        lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
        if not lines:
            continue
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = lines[0].replace("Slide Title:", "").strip()
        content = "\n".join(line.strip("-• ") for line in lines[1:])
        slide.placeholders[1].text = content
    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# --- Input Section ---
prompt = st.text_area("📌 Enter your prompt", placeholder="e.g., Create a Canva post about SNAP access")

format_options = {
    "Grant Proposal": "grant",
    "Blog Post": "blog_post",
    "Social Media Post": "social_media_post",
    "Presentation Slides": "presentation",
    "Canva Visual Post": "canva_post",
    "YouTube Video Script": "video_script"
}
selected_label = st.selectbox("📝 Content Type", list(format_options.keys()), index=1)
content_type = format_options[selected_label]

tone = st.selectbox("🎭 Tone", ["formal", "casual", "persuasive", "informative"], index=0)

submit = st.button("🔍 Generate Content")

# --- Output Section ---
if submit and prompt:
    with st.spinner("Generating content, please wait..."):
        api_url = "http://localhost:8000/generate"

        payload = {
            "query": prompt,
            "top_k": 5,
            "format": content_type,
            "tone": tone
        }

        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                generated_text = data["answer"]
                sources = data["sources"]

                # Initialize session state
                if "edited_output" not in st.session_state or st.session_state.edited_output != generated_text:
                    st.session_state.edited_output = generated_text
                    st.session_state.edit_history = [generated_text]
                    st.session_state.redo_stack = []
                    st.session_state.saved_output = ""

                st.subheader("📝 Generated Output")

                # Editable text box
                edited_text = st.text_area(
                    "Edit your content below:",
                    value=st.session_state.edited_output,
                    height=300,
                    key="editable_output"
                )

                # Track live edits
                if edited_text != st.session_state.edited_output:
                    st.session_state.edit_history.append(st.session_state.edited_output)
                    st.session_state.edited_output = edited_text
                    st.session_state.redo_stack.clear()

                # Undo/Redo/Save Buttons
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("↩️ Undo") and st.session_state.edit_history:
                        st.session_state.redo_stack.append(st.session_state.edited_output)
                        st.session_state.edited_output = st.session_state.edit_history.pop()
                with col2:
                    if st.button("↪️ Redo") and st.session_state.redo_stack:
                        st.session_state.edit_history.append(st.session_state.edited_output)
                        st.session_state.edited_output = st.session_state.redo_stack.pop()
                with col3:
                    if st.button("💾 Save Edit"):
                        st.session_state.saved_output = st.session_state.edited_output
                        st.success("✅ Edit saved!")

                # --- Multi-format download options ---
                selected_formats = st.multiselect(
                    "📥 Choose one or more formats to download",
                    ["PDF", "DOCX", "TXT", "PPTX"],
                    default=["PDF"]
                )

                for format in selected_formats:
                    output_to_download = st.session_state.get("saved_output", st.session_state.edited_output)
                    file_data = None
                    file_name = "cafbrain_output"
                    mime_type = "application/octet-stream"

                    if format == "PDF":
                        file_data = generate_pdf(output_to_download)
                        file_name += ".pdf"
                        mime_type = "application/pdf"
                    elif format == "DOCX":
                        file_data = generate_docx(output_to_download)
                        file_name += ".docx"
                        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    elif format == "TXT":
                        file_data = generate_txt(output_to_download)
                        file_name += ".txt"
                        mime_type = "text/plain"
                    elif format == "PPTX":
                        file_data = generate_ppt(output_to_download)
                        file_name += ".pptx"
                        mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

                    if file_data:
                        st.download_button(
                            f"⬇️ Download {format}",
                            data=file_data,
                            file_name=file_name,
                            mime=mime_type
                        )

                # --- Source chunk display ---
                st.subheader("📚 Sources Used")
                for s in sources:
                    st.markdown(f"**{s['title']}**  \n*{s['source']}*  \nScore: {s['score']:.2f}")
                    st.caption(s["text"][:400] + "...")

            else:
                st.error(f"❌ Backend Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"⚠️ Request failed: {e}")
