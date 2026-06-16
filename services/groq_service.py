import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def test_groq():
    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[
            {
                "role": "user",
                "content": "Reply with only: Groq connection successful"
            }
        ]
    )

    return response.choices[0].message.content
def generate_summary(contract_text):
    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[
            {
                "role": "system",
                "content": "You are a contract analysis assistant. Generate a concise summary of the contract."
            },
            {
                "role": "user",
                "content": contract_text
            }
        ]
    )

    return response.choices[0].message.content