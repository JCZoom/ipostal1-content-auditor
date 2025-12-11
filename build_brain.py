import json
from openai import OpenAI
import os
import streamlit as st

# --- CONFIGURATION ---
# We use st.secrets to get your API key safely, just like your main app.
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    # Fallback to environment variable if running locally without streamlit
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ Error: OpenAI API Key not found. Make sure it is in .streamlit/secrets.toml or your environment variables.")
    exit()

# --- THE BRAND BIBLE DATA ---
NEW_DATA = [
    {
        "q": "What is iPostal1's Core Identity?", 
        "a": "iPostal1 is the leader in Digital Mailbox Services. We provide Freedom & Control: 'View and manage your mail from anywhere, 24/7'."
    },
    {
        "q": "What is a Digital Mailbox?", 
        "a": "The Digital Mailbox is the Software Application (Platform) that allows users to view and manage their mail."
    },
    {
        "q": "What is a Virtual Address?", 
        "a": "A Virtual Address is the Physical Asset/Location. It acts as a router for traffic. It is a real physical street address, not a P.O. Box."
    },
    {
        "q": "What is a Virtual Office?", 
        "a": "A Virtual Office is a Communications Bundle (Phone + Fax) added to a Virtual Address. It does not imply physical office space rental."
    },
    {
        "q": "What is the difference between Virtual Business and Virtual Mailing plans?", 
        "a": "A Virtual Business plan is intended for Commercial Compliance (LLC/Corp registration). A Virtual Mailing plan is intended for Personal/Lifestyle Use."
    },
    {
        "q": "Does iPostal1 guarantee bank account opening?", 
        "a": "No. While our addresses are real and often accepted, bank policies vary. We recommend our addresses for business use but do not guarantee banking outcomes."
    },
    {
        "q": "Law #1: The Platform vs. Outcome Rule", 
        "a": "We guarantee the Mechanism, not the Outcome. We provide the tool (Address/App), but third parties (Banks/Carriers) provide the result."
    },
    {
        "q": "Law #2: The Ingestion Gap Rule", 
        "a": "The View is Instant, but the Process is Rapid and the Logistics are Physical. Mail is not available the moment the carrier arrives; there is a processing time for upload."
    },
    {
        "q": "How does iPostal1 handle package acceptance?", 
        "a": "We offer real street addresses capable of accepting packages from all carriers (FedEx, UPS), unlike standard P.O. Boxes."
    },
    {
        "q": "Shipping Costs and Rates", 
        "a": "We offer transparency ('Real-time quotes'), but not necessarily the lowest market rates. We do not promise 'Cheapest shipping'."
    }
]

# --- MAIN LOGIC ---
def generate_brain():
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {e}")
        return

    knowledge_base = []

    print(f"🧠 Processing {len(NEW_DATA)} items from Brand Bible...")

    for item in NEW_DATA:
        # Simplified: We just use the answer directly.
        text_to_embed = f"{item['q']} {item['a']}"
        
        try:
            # Generate Embedding
            response = client.embeddings.create(
                input=text_to_embed,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            
            # Add to list
            knowledge_base.append({
                "question": item['q'],
                "answer": item['a'],
                "embedding": embedding
            })
            print(f"✅ Processed: {item['q']}")
        except Exception as e:
            print(f"❌ Error processing {item['q']}: {e}")

    # Save to JSON
    try:
        with open("ipostal1_knowledge_base.json", "w") as f:
            json.dump(knowledge_base, f)
        print("\n🎉 Success! 'ipostal1_knowledge_base.json' has been updated.")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    generate_brain()