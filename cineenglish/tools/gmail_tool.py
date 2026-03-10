from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HtmlEmail:
    to: str
    subject: str
    html: str


class GmailTool:
    def __init__(
        self,
        credentials_file: str | None = None,
        token_file: str | None = None,
        sender: str | None = None,
        scopes: List[str] | None = None,
    ) -> None:
        self.credentials_file = credentials_file or settings.GMAIL_CREDENTIALS_FILE
        self.token_file = token_file or settings.GMAIL_TOKEN_FILE
        self.sender = sender or settings.GMAIL_SENDER
        self.scopes = scopes or settings.GMAIL_SCOPES
        self.service = None

    # Authentication ---------------------------------------------------
    def _authenticate(self) -> None:
        creds: Credentials | None = None
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                "credentials.json not found. "
                "Download it from Google Cloud Console → "
                "APIs & Services → Credentials → OAuth 2.0 Client → Download JSON. "
                "Rename to credentials.json and place in project root."
            )
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
        self.service = build("gmail", "v1", credentials=creds)

    def _build_message(
        self, to: str, subject: str, html_body: str, attachment_path: str | None = None
    ) -> dict:
        if attachment_path:
            message = MIMEMultipart("mixed")
            alt_part = MIMEMultipart("alternative")
            alt_part.attach(MIMEText(html_body, "html"))
            message.attach(alt_part)

            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), _subtype="pdf")
                filename = os.path.basename(attachment_path)
                part.add_header("Content-Disposition", "attachment", filename=filename)
                message.attach(part)
        else:
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(html_body, "html"))

        message["To"] = to
        message["From"] = self.sender
        message["Subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw}

    # Public senders ---------------------------------------------------
    def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        attachment_path: str | None = None,
    ) -> bool:
        try:
            if self.service is None:
                self._authenticate()
            if attachment_path and not Path(attachment_path).exists():
                logger.error("Attachment not found: %s", attachment_path)
                attachment_path = None
            msg = self._build_message(to, subject, html_body, attachment_path)
            self.service.users().messages().send(userId="me", body=msg).execute()
            return True
        except Exception as e:  # pragma: no cover
            logger.error("Failed to send Gmail message: %s", e)
            return False

    def send_daily_digest(self, to: str, words: List[dict], streak: int) -> bool:
        subject = "🎬 CineEnglish — Your Daily Word Digest"
        header = f"<h2>Your words for today 🎯</h2><p>🔥 {streak} day streak</p>"
        blocks = []
        for w in words:
            blocks.append(
                f"""
                <div style="margin:16px 0; padding:12px; border-left:4px solid #e50914">
                  <strong style="font-size:18px">{w.get('word')}</strong>
                  <span style="color:#666">({w.get('part_of_speech','')})</span><br>
                  <em>{w.get('definition','')}</em><br>
                  <small style="color:#999">"{w.get('scene_context','')}"</small>
                </div>
                """
            )
        footer = (
            '<div style="margin-top:24px;padding:12px;background:#111;color:#fff;'
            'text-align:center;">Keep watching, keep learning! 🎬</div>'
        )
        body = (
            '<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial;">'
            f"{header}{''.join(blocks)}{footer}</div>"
        )
        return self.send_email(to=to, subject=subject, html_body=body)

    def send_weekly_snapshot(self, to: str, stats: dict) -> bool:
        subject = "📊 CineEnglish — Weekly Progress Report"
        words = stats.get("words_learned", 0)
        quizzes = stats.get("quizzes_taken", 0)
        avg = stats.get("avg_score")
        streak = stats.get("streak", 0)
        level = stats.get("level", settings.DEFAULT_LEVEL)
        avg_text = f"{avg:.1f}%" if isinstance(avg, float) else "n/a"

        if isinstance(avg, float) and avg >= 80:
            msg = "Outstanding! You're on fire 🔥"
        elif isinstance(avg, float) and avg >= 60:
            msg = "Good progress! Keep it up 💪"
        else:
            msg = "Keep practicing — consistency is key 📚"

        body = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial;">
          <h2>Your week in review 📈</h2>
          <div style="display:flex;gap:12px;flex-wrap:wrap;">
            <div style="flex:1;min-width:120px;padding:12px;border:1px solid #eee;">
              <div style="font-size:24px;font-weight:bold;">{words}</div>
              <div>Words Learned</div>
            </div>
            <div style="flex:1;min-width:120px;padding:12px;border:1px solid #eee;">
              <div style="font-size:24px;font-weight:bold;">{quizzes}</div>
              <div>Quizzes Taken</div>
            </div>
            <div style="flex:1;min-width:120px;padding:12px;border:1px solid #eee;">
              <div style="font-size:24px;font-weight:bold;">{avg_text}</div>
              <div>Avg Score</div>
            </div>
            <div style="flex:1;min-width:120px;padding:12px;border:1px solid #eee;">
              <div style="font-size:24px;font-weight:bold;">{streak}</div>
              <div>Day Streak</div>
            </div>
          </div>
          <p>Level: <b>{level}</b></p>
          <p>{msg}</p>
          <a href="#" style="display:inline-block;margin-top:16px;padding:10px 18px;background:#e50914;color:#fff;text-decoration:none;border-radius:4px;">Open CineEnglish</a>
        </div>
        """
        return self.send_email(to=to, subject=subject, html_body=body)

    def send_monthly_report(self, to: str, stats: dict, pdf_path: str) -> bool:
        subject = f"📄 CineEnglish — Your {stats.get('month_name','This Month')} Report is Ready!"
        level_change = f"{stats.get('level_start','')} → {stats.get('level_end','')}"
        body = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial;">
          <h2>Your {stats.get('month_name','')} {stats.get('year','')} report</h2>
          <ul>
            <li>Words Learned: <b>{stats.get('words_learned',0)}</b></li>
            <li>Level Change: <b>{level_change}</b></li>
            <li>Average Score: <b>{stats.get('avg_score','n/a')}</b></li>
          </ul>
          <p>Your full report is attached as a PDF.</p>
          <p>Great job this month — let's make next month even better!</p>
        </div>
        """
        return self.send_email(to=to, subject=subject, html_body=body, attachment_path=pdf_path)


