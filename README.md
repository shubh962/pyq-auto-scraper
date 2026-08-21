# ⚡ PYQ Auto-Scraper & Headless Ingestion Engine

An automated, zero-maintenance educational data pipeline that periodically scrapes, cleans, normalizes, and distributes multi-topic competitive exam questions and PYQ solutions.

---

## 🔗 Quick Links

- ⚙️ **Workflow Runner (Manual Trigger):** [GitHub Actions](https://github.com/shubh962/pyq-auto-scraper/actions)
- 📄 **Structured JSON (Repository Preview):** [master_questions.json](https://github.com/shubh962/pyq-auto-scraper/blob/main/master_questions.json)
- 🚀 **Live CDN / API Endpoint (Raw Feed):** [master_questions.json (Raw)](https://raw.githubusercontent.com/shubh962/pyq-auto-scraper/main/master_questions.json?v=latest)

---

## 🏗️ Architecture & Features

- **Zero-Maintenance Automation:** Powered by GitHub Actions (`.github/workflows/scrape.yml`) on a scheduled cron runner.
- **Hierarchical Categorization:** Structures data by **Course $\rightarrow$ Topic $\rightarrow$ Question List** for instant course-based filtering.
- **Smart DOM & Math Parsing:** Converts raw HTML tables and fraction elements into standardized text formats (`(num/den)`).
- **Auto-Pagination:** Recursively crawls multi-page topic archives to fetch full question banks.
- **Offline-First Ready:** Deliverable via a single compressed JSON payload for local caching (SQLite / Hive / AsyncStorage).

---

## 📊 Master Data Schema

The pipeline exports a unified JSON structure consumed directly by client applications:

```json
{
  "courses": [
    {
      "id": "aptitude",
      "title": "Quantitative Aptitude",
      "icon": "calculate",
      "topics": [
        {
          "id": "time_and_work",
          "title": "Time and Work",
          "questions_count": 30
        }
      ]
    }
  ],
  "questions": [
    {
      "id": "time_and_work_1",
      "course_id": "aptitude",
      "topic_id": "time_and_work",
      "question": "A can do a work in 15 days...",
      "options": [
        { "id": "A", "text": "(7/15)" },
        { "id": "B", "text": "(8/15)" }
      ],
      "correct_option": "B",
      "explanation": "A's 1 day's work = (1/15)..."
    }
  ]
}
