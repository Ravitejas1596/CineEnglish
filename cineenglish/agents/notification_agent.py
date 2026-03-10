from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from cineenglish.database.sqlite_db import SqliteDB
from cineenglish.tools.gmail_tool import GmailTool
from cineenglish.tools.report_tool import ReportTool


@dataclass(frozen=True)
class DigestItem:
    word: str
    example_scene: str


class NotificationAgent:
    def __init__(
        self,
        db: SqliteDB | None = None,
        gmail_tool: GmailTool | None = None,
        report_tool: ReportTool | None = None,
    ) -> None:
        self.db = db or SqliteDB()
        self.gmail = gmail_tool or GmailTool()
        self.reports = report_tool or ReportTool()
        self.scheduler = BackgroundScheduler(timezone="UTC")

    # --- Email builders -----------------------------------------------
    def build_daily_email(self, user_id: str) -> tuple[str, str]:
        subject = "🎬 CineEnglish — Your Daily Word Digest"
        recent = self.db.recent_words(user_id, limit=5)
        progress = self.db.progress_overview(user_id)

        header = (
            f"<p>Streak: <b>{progress.get('current_streak', 0)}</b> days · "
            f"Level: <b>{progress.get('level', settings.DEFAULT_LEVEL)}</b></p>"
        )
        rows = []
        for r in recent:
            rows.append(
                f"<tr><td><b>{r['word']}</b></td>"
                f"<td><i>{r.get('scene_context') or ''}</i></td>"
                f"<td>{r.get('source_title') or ''}</td></tr>"
            )
        body = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial;">
          <h2>🎬 Your CineEnglish daily words</h2>
          {header}
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr><th>Word</th><th>Scene</th><th>Source</th></tr>
            </thead>
            <tbody>
              {''.join(rows)}
            </tbody>
          </table>
          <p>Keep watching, keep learning!</p>
        </div>
        """
        return subject, body

    def build_weekly_email(self, user_id: str) -> tuple[str, str]:
        subject = "📊 CineEnglish — Your Weekly Progress"
        stats = self.db.progress_overview(user_id)
        words = stats.get("total_words", 0)
        quizzes = stats.get("quizzes_taken", 0)
        avg = stats.get("avg_score")
        streak = stats.get("current_streak", 0)
        score_text = f"{avg:.1f}%" if isinstance(avg, float) else "n/a"

        encouragement = "Amazing work, keep your streak going! 🔥" if streak >= 3 else "Nice start, try a short session each day. 🙂"

        body = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial;">
          <h2>📊 Your weekly CineEnglish progress</h2>
          <ul>
            <li>Words learned: <b>{words}</b></li>
            <li>Quizzes taken: <b>{quizzes}</b></li>
            <li>Average score: <b>{score_text}</b></li>
            <li>Current streak: <b>{streak}</b> days</li>
          </ul>
          <p>{encouragement}</p>
          <p>Open CineEnglish to keep learning from your favorite shows.</p>
        </div>
        """
        return subject, body

    def build_monthly_email(self, user_id: str, pdf_path: str) -> tuple[str, str]:
        subject = "📄 CineEnglish — Your Monthly Report is Ready!"
        now = datetime.utcnow()
        body = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial;">
          <h2>📄 Your monthly CineEnglish report</h2>
          <p>Your report for {now.strftime('%B %Y')} is ready and attached.</p>
          <p>Open it to see your words learned, quiz performance, and watch time.</p>
        </div>
        """
        return subject, body

    # --- Senders ------------------------------------------------------
    def send_daily(self, user_id: str) -> None:
        subject, body = self.build_daily_email(user_id)
        self.gmail.send_email(subject=subject, body_html=body)

    def send_weekly(self, user_id: str) -> None:
        subject, body = self.build_weekly_email(user_id)
        self.gmail.send_email(subject=subject, body_html=body)

    def send_monthly(self, user_id: str) -> None:
        today = date.today()
        stats = self.db.monthly_stats(user_id, year=today.year, month=today.month)
        pdf_path = self.reports.generate(user_id, stats)
        subject, body = self.build_monthly_email(user_id, pdf_path)
        self.gmail.send_email(subject=subject, body_html=body, attachment=pdf_path)

    # --- Scheduler ----------------------------------------------------
    def start_scheduler(self, user_id: str) -> None:
        h = settings.DAILY_EMAIL_HOUR
        self.scheduler.add_job(
            self.send_daily,
            "cron",
            hour=h,
            minute=0,
            args=[user_id],
            id="daily_email",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.send_weekly,
            "cron",
            day_of_week=settings.WEEKLY_EMAIL_DAY,
            hour=9,
            minute=0,
            args=[user_id],
            id="weekly_email",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.send_monthly,
            "cron",
            day=settings.MONTHLY_EMAIL_DAY,
            hour=8,
            minute=0,
            args=[user_id],
            id="monthly_email",
            replace_existing=True,
        )
        self.scheduler.start()

    def stop_scheduler(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()

