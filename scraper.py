import httpx
from bs4 import BeautifulSoup
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
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
                # 1. Question
                q_text_el = c.select_one(".bix-td-qtxt")
                if not q_text_el:
                    continue
                q_text = clean_text(q_text_el.get_text(separator=" ", strip=True))

                # 2. Options (Handles tables, lists, and plain rows)
                options = []
                opt_tables = c.select(".bix-tbl-options tr")
                for row in opt_tables:
                    text_cells = row.select("td")
                    if len(text_cells) >= 2:
                        opt_id = text_cells[0].get_text(strip=True).replace(".", "").replace("(", "").replace(")", "").strip()
                        opt_val = clean_text(text_cells[1].get_text(strip=True))
                        if opt_id in ["A", "B", "C", "D", "E"]:
                            options.append({"id": opt_id, "text": opt_val})

                # 3. Correct Answer
                ans_el = c.select_one(".jq-hdnakqb, .pnl-answer")
                correct_ans = None
                if ans_el:
                    correct_ans = ans_el.get("value") or ans_el.get_text(strip=True)
                    correct_ans = correct_ans.replace("Answer:", "").strip()

                # 4. Explanation
                exp_el = c.select_one(".bix-ans-description, .div-explanation")
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
    
