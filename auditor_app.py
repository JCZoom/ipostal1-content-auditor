import streamlit as st
import dspy # pip install dspy-ai
import os
import json
import numpy as np
import base64
import re
import time
import uuid 
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_quill import st_quill
from openai import OpenAI

# --- 0. CONFIG & AUTHENTICATION ---
st.set_page_config(
    page_title="iPostal1 Content Auditor", 
    page_icon="ipostal1_logo.png", 
    layout="wide"
)

# --- CSS ---
CORE_CSS = """
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { color: #005eb8 !important; }
    div.stButton > button:first-child { background-color: #005eb8; color: white; border: none; }
    div.stButton > button:hover { background-color: #2a2829; color: white; border: none; }
    .pass-box { border-left: 5px solid #28a745; background-color: #e6fffa; padding: 15px; margin-bottom: 10px; border-radius: 5px; color: #333; }
    .fail-box { border-left: 5px solid #dc3545; background-color: #ffe6e6; padding: 15px; margin-bottom: 10px; border-radius: 5px; color: #333; }
    .warn-box { border-left: 5px solid #ffc107; background-color: #fff3cd; padding: 15px; margin-bottom: 10px; border-radius: 5px; color: #333; }
    .meta-label { font-weight: bold; color: #555; font-size: 0.75em; text-transform: uppercase; display: block; margin-bottom: 4px; }
    .stCheckbox { padding-top: 15px; } 
"""
st.markdown(f"<style>{CORE_CSS}</style>", unsafe_allow_html=True)

# --- LOGIN ---
if "OPENAI_API_KEY" not in st.secrets or "APP_PASSWORD" not in st.secrets:
    st.error("❌ Missing .streamlit/secrets.toml file.")
    st.stop()

def check_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated: return True

    st.markdown("## 🔒 Internal Access Only")
    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Password")
    return False

if not check_login(): st.stop()

# --- 1. DSPY SETUP ---
api_key = st.secrets["OPENAI_API_KEY"]

@st.cache_resource
def get_llm_object(key):
    try:
        return dspy.LM('openai/gpt-4o', api_key=key, max_tokens=300)
    except:
        try:
            return dspy.OpenAI(model='gpt-4o', api_key=key, max_tokens=300)
        except Exception as e:
            st.error(f"❌ OpenAI Connection Error: {e}")
            return None

lm_object = get_llm_object(api_key)
if not lm_object: st.stop()

# --- 2. PATHS & ASSETS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "ipostal1_logo.png")
KB_PATH = os.path.join(BASE_DIR, "ipostal1_knowledge_base.json")
RULES_PATH = os.path.join(BASE_DIR, "larry_rules.json")
OVERRIDES_PATH = os.path.join(BASE_DIR, "overrides.json")

# --- 3. DSPY SIGNATURES ---
class FactAuditSignature(dspy.Signature):
    """
    ROLE: Senior Content Auditor for iPostal1.
    INSTRUCTIONS:
    1. CHECK DEFINITION TRAP (Highest Priority):
       - Does this sentence define "A Virtual Address" (universal) as HAVING digital features?
       - FAIL PATTERN: "A virtual address is a location managed via an app."
       - PASS PATTERN: "An iPostal1 virtual address includes an app."
    2. CHECK OVERRIDES: If the claim contradicts the Overrides list -> FAIL.
    3. CHECK TERMINOLOGY: "P.O. Box" refers to a competitor. Claims stating they lack features are TRUE.
    4. CHECK PASSIVE VOICE: FAIL only if structure is truly passive.
    5. CHECK OPERATIONAL DETAILS: Claims about LOGGING, PHOTOGRAPHING, or SCANNING THE EXTERIOR of mail are TRUE standard procedures.
    
    OUTPUT: PASS, FAIL, or WARN.
    """
    sentence = dspy.InputField()
    context = dspy.InputField(desc="Knowledge Base")
    overrides = dspy.InputField(desc="Overrides List")
    status = dspy.OutputField(desc="PASS, FAIL, or WARN")
    reason = dspy.OutputField(desc="Reason")

