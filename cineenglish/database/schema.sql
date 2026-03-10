CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  created_at TEXT,
  level TEXT DEFAULT 'B1',
  streak_days INTEGER DEFAULT 0,
  last_active TEXT
);

CREATE TABLE IF NOT EXISTS word_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  word TEXT,
  definition TEXT,
  scene_context TEXT,
  source_title TEXT,
  source_type TEXT,
  logged_at TEXT
);

CREATE TABLE IF NOT EXISTS quiz_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  source_title TEXT,
  total_questions INTEGER,
  correct_answers INTEGER,
  score_pct REAL,
  level TEXT,
  taken_at TEXT
);

CREATE TABLE IF NOT EXISTS watch_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  title TEXT,
  media_type TEXT,
  genre TEXT,
  episode TEXT,
  watched_at TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS monthly_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,
  report_month TEXT,
  words_learned INTEGER,
  words_retained INTEGER,
  quizzes_taken INTEGER,
  avg_score REAL,
  level_start TEXT,
  level_end TEXT,
  hours_watched REAL,
  generated_at TEXT
);
