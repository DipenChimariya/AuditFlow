import streamlit as st

st.title("AuditFlow")

uploaded_file = st.file_uploader(
    "Upload Invoice",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file:
    st.success("File uploaded successfully")