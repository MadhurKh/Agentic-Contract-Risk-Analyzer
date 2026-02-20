from openai import OpenAI  # Replace with actual call if using OpenAI or Claude
import os

def analyze_contract(contract_text, prompt):
    # Simulated output for now
    return """
Clause 2 - Missing termination clause
→ Add a standard termination condition with 30-day notice.

Clause 3 - Vague liability
→ Define indirect liability limits more clearly.
"""

if __name__ == "__main__":
    with open("sample_data/sample_contract.txt", "r") as file:
        contract = file.read()
    with open("prompts/risk_detection_prompt.txt", "r") as file:
        prompt = file.read()

    result = analyze_contract(contract, prompt)
    print(result)
