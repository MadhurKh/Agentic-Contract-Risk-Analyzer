import streamlit as st
from app.contract_analyzer import analyze_contract

st.title("📄 GenAI Contract Risk Analyzer")

contract_text = st.text_area("Paste your contract below:", height=300)

if st.button("Analyze"):
    with open("prompts/risk_detection_prompt.txt", "r") as f:
        prompt = f.read()
    result = analyze_contract(contract_text, prompt)
    st.text_area("🛡️ Risk Analysis", value=result, height=300)