class StructureAuditSignature(dspy.Signature):
    """
    TASK: Audit this text block for AEO Structure (Chunking).
    RULES:
    1. SINGLE IDEA: Does it focus on ONE concept?
    2. SELF-CONTAINED: Can it be understood in isolation?
    OUTPUT: PASS or FAIL
    """
    paragraph = dspy.InputField()
    status = dspy.OutputField(desc="PASS or FAIL")
    reason = dspy.OutputField(desc="Reason")

class AuditorBot(dspy.Module):
    def __init__(self):
        super().__init__()
        self.fact_check = dspy.ChainOfThought(FactAuditSignature)
        self.struct_check = dspy.ChainOfThought(StructureAuditSignature)

    def audit_fact(self, sentence, context, overrides):
        return self.fact_check(sentence=sentence, context=context, overrides=overrides)

    def audit_structure(self, paragraph):
        return self.struct_check(paragraph=paragraph)

bot = AuditorBot()

# --- 4. HELPERS ---
def get_base64_logo(file_path):
    if not os.path.exists(file_path): return None
    with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
logo_b64 = get_base64_logo(LOGO_PATH)

@st.cache_resource
def load_data():
    kb, vecs, rules, ovr = [], None, [], []
    if os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, 'r') as f: data = json.load(f)
            kb = [f"Q: {e.get('question','')} | A: {e.get('answer','')}" for e in data if "embedding" in e]
            vecs = np.array([e["embedding"] for e in data if "embedding" in e])
        except: pass
    if os.path.exists(RULES_PATH): 
        with open(RULES_PATH, 'r') as f: rules = json.load(f)
    if os.path.exists(OVERRIDES_PATH):
        with open(OVERRIDES_PATH, 'r') as f: ovr = json.load(f)
    return kb, vecs, rules, ovr

facts, vectors, larry_rules, overrides = load_data()

def get_embedding_openai(text):
    text = text.replace("\n", " ")
    try:
        client = OpenAI(api_key=api_key)
        return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding
    except: return None

# --- UPDATED SENTENCE SPLITTER ---
def split_sentences(text):
    """
    Splits text into sentences while ignoring periods in common abbreviations (U.S., U.K., Mr., etc.).
    Strategy:
    1. Use negative lookbehinds (?<!...) to ignore known abbreviations.
    2. Use lookahead (?=[A-Z]|$) to only split if the next char is Uppercase or end-of-string.
       This prevents splitting "U.S. government" where 'g' is lowercase.
    """
    # Pattern explanation:
    # (?<!U\.S) -> Do not split if preceded by U.S
    # (?<!\b[A-Z]) -> Do not split if preceded by a single capital letter (initials)
    # [.!?]+ -> Split on punctuation
    # (?:\s+(?=[A-Z])|$) -> Only if followed by whitespace+Capital Letter OR End of string
    
    pattern = r'(?<!U\.S)(?<!U\.K)(?<!P\.O)(?<!Mr)(?<!Mrs)(?<!Ms)(?<!Dr)(?<!Inc)(?<!Ltd)(?<!\b[A-Z])[.!?]+(?:\s+(?=[A-Z])|$)'
    
    chunks = re.split(pattern, text)
    return [c.strip() for c in chunks if len(c.strip()) > 5]

def check_grammar_and_style(sentence):
    flags = []
    
    # --- UPDATED SECTION: REFERENTIAL AMBIGUITY ---
    # This regex looks for This, That, These, Those, It, or They at the start of a sentence.
    # It captures the specific word found so you can see which one triggered the flag.
    ambiguity_match = re.search(r'^\W*(This|That|These|Those|It|They)\b', sentence, re.IGNORECASE)
    if ambiguity_match:
        found_word = ambiguity_match.group(1).title() # Capitalize for the label
        flags.append(f"Referential Ambiguity ('{found_word}' at start)")
    # -----------------------------------------------

    if sentence.strip().endswith('?') and len(sentence) > 20: flags.append("Rhetorical Question")
    if re.search(r'\b(imagine|picture this|guess what)\b', sentence, re.IGNORECASE): flags.append("Hype Language")
    if re.search(r'\b(was|were|is|are|been)\b\s+\w+\s+\bby\b', sentence, re.IGNORECASE): flags.append("Passive Voice (Regex)")
    return flags

