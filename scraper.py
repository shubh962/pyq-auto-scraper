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

# ----------------- 1. Primary Source: IndiaBIX -----------------
def scrape_indiabix(url: str, course_id: str, topic_id: str):
    questions = []
    try:
        res = httpx.get(url, headers=HEADERS, timeout=12.0, follow_redirects=True)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
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
                    "id": f"{topic_id}_{idx+1}",
                    "source": "IndiaBIX",
                    "course_id": course_id,
                    "topic_id": topic_id,
                    "question": q_text,
                    "options": options,
                    "correct_option": correct_ans,
                    "explanation": explanation
                })
    except Exception as e:
        print(f"[IndiaBIX Failed] {url} -> {e}")
    return questions

# ----------------- 2. Fallback 1: Notopedia -----------------
def scrape_notopedia_fallback(url: str, course_id: str, topic_id: str):
    questions = []
    try:
        res = httpx.get(url, headers=HEADERS, timeout=12.0, follow_redirects=True)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".question-box, .post-content, .card")
            for idx, card in enumerate(cards):
                q_el = card.select_one("h2, h3, .q-title, p")
                if not q_el:
                    continue
                q_text = clean_text(q_el.get_text(strip=True))
                exp_el = card.select_one(".answer, .solution, .explanation")
                explanation = clean_text(exp_el.get_text(strip=True)) if exp_el else None

                questions.append({
                    "id": f"{topic_id}_noto_{idx+1}",
                    "source": "Notopedia",
                    "course_id": course_id,
                    "topic_id": topic_id,
                    "question": q_text,
                    "options": [],
                    "correct_option": None,
                    "explanation": explanation
                })
    except Exception as e:
        print(f"[Notopedia Fallback Failed] {url} -> {e}")
    return questions

# ----------------- 3. Fallback 2: Magnet Brains -----------------
def scrape_magnetbrains_fallback(url: str, course_id: str, topic_id: str):
    questions = []
    try:
        res = httpx.get(url, headers=HEADERS, timeout=12.0, follow_redirects=True)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            summary_block = soup.select_one(".chapter-summary, .course-description, article")
            if summary_block:
                summary_text = clean_text(summary_block.get_text(separator="\n", strip=True))
                questions.append({
                    "id": f"{topic_id}_mb_note",
                    "source": "MagnetBrains",
                    "course_id": course_id,
                    "topic_id": topic_id,
                    "question": f"Key Conceptual Summary for {topic_id.replace('_', ' ').title()}",
                    "options": [],
                    "correct_option": None,
                    "explanation": summary_text
                })
    except Exception as e:
        print(f"[MagnetBrains Fallback Failed] {url} -> {e}")
    return questions

# ----------------- Configuration with Multi-Source Fallbacks -----------------
CONFIG_COURSES = [
    {
        "course_id": "aptitude_placement",
        "course_title": "Quantitative Aptitude",
        "icon": "calculate",
        "topics": [
            {
                "topic_id": "time_and_work",
                "topic_title": "Time and Work",
                "primary_url": "https://www.indiabix.com/aptitude/time-and-work/",
                "fallback_notopedia": "https://www.notopedia.com/study-material/aptitude/time-and-work",
                "fallback_magnetbrains": "https://www.magnetbrains.com/course/class-10-maths-work-time"
            },
            {
                "topic_id": "profit_and_loss",
                "topic_title": "Profit and Loss",
                "primary_url": "https://www.indiabix.com/aptitude/profit-and-loss/",
                "fallback_notopedia": "https://www.notopedia.com/study-material/aptitude/profit-and-loss",
                "fallback_magnetbrains": "https://www.magnetbrains.com/course/class-10-maths-profit-loss"
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
            # 1. Try Primary (IndiaBIX)
            qs = scrape_indiabix(t["primary_url"], c["course_id"], t["topic_id"])
            
            # 2. Fallback to Notopedia if Primary fails or is empty
            if not qs and "fallback_notopedia" in t:
                print(f"Fallback triggered for {t['topic_id']} -> Notopedia")
                qs = scrape_notopedia_fallback(t["fallback_notopedia"], c["course_id"], t["topic_id"])
            
            # 3. Fallback to Magnet Brains if secondary also fails
            if not qs and "fallback_magnetbrains" in t:
                print(f"Fallback triggered for {t['topic_id']} -> Magnet Brains")
                qs = scrape_magnetbrains_fallback(t["fallback_magnetbrains"], c["course_id"], t["topic_id"])

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

    print(f"Data sync complete: {len(all_questions)} questions processed.")
    
