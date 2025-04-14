# 📑 UI, Prompt Engineering, and Responsible AI Considerations

## 🖼️ Streamlit UI Design Principles

Our frontend interface is designed with a **human-in-the-loop workflow** to ensure that users — specifically fundraising and communications staff at CAFB — retain full control over the generated content.

### Key Features:
- **Editable Output Field:** Users can modify generated text before finalizing, ensuring it aligns with CAFB tone, accuracy, and brand.
- **Tone Selector:** Allows adjusting the emotional and stylistic feel of generated content.
- **Content Type Dropdown:** Enables users to pick the correct format (grant, blog post, social media) to shape prompts dynamically.
- **Source Attribution:** Clearly displays where retrieved content came from, fostering transparency and enabling fact-checking.

---

## 🧠 Prompt Engineering Strategy

Prompt templates are carefully crafted to:
- Ground responses in **retrieved source content** (RAG) to ensure relevance.
- Include **instructions on tone and format** to guide GPT-4 behavior.
- Prevent hallucinations by framing queries within explicit content boundaries.

### Example Structure:
```text
You are a helpful assistant for the Capital Area Food Bank.
Based on the following retrieved information, write a clear and concise answer to the user's query.
Tone: {tone}. Format: {format}.
---
{retrieved_chunks}
---
User query: {user_prompt}
