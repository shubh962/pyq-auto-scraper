import httpx
from bs4 import BeautifulSoup
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def scrape_single_page(html_content, course_id, topic_id, start_idx=1):
    questions = []
    soup = BeautifulSoup(html_content, "html.parser")
    containers = soup.select(".bix-div-container")
    
    for idx, c in enumerate(containers):
        q_text_el = c.select_one(".bix-td-qtxt")
        if not q_text_el:
            continue
        q_text = clean_text(q_text_el.get_text(separator=" ", strip=True))

        options = []
        opt_rows = c.select(".bix-tbl-options tr, .bix-opt-row")
        for row in opt_rows:
            opt_id_el = row.select_one(".bix-td-option-order, .bix-opt-order")
            opt_val_el = row.select_one(".bix-td-option-val, .bix-opt-desc")
            if opt_id_el and opt_val_el:
                opt_id = opt_id_el.get_text(strip=True).replace(".", "").strip()
                opt_val = clean_text(opt_val_el.get_text(separator=" ", strip=True))
                if opt_id in ["A", "B", "C", "D", "E"] and opt_val:
                    options.append({"id": opt_id, "text": opt_val})

        ans_input = c.select_one("input.jq-hdnakqb, input[name^='hdnAnq']")
        correct_ans = ans_input.get("value", "").strip().upper() if ans_input else None

        exp_el = c.select_one(".bix-ans-description, .div-explanation")
        explanation = clean_text(exp_el.get_text(separator=" ", strip=True)) if exp_el else None

        questions.append({
            "id": f"{topic_id}_{start_idx + idx}",
            "course_id": course_id,
            "topic_id": topic_id,
            "question": q_text,
            "options": options,
            "correct_option": correct_ans,
            "explanation": explanation
        })
    return questions

def scrape_all_pages_of_topic(base_url, course_id, topic_id, max_pages=6):
    """Topic ke sabhi pages (1 to N) ko follow karta hai."""
    all_topic_questions = []
    current_url = base_url
    
    for page_num in range(1, max_pages + 1):
        try:
            res = httpx.get(current_url, headers=HEADERS, timeout=20.0, follow_redirects=True)
            if res.status_code != 200:
                break
                
            page_qs = scrape_single_page(res.text, course_id, topic_id, start_idx=len(all_topic_questions) + 1)
            if not page_qs:
                break
                
            all_topic_questions.extend(page_qs)
            
            # Next page ka URL find karna
            soup = BeautifulSoup(res.text, "html.parser")
            # IndiaBIX pagination container
            pagination = soup.select(".mx-pager-container a, .pagination a")
            next_url = None
            for a in pagination:
                text = a.get_text(strip=True)
                if text.isdigit() and int(text) == page_num + 1:
                    next_url = a.get("href")
                    if next_url and not next_url.startswith("http"):
                        next_url = f"https://www.indiabix.com{next_url}"
                    break
            
            if not next_url:
                break
            current_url = next_url
            
        except Exception as e:
            print(f"Error on {current_url}: {e}")
            break
            
    return all_topic_questions

# Topic list setup
CONFIG_COURSES = [
    {
        "course_id": "aptitude",
        "course_title": "Quantitative Aptitude",
        "icon": "calculate",
        "topics": [
            {
                "topic_id": "time_and_work",
                "topic_title": "Time and Work",
                "url": "https://www.indiabix.com/aptitude/time-and-work/"
            },
            {
                "topic_id": "profit_and_loss",
                "topic_title": "Profit and Loss",
                "url": "https://www.indiabix.com/aptitude/profit-and-loss/"
            },
            {
                "topic_id": "percentage",
                "topic_title": "Percentage",
                "url": "https://www.indiabix.com/aptitude/percentage/"
            }
        ]
    }
]

if __name__ == "__main__":
    master_courses = []
    all_questions = []

    for c in CONFIG_COURSES:
        course_entry = {
            "id": c["course_id"],
            "title": c["course_title"],
            "icon": c["icon"],
            "topics": []
        }
        for t in c["topics"]:
            qs = scrape_all_pages_of_topic(t["url"], c["course_id"], t["topic_id"])
            all_questions.extend(qs)
            course_entry["topics"].append({
                "id": t["topic_id"],
                "title": t["topic_title"],
                "questions_count": len(qs)
            })
        master_courses.append(course_entry)

    output = {
        "courses": master_courses,
        "questions": all_questions
    }

    with open("master_questions.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Extraction complete! Total questions parsed: {len(all_questions)}")
            
