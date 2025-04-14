import streamlit as st
import requests
import json

# --- Streamlit App Layout ---
st.set_page_config(page_title="CAFBrain Generator", layout="centered")
st.title("🧠 CAFBrain: Smart Document Generator")
st.markdown("Generate grant proposals, blogs, and social media posts from existing CAFB content.")

# --- Input Section ---
prompt = st.text_area(
    "📌 Enter your prompt",
    placeholder="e.g., Generate a 5-paragraph blog post about SNAP barriers"
)

col1, col2 = st.columns(2)
with col1:
    content_type = st.selectbox(
        "📝 Content Type",
        ["grant", "blog_post", "social_media_post"],
        index=1
    )
with col2:
    tone = st.selectbox(
        "🎭 Tone",
        ["formal", "casual", "persuasive", "informative"],
        index=0
    )

submit = st.button("🔍 Generate Content")

# --- Output Section ---
if submit and prompt:
    with st.spinner("Generating content, please wait..."):
        api_url = "http://localhost:8000/generate"  # Replace with deployed URL if needed

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

                st.subheader("📝 Generated Output")
                st.text_area("You can edit the output below:", value=generated_text, height=300)

                st.subheader("📚 Sources Used")
                for s in sources:
                    st.markdown(f"**{s['title']}**  \n*{s['source']}*  \nScore: {s['score']:.2f}")
                    st.caption(s["text"][:400] + "...")

                st.download_button("💾 Download Output", generated_text, file_name="cafbrain_output.txt")

            else:
                st.error(f"❌ Backend Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"⚠️ Request failed: {e}")
