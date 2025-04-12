import streamlit as st
import requests
import json
import time 

# --- Streamlit App Layout ---
st.set_page_config(page_title="CAFBrain Generator", layout="centered")
st.title("🧠 CAFBrain: Smart Document Generator")
st.markdown("Generate grant proposals, blogs, and social media posts from existing CAFB content.")

# --- Input Section ---
prompt = st.text_area("📌 Enter your prompt", placeholder="e.g., Generate a 5-paragraph blog post about SNAP barriers")

col1, col2 = st.columns(2)
with col1:
    content_type = st.selectbox("📝 Content Type", ["Grant Proposal", "Blog Post", "Social Media Post"])
with col2:
    tone = st.selectbox("🎭 Tone", ["Formal", "Casual", "Persuasive", "Informative"])

submit = st.button("🔍 Generate Content")

# --- Output Section ---
if submit and prompt:
    with st.spinner("Generating content, please wait..."):
        # Placeholder backend URL (to be updated when backend is ready)
        api_url = "http://localhost:8000/generate"

        # Payload to send to backend
        payload = {
            "prompt": prompt,
            "tone": tone.lower(),
            "content_type": content_type.lower().replace(" ", "_")
        }

        # try:
        #     response = requests.post(api_url, json=payload)
        #     if response.status_code == 200:
        #         result_text = response.json().get("generated_text", "")
        #     else:
        #         result_text = f"Error: {response.status_code} - {response.text}"
        # except requests.exceptions.RequestException as e:
        #     result_text = f"Request failed: {str(e)}"
        
        #Mock output
        time.sleep(1)
        result_text = f"""[Mocked Output]
        Content Type: {content_type}
        Tone: {tone}
        Prompt: {prompt}
        Here is a generated sample paragraph based on your input...
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam."""
        
        # Editable Output Box
        st.subheader("🖊️ Generated Output")
        edited_output = st.text_area("Edit the result as needed:", value=result_text, height=300)

        # Download Button
        st.download_button(
            label="💾 Download Output",
            data=edited_output,
            file_name="cafbrain_output.txt",
            mime="text/plain"
        )
