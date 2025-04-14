import streamlit as st
import requests
import json
from fpdf import FPDF  # PDF support

# --- Streamlit App Layout ---
st.set_page_config(page_title="CAFBrain Generator", layout="centered")
st.title("🧠 CAFBrain: Smart Document Generator")
st.markdown("Generate grant proposals, blogs, social media posts, presentations, Canva visuals, and video scripts from CAFB content.")

# --- PDF Generator Function ---
def generate_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)

    return pdf.output(dest='S').encode('latin-1')

# --- Input Section ---
prompt = st.text_area(
    "📌 Enter your prompt",
    placeholder="e.g., Create a Canva post highlighting barriers to SNAP access"
)

# --- Friendly Labels to Backend Keys ---
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

tone = st.selectbox(
    "🎭 Tone",
    ["formal", "casual", "persuasive", "informative"],
    index=0
)

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

                # Persist edited output using session state
                if "edited_output" not in st.session_state or st.session_state.edited_output != generated_text:
                    st.session_state.edited_output = generated_text

                st.subheader("📝 Generated Output")
                st.session_state.edited_output = st.text_area(
                    "You can edit the output below:",
                    value=st.session_state.edited_output,
                    height=300,
                    key="editable_output"
                )

                st.download_button(
                    "📄 Download as PDF",
                    data=generate_pdf(st.session_state.edited_output),
                    file_name="cafbrain_output.pdf",
                    mime="application/pdf"
                )

                # Display sources
                st.subheader("📚 Sources Used")
                for s in sources:
                    st.markdown(f"**{s['title']}**  \n*{s['source']}*  \nScore: {s['score']:.2f}")
                    st.caption(s["text"][:400] + "...")

            else:
                st.error(f"❌ Backend Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"⚠️ Request failed: {e}")
