import json
import os
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

# --- CONFIGURATION ---
# Make sure your API Key is set in your environment or paste it here (not recommended for sharing)
client = OpenAI(api_key=os.environ.get("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"))

# Paths
KNOWLEDGE_BASE_PATH = os.path.expanduser("~/Downloads/ipostal1_knowledge_base.json")
DRAFT_TEXT = """
[PASTE THE TEXT OF THE DRAFT YOU WANT TO CHECK HERE]
For example:
iPostal1 offers virtual office services in all 195 countries.
You can pick up your mail on Sundays at any location.
"""

def get_embedding(text):
    """Turns text into a vector using OpenAI."""
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def load_brain():
    """Loads the JSON and pre-calculates embeddings (The Indexing Step)."""
    print("🧠 Loading Knowledge Base...")
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        print(f"❌ Error: Could not find {KNOWLEDGE_BASE_PATH}")
        return None, None

    with open(KNOWLEDGE_BASE_PATH, 'r') as f:
        kb = json.load(f)
    
    # Simple In-Memory Vector Store
    # In a real app, you'd use Pinecone/ChromaDB. For tonight, a list is fine.
    print(f"   -> Indexing {len(kb)} facts (this takes a few seconds)...")
    
    vectors = []
    facts = []
    
    for entry in kb:
        # We embed the Question + Answer combined for better context matching
        text_chunk = f"Context: {entry['context']} | Q: {entry['question']} | A: {entry['answer']}"
        entry['embedding'] = get_embedding(text_chunk)
        
        vectors.append(entry['embedding'])
        facts.append(text_chunk)
        
    return facts, np.array(vectors)

def check_draft(draft, facts, vectors):
    print("\n🕵️‍♂️ Auditing Draft...\n")
    sentences = [s.strip() for s in draft.split('.') if len(s.strip()) > 20] # Simple split
    
    for i, sentence in enumerate(sentences):
        # 1. Embed the sentence
        sent_vector = np.array(get_embedding(sentence)).reshape(1, -1)
        
        # 2. Search the Brain (Cosine Similarity)
        similarities = cosine_similarity(sent_vector, vectors)
        top_idx = np.argmax(similarities)
        score = similarities[0][top_idx]
        
        # 3. Filter: Is there a relevant fact? (Threshold 0.4 is a good starting point)
        if score > 0.4:
            relevant_fact = facts[top_idx]
            
            # 4. The "Judge" (GPT-4)
            # We ask: Does the sentence contradict the fact?
            prompt = f"""
            FACT: {relevant_fact}
            CLAIM: {sentence}
            
            Based ONLY on the FACT, is the CLAIM accurate?
            If YES, return "PASS".
            If NO, return "FAIL - [Brief Explanation]".
            If the FACT doesn't contain enough info, return "SKIP".
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            result = response.choices[0].message.content
            
            if "FAIL" in result:
                print(f"❌ SENTENCE {i+1}: {sentence}")
                print(f"   EVIDENCE: {relevant_fact}")
                print(f"   VERDICT: {result}\n")
            # else: print(f"✅ Sentence {i+1} Passed") # Uncomment to see passes

        else:
            # Low score means we don't have a fact about this.
            # print(f"⚠️ No matching fact found for: {sentence}")
            pass

if __name__ == "__main__":
    facts, vectors = load_brain()
    if facts:
        check_draft(DRAFT_TEXT, facts, vectors)