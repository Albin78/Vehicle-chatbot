import os
import urllib3
import streamlit as st
import requests

# Disable InsecureRequestWarning for internal SSL container communication
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = os.getenv("API_URL", "http://localhost:8000/query")

st.set_page_config(page_title="VMS Chatbot", layout="wide")

st.title("VMS Chatbot")

# -------------------------
# Session history
# -------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------
# Sidebar (Better UX for system inputs)
# -------------------------
# st.sidebar.header("Configuration")

# company_id = st.sidebar.text_input("Company ID")

# -------------------------
# Main Inputs
# -------------------------
query = st.text_input("Enter your query")

col1, col2 = st.columns([1, 1])

with col1:
    submit = st.button("Run Query")

with col2:
    clear = st.button("Clear History")

# -------------------------
# Clear history
# -------------------------
if clear:
    st.session_state.history = []

# -------------------------
# Submit Logic
# -------------------------
if submit:
    if not query.strip():
        st.warning("Query cannot be empty")

    # elif not company_id.strip():
    #     st.warning("Company ID is required")

    else:
        try:
            with st.spinner("Processing..."):

                response = requests.post(
                    API_URL,
                    json={
                        "query": query
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                    verify=False
                )

            if response.status_code != 200:
                st.warning(
                    "I apologize, but I am having trouble reaching the vehicle network right now. "
                    "Please try your request again in a few moments."
                )

            else:
                data = response.json()
                answer = data.get("response", "No response available")

                # Store history
                st.session_state.history.append({
                    "query": query,
                    "answer": answer
                })

        except Exception as e:
            st.warning(
                "I apologize, but I am having trouble reaching the vehicle network right now. "
                "Please try your request again in a few moments."
            )

# -------------------------
# Display History
# -------------------------
if st.session_state.history:
    st.markdown("### Chat History")

    for item in reversed(st.session_state.history):
        st.markdown(f"**You:** {item['query']}")
        st.success(item["answer"])