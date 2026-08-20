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

# Configure all courses and their topic URLs here
CONFIG_COURSES = [
    {
        "course_id": "aptitude_placement",
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
    },
    {
        "course_id": "cs_engineering",
        "course_title": "Computer Science (C / Data Structures)",
        "icon": "code",
        "topics": [
            {
                "topic_id": "c_pointers",
                "topic_title": "C Programming - Pointers",
                "url": "https://www.indiabix.com/c-programming/pointers/"
            }
        ]
    }
]

def scrape_topic_questions(url: str, course_id: str, topic_id: str):
    questions = []
    try:
        res = httpx.get(url, headers=HEADERS, timeout=20.0, follow_redirects=True)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            containers = soup.select(".bix-div-container")
            
            for idx, c in enumerate(containers):
                q_text_el = c.select_one(".bix-td-qtxt")
                if not q_text_el:
                    continue
                q_text = clean_text(q_text_el.get_text(separator=" ", strip=True))

                # Options
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

                # Fallback options
                if not options:
                    for opt_letter in ["A", "B", "C", "D"]:
                        opt_val = c.select_one(f"#ibx_opt_{opt_letter}_{idx+1}, .opt-{opt_letter.lower()}")
                        if opt_val:
                            options.append({"id": opt_letter, "text": clean_text(opt_val.get_text(strip=True))})

                # Correct Answer
                ans_input = c.select_one("input.jq-hdnakqb, input[name^='hdnAnq']")
                correct_ans = ans_input.get("value", "").strip().upper() if ans_input else None

                # Explanation
                exp_el = c.select_one(".bix-ans-description, .div-explanation")
                explanation = clean_text(exp_el.get_text(separator=" ", strip=True)) if exp_el else None

                questions.append({
                    "id": f"{topic_id}_{idx+1}",
                    "course_id": course_id,
                    "topic_id": topic_id,
                    "question": q_text,
                    "options": options,
                    "correct_option": correct_ans,
                    "explanation": explanation
                })
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return questions

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
            qs = scrape_topic_questions(t["url"], c["course_id"], t["topic_id"])
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

    print(f"Done! Scraped {len(all_questions)} questions across {len(master_courses)} courses.")
    
