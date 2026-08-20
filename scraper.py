import httpx
from bs4 import BeautifulSoup
import json
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch_indiabix_questions():
    url = "https://www.indiabix.com/aptitude/time-and-work/"
    questions = []
    
    try:
        res = httpx.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            containers = soup.select(".bix-div-container")
            
            for idx, c in enumerate(containers):
                q_text_el = c.select_one(".bix-td-qtxt")
                if not q_text_el:
                    continue
                q_text = q_text_el.get_text(separator=" ", strip=True)

                options = []
                for row in c.select(".bix-tbl-options tr"):
                    opt_id = row.select_one(".bix-td-option-order")
                    opt_val = row.select_one(".bix-td-option-val")
                    if opt_id and opt_val:
                        options.append({
                            "id": opt_id.get_text(strip=True).replace(".", ""),
                            "text": opt_val.get_text(strip=True)
                        })

                ans_el = c.select_one(".jq-hdnakqb")
                correct_ans = ans_el.get("value", "").strip() if ans_el else None
                exp_el = c.select_one(".bix-ans-description")
                explanation = exp_el.get_text(separator="\n", strip=True) if exp_el else None

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
        print(f"Error scraping: {e}")
        
    return questions

if __name__ == "__main__":
    new_data = fetch_indiabix_questions()
    
    # Save output to master_questions.json
    with open("master_questions.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(new_data)} questions.")
  