def generate_report(s_logs, f_logs, title, notes, include_pass):
    html = f"""<html><head><style>{CORE_CSS} body {{ padding: 40px; max-width: 800px; margin: 0 auto; }}</style></head><body>
    <div style="text-align:center;"><h1>{title}</h1><p>{time.strftime("%Y-%m-%d")}</p></div>
    {f'<div style="background:#f4f4f4; padding:15px; margin-bottom:20px;"><strong>Notes:</strong><br>{notes}</div>' if notes else ''}"""
    
    filtered_s = [r for r in s_logs if include_pass or r['status'] != 'PASS']
    filtered_f = [r for r in f_logs if include_pass or r['status'] != 'PASS']

    if filtered_s:
        html += "<h3>SEO and AEO Structure Audit</h3>"
        for r in filtered_s:
            if r['status'] == "FAIL": c = "fail-box"
            elif r['status'] == "WARN": c = "warn-box"
            else: c = "pass-box"
            label_html = f"<span class='meta-label'>{r.get('label','')}</span>" if r.get('label') else ""
            html += f"<div class='{c}'>{label_html}<strong>{r['header']}</strong><br><em>{r['quote']}</em></div>"
            
    if filtered_f:
        html += "<h3>Facts, Grammar, and Style Audit</h3>"
        for r in filtered_f:
            if r['status'] == "FAIL": c = "fail-box"
            elif r['status'] == "WARN": c = "warn-box"
            else: c = "pass-box"
            label_html = f"<span class='meta-label'>{r.get('label','')}</span>" if r.get('label') else ""
            html += f"<div class='{c}'>{label_html}<strong>[{r['status']}] {r['header']}</strong><br><em>{r['quote']}</em></div>"
            
    html += "</body></html>"
    return html

# --- 5. UI & LOGIC ---
if "view_mode" not in st.session_state: st.session_state.view_mode = "audit"
if "audit_run" not in st.session_state: st.session_state.audit_run = False
if "logs" not in st.session_state: st.session_state.logs = {"structure": [], "facts": []}
if "show_pass" not in st.session_state: st.session_state.show_pass = True

# --- SIDEBAR (RESTORED) ---
with st.sidebar:
    st.success("🔓 Logged in")
    st.divider()
    st.info(f"🧠 Brain: {len(facts)} items\n📏 Rules: {len(larry_rules)}\n⚡ Overrides: {len(overrides)}")
    if st.session_state.view_mode == "audit":
        st.session_state.show_pass = st.checkbox("Show Passing Items (Audit View)", value=st.session_state.show_pass)
    if st.button("🔒 Logout"): st.session_state.authenticated = False; st.rerun()

