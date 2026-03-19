import streamlit as st
import requests

API_URL = "http://localhost:8000/query"

st.set_page_config(page_title="VMS Chatbot", layout="wide")

st.title("VMS Chatbot")

# Session history
if "history" not in st.session_state:
    st.session_state.history = []

# Inputs
imei = st.text_input("Enter IMEI")

query = st.text_input("Enter your query")

col1, col2 = st.columns([1, 1])

with col1:
    submit = st.button("Run Query")

with col2:
    clear = st.button("Clear")

if clear:
    st.session_state.history = []

if submit:
    if not query.strip():
        st.warning("Query cannot be empty")
    elif not imei.strip():
        st.warning("IMEI is required")
    else:
        try:
            with st.spinner("Processing..."):
                response = requests.post(
                    API_URL,
                    json={
                        "query": query,
                        "imei": imei
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )

            if response.status_code != 200:
                st.error(f"API Error: {response.status_code}")
                st.text(response.text)
            else:
                data = response.json()

                answer = data.get("response", "No response available")

                # Store history
                st.session_state.history.append({
                    "query": query,
                    "answer": answer
                })

                # Display nicely
                st.markdown("### Response")
                st.success(answer)

        except Exception as e:
            st.error(f"Error: {str(e)}")