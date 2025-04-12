import streamlit as st
import requests

st.set_page_config(page_title="CAFBrain", layout="wide")

st.title("🧠 CAFBrain Content Generator")

# Step 1: Prompt input
user_prompt = st.text_area("📝 Describe what content you want generated", height=200)

# Step 2: Select tone
tone = st.selectbox("🎭 Tone", ["Formal", "Casual", "Inspirational", "Upbeat"])

# Step 3: Select content type
content_type = st.selectbox("📄 Output Format", ["Grant Proposal", "Blog Post", "Social Media Caption"])

# Submit button
if st.button("🚀 Generate Content"):
    with st.spinner("Generating..."):
        response = requests.post("http://localhost:8000/generate", json={
            "prompt": user_prompt,
            "tone": tone,
            "content_type": content_type
        })
        if response.ok:
            result = response.json()["result"]
            st.text_area("✍️ Generated Content", value=result, height=400)
        else:
            st.error("Failed to generate content. Please check the backend.")