# --- MAIN AUDIT VIEW ---
if st.session_state.view_mode == "audit":
    # Using HTML Flexbox to perfectly align logo bottom with text bottom
    # and remove the whitespace gap.
    st.markdown(f"""
        <div style="display: flex; align-items: flex-end; gap: 10px; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_b64}" width="80" style="margin-bottom: 6px;">
            <div>
                <h1 style="margin: 0; padding: 0; line-height: 1.2; font-size: 3rem;">iPostal1 Content Auditor</h1>
                <p style="margin: 0; padding: 0; font-size: 1rem; color: #555;">SEO/AEO & Brand Compliance Tool</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    target_kw = st.text_input("Target Keyword (Required):", placeholder="e.g. virtual mailbox")
    draft_html = st_quill(placeholder="Paste content here...", html=True, key="quill")

    if st.button("🚀 Audit Content", type="primary"):
        st.session_state.logs = {"structure": [], "facts": []}
        st.session_state.audit_run = True
        
        if not draft_html: st.warning("Input is empty."); st.stop()
        
        # --- PARSING ---
        soup = BeautifulSoup(draft_html, "html.parser")
        elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'div', 'li'])
        links = soup.find_all('a')
        
        # Fallback for plain text
        if len(elements) < 1:
            raw_text = soup.get_text(separator="\n")
            blocks = [b.strip() for b in raw_text.split('\n') if len(b.strip()) > 5]
            elements = []
            for b in blocks:
                tag = soup.new_tag("p")
                tag.string = b
                elements.append(tag)

        # --- SETUP CONTAINERS FOR REAL-TIME DISPLAY ---
        progress = st.progress(0, text="Initializing...")
        
        st.subheader("SEO and AEO Structure Audit")
        struct_con = st.container()
        
        st.subheader("Facts, Grammar, and Style Audit")
        fact_con = st.container()

        # --- 1. GLOBAL CHECKS (LINKS) ---
        link_count = len(links)
        l_res = {}
        if link_count > 4:
            l_res = {"status": "FAIL", "header": f"Link Count: {link_count} (Limit is 4)", "quote": "Too many links."}
        elif link_count == 0:
            l_res = {"status": "FAIL", "header": "Link Count: 0 (Min 2 required)", "quote": "No links found."}
        else:
            l_res = {"status": "PASS", "header": f"Found {link_count} links (Pass)", "quote": "OK."}
        
        st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "SEO | LINK COUNT", **l_res})
        if l_res['status'] != 'PASS' or st.session_state.show_pass:
            css = "fail-box" if l_res['status'] == "FAIL" else "pass-box"
            struct_con.markdown(f"<div class='{css}'><strong>{l_res['header']}</strong></div>", unsafe_allow_html=True)

        # --- 2. MAIN LOOP ---
        current_section_words = 0
        current_h2 = None
        h2_keyword_found = False
        para_counter = 0
        
        for i, el in enumerate(elements):
            text = el.get_text().strip()
            if not text or len(text) < 2: continue 
            
            progress.progress((i+1)/len(elements), text=f"Auditing Block {i+1}...")
            words = text.split()
            tag = el.name if el.name else "p"
            
            # --- STRUCTURE: H1 ---
            if tag == 'h1':
                if target_kw and target_kw.lower() in text.lower():
                    res = {"status": "PASS", "header": f"Includes keyword '{target_kw}'", "quote": text}
                else:
                    res = {"status": "FAIL", "header": f"Missing keyword '{target_kw}'", "quote": text}
                st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "H1 HEADER", **res})
                if res['status'] != 'PASS' or st.session_state.show_pass:
                    css = "fail-box" if res['status'] == "FAIL" else "pass-box"
                    struct_con.markdown(f"<div class='{css}'><strong>{res['header']}</strong><br><em>{res['quote']}</em></div>", unsafe_allow_html=True)

            # --- STRUCTURE: H2 ---
            elif tag == 'h2':
                if current_h2 and current_section_words > 300:
                    res = {"status": "FAIL", "header": f"Section '{current_h2[:30]}...' is {current_section_words} words. Limit is 300.", "quote": ""}
                    st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "H2 SECTION LENGTH", **res})
                    struct_con.markdown(f"<div class='fail-box'><strong>{res['header']}</strong></div>", unsafe_allow_html=True)

                current_section_words = 0
                current_h2 = text
                if target_kw and target_kw.lower() in text.lower():
                    h2_keyword_found = True

            # --- STRUCTURE: LIST CONTAINERS ---
            elif tag in ['ul', 'ol']:
                list_items = el.find_all('li', recursive=False)
                count = len(list_items)
                
                if count > 0 and count < 3:
                    res = {"status": "WARN", "header": f"List has only {count} items.", "quote": "Fewer than 3 items lacks meaningful structure."}
                    st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "LIST CHUNKING", **res})
                    struct_con.markdown(f"<div class='warn-box'><span class='meta-label'>LIST CHUNKING</span><strong>{res['header']}</strong><br><em>{res['quote']}</em></div>", unsafe_allow_html=True)
                elif count > 5:
                    res = {"status": "FAIL", "header": f"List has {count} items (Limit is 5).", "quote": "Exceeds working-memory span."}
                    st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "LIST CHUNKING", **res})
                    struct_con.markdown(f"<div class='fail-box'><span class='meta-label'>LIST CHUNKING</span><strong>{res['header']}</strong><br><em>{res['quote']}</em></div>", unsafe_allow_html=True)

            # --- STRUCTURE: LIST ITEMS ---
            elif tag == 'li':
                current_section_words += len(words)
                if len(words) > 30:
                    res = {"status": "FAIL", "header": f"Bullet is {len(words)} words (Limit 30).", "quote": text[:50]+"..."}
                    st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "BULLET LENGTH", **res})
                    struct_con.markdown(f"<div class='fail-box'><span class='meta-label'>BULLET LENGTH</span><strong>{res['header']}</strong><br><em>{res['quote']}</em></div>", unsafe_allow_html=True)

                if len(words) > 5:
                    try:
                        with dspy.context(lm=lm_object):
                            pred = bot.audit_structure(paragraph=text)
                        if pred.status == "FAIL":
                            st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "BULLET CONTEXT", "status": "FAIL", "header": "Bullet not self-contained", "quote": text[:50]+"..."})
                            struct_con.markdown(f"<div class='fail-box'><span class='meta-label'>BULLET CONTEXT</span><strong>Bullet not self-contained</strong><br><em>{text[:50]}...</em></div>", unsafe_allow_html=True)
                    except: pass

            # --- STRUCTURE: PARAGRAPHS ---
            elif tag in ['p', 'div', 'h3', 'h4', 'h5', 'h6']:
                current_section_words += len(words)
                
                if len(words) > 5:
                    para_counter += 1
                    sentences = split_sentences(text)

                    if para_counter == 1:
                        if target_kw and target_kw.lower() in sentences[0].lower():
                            res = {"status": "PASS", "header": f"Keyword '{target_kw}' found.", "quote": text[:100]}
                        else:
                            res = {"status": "FAIL", "header": f"Keyword '{target_kw}' missing.", "quote": text[:100]}
                        st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "FIRST SENTENCE", **res})
                        if res['status'] != 'PASS' or st.session_state.show_pass:
                            css = "fail-box" if res['status'] == "FAIL" else "pass-box"
                            struct_con.markdown(f"<div class='{css}'><strong>{res['header']}</strong><br><em>{res['quote']}</em></div>", unsafe_allow_html=True)

                    len_res = None
                    if len(sentences) > 4:
                        len_res = {"status": "FAIL", "header": f"Too Long ({len(sentences)} sentences)", "quote": text[:50]+"..."}
                    elif len(words) > 80:
                        len_res = {"status": "FAIL", "header": f"Wall of Text ({len(words)} words)", "quote": text[:50]+"..."}
                    elif len(sentences) < 2 and len(words) > 20:
                        len_res = {"status": "WARN", "header": f"Too Short ({len(sentences)} sentence - Aim for 2-4)", "quote": text[:50]+"..."}
                    
                    if len_res:
                        st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "PARAGRAPH LENGTH", **len_res})
                        css = "fail-box" if len_res['status'] == "FAIL" else "warn-box"
                        struct_con.markdown(f"<div class='{css}'><strong>{len_res['header']}</strong><br><em>{len_res['quote']}</em></div>", unsafe_allow_html=True)

                    try:
                        with dspy.context(lm=lm_object):
                            pred = bot.audit_structure(paragraph=text)
                        st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "AEO CHUNKING", "status": pred.status, "header": pred.reason, "quote": text[:50]+"..."})
                        if pred.status != "PASS" or st.session_state.show_pass:
                            css = "fail-box" if pred.status == "FAIL" else "pass-box"
                            struct_con.markdown(f"<div class='{css}'><span class='meta-label'>AEO CHUNKING</span><strong>{pred.reason}</strong><br><em>{text[:50]}...</em></div>", unsafe_allow_html=True)
                    except: pass

            # --- FACTS & GRAMMAR LOOP ---
            is_header = tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            if is_header: sentences = [text] 
            else: sentences = split_sentences(text)

            for sent in sentences:
                # 1. LARRY RULES
                hit_rule = False
                for rule in larry_rules:
                    if any(t.lower() in sent.lower() for t in rule["triggers"]):
                        if all(m.lower() in sent.lower() for m in rule.get("must_also_contain", [])):
                            res = {"status": "FAIL", "label": "LARRY RULE", "header": rule['message'], "quote": sent}
                            st.session_state.logs["facts"].append({"id": str(uuid.uuid4()), **res})
                            fact_con.markdown(f"<div class='fail-box'>❌ <strong>{rule['message']}</strong><br><em>{sent}</em></div>", unsafe_allow_html=True)
                            hit_rule = True
                if hit_rule: continue
                
                # 2. GRAMMAR
                if not is_header:
                    style_flags = check_grammar_and_style(sent)
                    if style_flags:
                        res = {"status": "WARN", "label": "STYLE", "header": ", ".join(style_flags), "quote": sent}
                        st.session_state.logs["facts"].append({"id": str(uuid.uuid4()), **res})
                        fact_con.markdown(f"<div class='warn-box'>⚠️ <strong>{res['header']}</strong><br><em>{sent}</em></div>", unsafe_allow_html=True)

                    # 3. DSPy FACT
                    ctx = "No specific internal match found."
                    emb = get_embedding_openai(sent)
                    if emb is not None and vectors is not None and len(vectors) > 0:
                        sims = cosine_similarity(np.array(emb).reshape(1, -1), vectors)
                        top_idx = np.argsort(sims[0])[-2:][::-1]
                        if sims[0][top_idx[0]] > 0.15:
                            ctx = " | ".join([facts[x] for x in top_idx])
                    
                    overrides_str = "; ".join(overrides)
                    with dspy.context(lm=lm_object):
                        pred = bot.audit_fact(sentence=sent, context=ctx, overrides=overrides_str)
                    
                    st.session_state.logs["facts"].append({"id": str(uuid.uuid4()), "status": pred.status, "label": "FACT/STYLE", "header": pred.reason, "quote": sent})
                    
                    if pred.status != "PASS" or st.session_state.show_pass:
                        css = "fail-box" if pred.status == "FAIL" else "warn-box" if pred.status == "WARN" else "pass-box"
                        icon = "✅" if pred.status == "PASS" else "❌" if pred.status == "FAIL" else "⚠️"
                        fact_con.markdown(f"<div class='{css}'><span class='meta-label'>FACT/STYLE</span><strong>{icon} {pred.reason}</strong><br><em>{sent}</em></div>", unsafe_allow_html=True)

        # --- FINAL CHECKS ---
        if current_h2 and current_section_words > 300:
             res = {"status": "FAIL", "header": f"Section '{current_h2[:30]}...' is {current_section_words} words. Limit is 300.", "quote": ""}
             st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "H2 SECTION LENGTH", **res})
             struct_con.markdown(f"<div class='fail-box'><strong>{res['header']}</strong></div>", unsafe_allow_html=True)
             
        if target_kw:
            if h2_keyword_found:
                res = {"status": "PASS", "header": "Primary keyword found in at least one H2.", "quote": ""}
            else:
                res = {"status": "FAIL", "header": f"Primary keyword '{target_kw}' NOT found in any H2.", "quote": ""}
            st.session_state.logs["structure"].append({"id": str(uuid.uuid4()), "label": "H2 KEYWORDS", **res})
            if res['status'] != 'PASS' or st.session_state.show_pass:
                css = "pass-box" if res['status'] == "PASS" else "fail-box"
                struct_con.markdown(f"<div class='{css}'><strong>{res['header']}</strong></div>", unsafe_allow_html=True)

        progress.empty()
        st.success("Audit Complete.")
        
    # --- EXPORT BUTTON (PERSISTENT) ---
    if st.session_state.audit_run:
        st.divider()
        if st.button("Create and Export Results"):
            if "selected_ids" in st.session_state: del st.session_state.selected_ids
            st.session_state.view_mode = "export"
            st.rerun()

# --- EXPORT VIEW ---
elif st.session_state.view_mode == "export":
    st.title("📝 Report Export Setup")
    st.info("Review audit items below. Uncheck any items you wish to exclude from the final HTML report.")
    
    # CRITICAL FIX: Only select items that match your current 'Show Pass' setting.
    if "selected_ids" not in st.session_state:
         init_s = [
            item['id'] for item in st.session_state.logs["structure"]
            if st.session_state.show_pass or item['status'] != 'PASS'
         ]
         init_f = [
            item['id'] for item in st.session_state.logs["facts"]
            if st.session_state.show_pass or item['status'] != 'PASS'
         ]
         st.session_state.selected_ids = set(init_s + init_f)

    c_meta, c_notes = st.columns([1, 2])
    with c_meta:
        title = st.text_input("Report Title", "Content Audit")
        st.write(f"**Total Items Selected:** {len(st.session_state.selected_ids)}")
    with c_notes:
        st.markdown("<strong>Notes / Summary (Included at top of report)</strong>", unsafe_allow_html=True)
        notes = st_quill(html=True, key="export_notes_quill")

    st.divider()

    def display_selectable_logs(log_type, section_title):
        logs = st.session_state.logs[log_type]
        filtered_logs_for_display = [r for r in logs if st.session_state.show_pass or r['status'] != 'PASS']

        if filtered_logs_for_display:
            st.subheader(f"{section_title} ({len(filtered_logs_for_display)} items)")
            for item in filtered_logs_for_display:
                c_chk, c_card = st.columns([0.5, 11.5])
                with c_chk:
                    is_selected = item['id'] in st.session_state.selected_ids
                    def update_selection(item_id=item['id']):
                        if item_id in st.session_state.selected_ids:
                            st.session_state.selected_ids.remove(item_id)
                        else:
                            st.session_state.selected_ids.add(item_id)

                    st.checkbox("", value=is_selected, key=f"chk_{item['id']}", on_change=update_selection, label_visibility="collapsed")

                with c_card:
                    css = "fail-box" if item['status'] == "FAIL" else "warn-box" if item['status'] == "WARN" else "pass-box"
                    label_html = f"<span class='meta-label'>{item.get('label','')}</span>" if item.get('label') else ""
                    quote_text = item.get('quote', '')
                    quote_html = f"<br><em>{quote_text}</em>" if quote_text else ""
                    st.markdown(f"<div class='{css}' style='margin-bottom:5px;'>{label_html}<strong>{item['header']}</strong>{quote_html}</div>", unsafe_allow_html=True)
            st.divider()

    with st.container(height=600, border=True):
        display_selectable_logs("structure", "SEO and AEO Structure")
        display_selectable_logs("facts", "Facts, Grammar, and Style")

    final_s_logs = [item for item in st.session_state.logs["structure"] if item['id'] in st.session_state.selected_ids]
    final_f_logs = [item for item in st.session_state.logs["facts"] if item['id'] in st.session_state.selected_ids]

    html = generate_report(final_s_logs, final_f_logs, title, notes, include_pass=True)

    safe_title = re.sub(r'\W+', '_', title).lower().strip('_')
    if not safe_title: safe_title = "audit_report"
    file_name = f"{safe_title}.html"

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("🎉 Download Final HTML Report", data=html, file_name=file_name, mime="text/html", type="primary", use_container_width=True)
    with c2:
        if st.button("⬅ Back to Auditor", use_container_width=True): 
            st.session_state.view_mode = "audit"
            st.rerun()