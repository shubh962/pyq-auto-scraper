import httpx
from bs4 import BeautifulSoup
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def clean_element_text(element):
    """HTML elements se clean human-readable text banata hai, including math fractions."""
    if not element:
        return ""
    
    # Handle HTML fraction tables (e.g. 7 / 15)
    for table in element.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) == 2:
            num = rows[0].get_text(strip=True)
            den = rows[1].get_text(strip=True)
            table.replace_with(f" {num}/{den} ")
        else:
            table.replace_with(f" {table.get_text(separator=' ', strip=True)} ")

    text = element.get_text(separator=" ", strip=True)
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_question_container(c, topic_id, q_number):
    # 1. Question Text
    q_txt_elem = c.select_one(".bix-td-qtxt, .bix-qtxt")
    if not q_txt_elem:
        return None
    question_text = clean_element_text(q_txt_elem)

    # 2. Options Extraction (Universal matcher)
    options = []
    
    # Strategy A: Match flex/grid option divs
    opt_divs = c.select(".bix-div-option, .bix-opt-row, .d-flex.flex-row")
    for d in opt_divs:
        order = d.select_one(".bix-opt-order, .bix-td-option-order, [class*='order']")
        val = d.select_one(".bix-opt-desc, .bix-td-option-val, [class*='desc'], [class*='val']")
        if order and val:
            letter = clean_element_text(order).replace(".", "").replace("(", "").replace(")", "").strip().upper()
            txt = clean_element_text(val)
            if letter in ["A", "B", "C", "D", "E"] and txt:
                options.append({"id": letter, "text": txt})

    # Strategy B: Match table rows if Strategy A got nothing
    if not options:
        opt_rows = c.select("table.bix-tbl-options tr, tr[id*='trOption']")
        for r in opt_rows:
            tds = r.find_all("td")
            if len(tds) >= 2:
                letter = clean_element_text(tds[0]).replace(".", "").replace("(", "").replace(")", "").strip().upper()
                txt = clean_element_text(tds[1])
                if letter in ["A", "B", "C", "D", "E"] and txt:
                    options.append({"id": letter, "text": txt})

    # Strategy C: Raw regex fallback from container text
    if not options:
        raw_c_text = c.get_text("\n")
        matches = re.findall(r'([A-D])[\.\)]\s*([^\n\r]+)', raw_c_text)
        for letter, txt in matches:
            options.append({"id": letter.upper(), "text": clean_element_text(BeautifulSoup(txt, "html.parser"))})

    # Deduplicate options
    seen = set()
    unique_options = []
    for opt in options:
        if opt["id"] not in seen:
            seen.add(opt["id"])
            unique_options.append(opt)

    # 3. Correct Answer Extraction
    correct_option = None
    
    # Check hidden inputs first
    ans_inp = c.select_one("input[name^='hdnAnq'], input.jq-hdnakqb, input[id^='hdnAnq']")
    if ans_inp and ans_inp.get("value"):
        val = ans_inp.get("value").strip().upper()
        if val in ["A", "B", "C", "D", "E"]:
            correct_option = val
        elif val.isdigit():
            idx_map = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}
            correct_option = idx_map.get(val)

    # If not found, parse answer text block
    if not correct_option:
        ans_block = c.select_one(".bix-div-answer, .jq-pnl-answer, .pnl-answer")
        if ans_block:
            m = re.search(r'Answer:\s*Option\s*([A-E])', ans_block.get_text(), re.IGNORECASE)
            if m:
                correct_option = m.group(1).upper()

    # 4. Explanation Extraction
    exp_block = c.select_one(".bix-ans-description, .div-explanation")
    explanation = clean_element_text(exp_block) if exp_block else None

    return {
        "id": f"{topic_id}_{q_number}",
        "question": question_text,
        "options": unique_options,
        "correct_option": correct_option,
        "explanation": explanation
    }

def scrape_topic(url, course_id, topic_id, max_pages=3):
    questions = []
    current_url = url
    q_counter = 1

    for page in range(1, max_pages + 1):
        try:
            res = httpx.get(current_url, headers=HEADERS, timeout=20.0, follow_redirects=True)
            if res.status_code != 200:
                break
            
            soup = BeautifulSoup(res.text, "html.parser")
            containers = soup.select(".bix-div-container")
            if not containers:
                break

            for c in containers:
                q_data = parse_question_container(c, topic_id, q_counter)
                if q_data and q_data["question"]:
                    q_data["course_id"] = course_id
                    q_data["topic_id"] = topic_id
                    questions.append(q_data)
                    q_counter += 1

            # Next page check
            next_link = soup.find("a", string=str(page + 1))
            if next_link and next_link.get("href"):
                next_url = next_link.get("href")
                current_url = next_url if next_url.startswith("http") else f"https://www.indiabix.com{next_url}"
            else:
                break
        except Exception as e:
            print(f"Error scraping {current_url}: {e}")
            break

    return questions

CONFIG = [
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
    courses_out = []
    all_questions = []

    for c in CONFIG:
        c_entry = {
            "id": c["course_id"],
            "title": c["course_title"],
            "icon": c["icon"],
            "topics": []
        }
        for t in c["topics"]:
            qs = scrape_topic(t["url"], c["course_id"], t["topic_id"], max_pages=3)
            all_questions.extend(qs)
            c_entry["topics"].append({
                "id": t["topic_id"],
                "title": t["topic_title"],
                "questions_count": len(qs)
            })
        courses_out.append(c_entry)

    master_payload = {
        "courses": courses_out,
        "questions": all_questions
    }

    with open("master_questions.json", "w", encoding="utf-8") as f:
        json.dump(master_payload, f, ensure_ascii=False, indent=2)

    print(f"DONE. Total Questions: {len(all_questions)}")
    
