import os
from bs4 import BeautifulSoup
import json
import re
import glob

# 1. SETUP: Where did you save the HTML files?
# Using 'os.path.expanduser' finds your Home folder automatically.
SOURCE_FOLDER = os.path.expanduser("~/Downloads/ipostal1_source")

def clean_text(text):
    """Removes extra whitespace/newlines."""
    if text:
        text = text.replace('\xa0', ' ').replace('\n', ' ')
        return re.sub(r'\s+', ' ', text).strip()
    return ""

def get_context_from_title(soup):
    """Extracts title from local HTML file."""
    if soup.title:
        raw_title = soup.title.string
        if raw_title:
            clean = raw_title.split('|')[0].split('-')[0].strip()
            return clean
    return "General Knowledge"

def parse_local_files():
    knowledge_base = []
    
    # Find all HTML files in the folder
    # This grabs .html, .htm, or .php files if you saved them that way
    search_path = os.path.join(SOURCE_FOLDER, "*")
    files = glob.glob(search_path)
    
    # Filter for html-ish files
    html_files = [f for f in files if f.endswith(('.html', '.htm', '.php', '.webarchive'))]

    if not html_files:
        print(f"❌ No files found in {SOURCE_FOLDER}")
        print("Please make sure you saved the pages there!")
        return

    print(f"📂 Found {len(html_files)} local files. Processing...")

    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 1. Get Context
            context_tag = get_context_from_title(soup)
            
            # 2. Extract Questions (DT) and Answers (DD)
            questions = soup.find_all("dt")
            
            count = 0
            for q_elem in questions:
                question_text = clean_text(q_elem.get_text())
                answer_elem = q_elem.find_next_sibling("dd")
                
                if answer_elem:
                    answer_text = clean_text(answer_elem.get_text())
                    
                    if question_text and answer_text:
                        entry = {
                            "context": context_tag,
                            "source_file": os.path.basename(file_path),
                            "question": question_text,
                            "answer": answer_text
                        }
                        knowledge_base.append(entry)
                        count += 1
            
            print(f"   -> Parsed '{os.path.basename(file_path)}': Found {count} facts ({context_tag})")

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    # 3. Save the JSON Output to Downloads
    output_path = os.path.join(os.path.expanduser("~/Downloads"), "ipostal1_knowledge_base.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ SUCCESS! Extracted {len(knowledge_base)} total facts.")
    print(f"   Saved Brain to: {output_path}")

if __name__ == "__main__":
    parse_local_files()