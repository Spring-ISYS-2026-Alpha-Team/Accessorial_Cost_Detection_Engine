import sys
import os
import streamlit as st
import requests
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import require_auth
from utils.styling import inject_css, top_nav

st.set_page_config(
    page_title="PACE — Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

require_auth()
username = st.session_state.get("username", "User")
top_nav(username)

try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    HF_MODEL = st.secrets["HF_MODEL"]
except Exception:
    HF_TOKEN = os.getenv("HF_TOKEN", "")
    HF_MODEL = os.getenv("HF_MODEL", "kirsten-capangpangan/pace-smollm2-freight")

API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"
HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

st.markdown("""
<style>
.chat-bubble-user {
    background: #3A2B50;
    color: #e8e0f0;
    border-radius: 16px 16px 4px 16px;
    padding: 10px 16px;
    margin: 6px 0 6px 20%;
    font-size: 14px;
    line-height: 1.5;
}
.chat-bubble-bot {
    background: #1B435E;
    color: #d0eaf7;
    border-radius: 16px 16px 16px 4px;
    padding: 10px 16px;
    margin: 6px 20% 6px 0;
    font-size: 14px;
    line-height: 1.5;
}
.chat-label {
    font-size: 11px;
    color: #888;
    margin: 2px 0;
}
</style>
""", unsafe_allow_html=True)

st.title("PACE Assistant")
st.caption("Ask about shipment risk, accessorial charges, or carrier data fields.")

EXAMPLE_QUESTIONS = [
    "What is an accessorial charge?",
    "What does oos_total mean?",
    "How does diesel price affect freight costs?",
    "What makes a shipment high risk?",
]

if "messages" not in st.session_state:
    st.session_state.messages = []

def build_prompt(user_message):
    return (
        "Below is an instruction that describes a task.\n"
        "Write a response that appropriately completes the request.\n\n"
        f"### Instruction:\n{user_message}\n\n"
        "### Response:\n"
    )

def query_model(prompt, retries=3):
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "return_full_text": False,
        }
    }
    for attempt in range(retries):
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json=payload,
                timeout=60
            )

            if response.status_code == 401:
                return "Authentication failed. Please check the HF token in secrets."

            if response.status_code == 403:
                return "Access denied. Token may not have inference permissions."

            if response.status_code == 404:
                return "Model not found. Please check the model name in secrets."

            if response.status_code == 503:
                est = response.json().get("estimated_time", 20)
                st.info(f"Model is warming up, retrying in {int(est)} seconds...")
                time.sleep(min(est, 30))
                continue

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    text = result[0].get("generated_text", "").strip()
                    if "### Response:" in text:
                        text = text.split("### Response:")[-1].strip()
                    return text if text else "No response generated. Try rephrasing your question."

            return f"Unexpected response ({response.status_code}): {response.text[:200]}"

        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                return "Request timed out. The model may be overloaded — try again in a moment."
        except Exception as e:
            if attempt == retries - 1:
                return f"Error contacting model: {str(e)}"
        time.sleep(3)

    return "The model did not respond after multiple attempts. Try again in a moment."

st.markdown("**Quick questions:**")
cols = st.columns(2)
for i, q in enumerate(EXAMPLE_QUESTIONS):
    if cols[i % 2].button(q, key=f"example_{i}"):
        st.session_state.messages.append({"role": "user", "content": q})
        with st.spinner("Thinking..."):
            answer = query_model(build_prompt(q))
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

st.divider()

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="chat-label" style="text-align:right">You</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="chat-bubble-user">{msg["content"]}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="chat-label">PACE Assistant</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="chat-bubble-bot">{msg["content"]}</div>',
            unsafe_allow_html=True
        )

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Ask about freight risk, carriers, or PACE...",
        key="chat_input"
    )
    submitted = st.form_submit_button("Send")

if submitted and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        answer = query_model(build_prompt(user_input))
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

if st.button("Clear chat"):
    st.session_state.messages = []
    st.rerun()