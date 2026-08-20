import httpx
from bs4 import BeautifulSoup
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text: str) -> str:
    """Extra newlines, HTML artifacts aur messy spaces clean karta hai."""
    if not text:
        return ""
    # Remove HTML entities like \n1\n;
    text = re.sub(r'\\n|\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_indiabix_questions():
    url = "https://www.indiabix.com/aptitude/time-and-work/"
    questions = []
    
    try:
        res = httpx.get(url, headers=HEADERS, timeout=20.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            containers = soup.select(".bix-div-container")
            
            for idx, c in enumerate(containers):
                # 1. Question Text
                q_text_el = c.select_one(".bix-td-qtxt")
                if not q_text_el:
                    continue
                q_text = clean_text(q_text_el.get_text(separator=" ", strip=True))

                # 2. Options Extraction
                options = []
                # IndiaBIX uses table rows or flex divs for options
                opt_rows = c.select(".bix-tbl-options tr, .bix-opt-row")
                for row in opt_rows:
                    opt_id_el = row.select_one(".bix-td-option-order, .bix-opt-order")
                    opt_val_el = row.select_one(".bix-td-option-val, .bix-opt-desc")
                    
                    if opt_id_el and opt_val_el:
                        opt_id = opt_id_el.get_text(strip=True).replace(".", "").replace("(", "").replace(")", "").strip()
                        opt_text = clean_text(opt_val_el.get_text(separator=" ", strip=True))
                        options.append({
                            "id": opt_id,
                            "text": opt_text
                        })

                # 3. Correct Answer
                ans_input = c.select_one("input.jq-hdnakqb")
                correct_ans = ans_input.get("value", "").strip() if ans_input else None

                # 4. Step-by-Step Explanation
                exp_el = c.select_one(".bix-ans-description")
                explanation = clean_text(exp_el.get_text(separator=" ", strip=True)) if exp_el else None

                questions.append({
                    "id": f"ibix_tw_{idx+1}",
                    "category": "Quantitative Aptitude",
                    "topic": "Time and Work",
                    "question": q_text,
                    "options": options,
                    "correct_option": correct_ans,
                    "explanation": explanation
                })
    except Exception as e:
        print(f"Scraping error: {e}")
        
    return questions

if __name__ == "__main__":
    new_data = fetch_indiabix_questions()
    
    with open("master_questions.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully processed {len(new_data)} clean questions.")
    
