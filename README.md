# 🎬 CineEnglish — Learn English Through Movies & Series

> *Stop studying English. Start watching it.*

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=flat-square&logo=streamlit)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Cost](https://img.shields.io/badge/Cost-$0%20to%20run-brightgreen?style=flat-square)
[![Live App](https://img.shields.io/badge/Live%20App-Open%20CineEnglish-red?style=flat-square&logo=streamlit)](https://cineenglish-movierecommender.streamlit.app)

---
## 🌐 Live Demo

**Try it now → [https://cineenglish-movierecommender.streamlit.app](https://cineenglish-movierecommender.streamlit.app)**

> No installation needed. Open the link, pick a genre, and start learning.

## 💡 Why I Built This

Learning English from textbooks never worked for me.

Vocabulary lists with no context. Grammar drills with no soul.
You memorize a word on Monday and forget it by Wednesday —
because you never *heard* it used by a real person in a real moment.

Then one day I was watching **Suits**, and Harvey Specter said
*"I don't have dreams, I have goals"* — and I looked up every word
in that sentence. I remembered all of them. Still do.

That's when it clicked: **the best way to learn English is through
content you actually care about.**

CineEnglish is my attempt to build that system — a multi-agent AI
app that turns any movie, series, or YouTube clip into a personalized
English lesson. It watches what you watch, pulls out the vocabulary
that matters, quizzes you on it, and tracks your progress over time.

No boring word lists. No abstract grammar rules.
Just you, your favorite shows, and real English — in context.

---

## ✨ What It Does

CineEnglish has 4 core features:

### 🎬 1. Recommendations
Tell the app your mood and genre — it recommends movies and series
matched to your current English level (CEFR A1–C2).

- Choose: Movies or Series
- Pick a genre: Drama, Comedy, Crime & Thriller, Sci-Fi, Action
- Refine by mood: intense vs light, challenge vs comfort
- Get cards with title, rating, poster, and *why this is good for your level*
- Click "I'll watch this" → it automatically finds a YouTube clip,
  extracts vocabulary, and has a quiz ready for you

### 📝 2. Vocab & Quiz
Paste any YouTube video URL or upload a local file — CineEnglish
extracts the most useful vocabulary from the subtitles and builds
a personalized multiple-choice quiz on the spot.

- YouTube URL or local video/subtitle file
- Automatic subtitle fetching + smart word extraction
- Definitions pulled from Free Dictionary API with scene context
- AI-generated quiz questions (not just definitions — context-based)
- Results saved to your personal word library

### 📚 3. Word Library
Every word you've ever learned — organized by the show or clip
it came from. Your personal dictionary, built from your own
watching history.

- Browse words by source (Suits S01E01, Breaking Bad clip, etc.)
- See the exact scene where you learned each word
- Rebuild a fresh quiz from any source anytime
- Semantic search across your entire vocabulary bank

### 🎓 4. Coach Chat
Talk to your AI English coach. Ask about your progress, request
recommendations, or just practice English conversation. The coach
remembers your history and gives you personalized feedback.

- Natural conversation with context memory
- Progress summaries with stats and streaks
- Quick actions: "How am I doing?", "Quiz me", "What to watch?"
- Email notifications for daily word digest + weekly progress
- One-click monthly PDF report generation

---

## 🤖 How It Works — The Multi-Agent System

CineEnglish is powered by **6 AI agents** that coordinate with
each other using LangGraph:
```
User
  │
  ▼
┌─────────────────────────────────────┐
│          MAESTRO AGENT              │
│  Orchestrates all other agents.     │
│  Handles conversation, routes       │
│  intents, tracks user progress.     │
└──────────────┬──────────────────────┘
               │
     ┌─────────┼──────────┬───────────┐
     ▼         ▼          ▼           ▼
┌─────────┐ ┌───────┐ ┌───────┐ ┌──────────┐
│RECOMMEND│ │SUBTITLE│ │TEACH- │ │NOTIFICA- │
│  AGENT  │ │ AGENT  │ │  ING  │ │  TION    │
│         │ │        │ │ AGENT │ │  AGENT   │
│Finds    │ │Fetches │ │Builds │ │Sends     │
│movies   │ │subs,   │ │quizzes│ │Gmail     │
│via TMDB │ │extracts│ │via    │ │digests + │
│by genre │ │vocab   │ │Groq   │ │reports   │
│+ level  │ │        │ │       │ │          │
└─────────┘ └───┬────┘ └───────┘ └──────────┘
                │
                ▼
         ┌────────────┐
         │ DICTIONARY │
         │   AGENT    │
         │            │
         │Looks up    │
         │definitions,│
         │examples,   │
         │phonetics   │
         └────────────┘
                │
                ▼
    ┌───────────────────────┐
    │  ChromaDB + SQLite    │
    │  Remembers everything │
    └───────────────────────┘
```

### Agent Responsibilities

| Agent | What It Does |
|---|---|
| **MaestroAgent** | Orchestrates all agents, handles Coach Chat, classifies user intent, recalls memory |
| **RecommenderAgent** | Queries TMDB API, filters by genre + level, returns recommendation cards |
| **SubtitleAgent** | Fetches YouTube transcripts or file subtitles, extracts high-value vocabulary |
| **DictionaryAgent** | Looks up definitions, phonetics, examples via Free Dictionary API |
| **TeachingAgent** | Builds context-aware multiple-choice quizzes using Groq LLM |
| **NotificationAgent** | Sends HTML email digests, weekly snapshots, monthly PDF reports via Gmail |

---

## 🧠 Memory Architecture

CineEnglish uses a **two-layer memory system** to remember you
across sessions:
```
┌─────────────────────────────────────────────┐
│               ChromaDB (Vector)             │
│                                             │
│  user_conversations  →  semantic chat recall│
│  vocabulary_bank     →  word search by meaning│
│                                             │
│  Embeddings: all-MiniLM-L6-v2 (local, free)│
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│               SQLite (Structured)           │
│                                             │
│  word_logs      →  every word you learned   │
│  quiz_results   →  every quiz you took      │
│  watch_history  →  everything you watched   │
│  monthly_reports→  archived monthly stats   │
└─────────────────────────────────────────────┘
```

---

## 📧 Email Notifications

CineEnglish sends you real HTML emails via Gmail API:

| Email | When | Contains |
|---|---|---|
| Daily Digest | Every morning 8AM | 5 words from recent watching + streak |
| Weekly Snapshot | Every Monday | Stats, progress bar, what to watch next |
| Monthly Report | 1st of every month | Full PDF attached with level change + highlights |

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **UI** | Streamlit | Fast, Python-native, no frontend needed |
| **Agents** | LangGraph | Stateful multi-agent graph coordination |
| **LLM** | Groq — Llama 3.3 70B | Free tier, ultra fast inference |
| **Vector Memory** | ChromaDB | Local persistent vector store |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Local, free, no API needed |
| **Structured DB** | SQLite | Zero-config, local, perfect for single user |
| **Movie Data** | TMDB API | Free, rich metadata, posters |
| **Subtitles** | youtube-transcript-api + subliminal | YouTube primary, multi-source fallback |
| **Dictionary** | Free Dictionary API | No key needed, clean JSON |
| **Email** | Gmail API (OAuth2) | Free, reliable, HTML templates |
| **Scheduler** | APScheduler | Background jobs for daily/weekly/monthly emails |
| **PDF Reports** | ReportLab | Professional PDF generation, free |

**Total monthly cost to run: $0**

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A Groq account (free) → [console.groq.com](https://console.groq.com)
- A TMDB account (free) → [themoviedb.org](https://www.themoviedb.org)
- A Gmail account + Google Cloud project (for email notifications)

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/cineenglish.git
cd cineenglish

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and fill in your API keys
```

### Environment Variables
```env
GROQ_API_KEY=your_groq_api_key
TMDB_API_KEY=your_tmdb_api_key
GMAIL_SENDER=your_email@gmail.com
```

### Gmail Setup (One Time)
```
1. Go to console.cloud.google.com
2. Create a new project
3. Enable the Gmail API
4. Go to APIs & Services → Credentials
5. Create OAuth 2.0 Client ID → Desktop App
6. Download JSON → rename to credentials.json
7. Place credentials.json in project root
8. First run will open browser for one-time login
```

### Run the App
```bash
streamlit run main.py
```

Open [http://localhost:8501](http://localhost:8501) 🎬

---

## 📁 Project Structure
```
cineenglish/
├── main.py                        # Streamlit entry point
├── config.py                      # All settings + API config
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── maestro_agent.py           # Orchestrator + Coach Chat
│   ├── recommender_agent.py       # Movie/series suggestions
│   ├── subtitle_agent.py          # Subtitle fetch + vocab extraction
│   ├── dictionary_agent.py        # Word definitions + phonetics
│   ├── teaching_agent.py          # Quiz generation via Groq
│   └── notification_agent.py      # Email scheduler + templates
│
├── memory/
│   ├── chroma_store.py            # ChromaDB operations
│   └── conversation_memory.py     # 3-layer memory system
│
├── tools/
│   ├── tmdb_tool.py               # TMDB API wrapper
│   ├── gmail_tool.py              # Gmail send + OAuth
│   └── report_tool.py             # PDF report generator
│
├── database/
│   ├── sqlite_db.py               # All DB operations
│   └── schema.sql                 # Table definitions
│
├── ui/
│   ├── recommendations_tab.py     # Tab 1
│   ├── vocab_quiz_tab.py          # Tab 2
│   ├── word_library_tab.py        # Tab 3
│   └── coach_chat_tab.py          # Tab 4
│
└── data/
    ├── chroma_db/                 # Vector store (auto-created)
    └── reports/                   # Generated PDFs (auto-created)
```

---

## 🗺️ Roadmap

- [x] Multi-agent LangGraph architecture
- [x] YouTube + file subtitle extraction
- [x] AI quiz generation
- [x] Word library with source tracking
- [x] Coach Chat with memory
- [x] Gmail notifications + monthly PDF
- [x] Dark cinema UI theme
- [ ] Personalized recommendations using watch history
- [ ] Spaced repetition word review system
- [ ] Accent detection (American vs British vs Australian)
- [ ] Shadowing mode — repeat after characters
- [ ] Multi-user support
- [ ] Mobile-friendly layout
- [ ] Export vocabulary to Anki deck

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for new features,
open an issue first to discuss what you'd like to change.
```bash
# Fork the repo
# Create your feature branch
git checkout -b feature/shadowing-mode

# Commit your changes
git commit -m "Add shadowing mode for pronunciation practice"

# Push to branch
git push origin feature/shadowing-mode

# Open a Pull Request
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) — for blazing fast free LLM inference
- [TMDB](https://www.themoviedb.org) — for the movie database
- [LangChain](https://langchain.com) — for agent tooling
- [Streamlit](https://streamlit.io) — for making Python UIs painless
- Harvey Specter — for teaching me what "litigation" means

---

<p align="center">
  Built with ❤️ for anyone who ever paused a show to look up a word.
</p>
