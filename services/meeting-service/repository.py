from abc import ABC, abstractmethod
from typing import List, Optional
import sqlite3
from datetime import datetime
from pydantic import BaseModel, Field

class Participant(BaseModel):
    id: Optional[int] = None
    meeting_id: Optional[int] = None
    participant_email: str
    participant_name: Optional[str] = None

class Meeting(BaseModel):
    id: Optional[int] = None
    user_id: str
    source_email_id: str
    source_platform: str  # 'gmail', 'outlook', 'ics', 'manual'
    meeting_platform: str  # 'Google Meet', 'Microsoft Teams', 'Zoom', 'Other'
    meeting_url: Optional[str] = None
    meeting_title: str
    description: Optional[str] = None
    organizer: Optional[str] = None
    start_datetime: str  # ISO-8601 string
    end_datetime: str  # ISO-8601 string
    prev_start_datetime: Optional[str] = None
    prev_end_datetime: Optional[str] = None
    status: str  # 'Pending', 'Confirmed', 'Updated', 'Cancelled', 'Dismissed'
    calendar_added_flag: int = 0  # 0 or 1
    reminder_1_day_sent: int = 0  # 0 or 1
    reminder_1_hour_sent: int = 0  # 0 or 1
    created_timestamp: str
    updated_timestamp: str
    participants: List[Participant] = []

class MeetingRepository(ABC):
    @abstractmethod
    def initialize_db(self) -> None:
        pass

    @abstractmethod
    def create_meeting(self, meeting: Meeting) -> Meeting:
        pass

    @abstractmethod
    def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        pass

    @abstractmethod
    def get_meeting_by_source_email(self, user_id: str, source_email_id: str) -> Optional[Meeting]:
        pass

    @abstractmethod
    def get_meeting_by_url(self, user_id: str, meeting_url: str) -> Optional[Meeting]:
        pass

    @abstractmethod
    def get_meeting_by_title_and_organizer(self, user_id: str, title: str, organizer: str) -> Optional[Meeting]:
        pass

    @abstractmethod
    def update_meeting(self, meeting: Meeting) -> Meeting:
        pass

    @abstractmethod
    def delete_meeting(self, meeting_id: int) -> bool:
        pass

    @abstractmethod
    def list_meetings(self, user_id: str, calendar_added_only: bool = False) -> List[Meeting]:
        pass

    @abstractmethod
    def list_pending_meetings(self, user_id: str) -> List[Meeting]:
        pass

    @abstractmethod
    def list_upcoming_meetings(self, user_id: str) -> List[Meeting]:
        pass


class SQLiteMeetingRepository(MeetingRepository):
    def __init__(self, db_path: str = "meetings.db"):
        self.db_path = db_path
        self.initialize_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_db(self) -> None:
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    source_email_id TEXT NOT NULL,
                    source_platform TEXT NOT NULL,
                    meeting_platform TEXT NOT NULL,
                    meeting_url TEXT,
                    meeting_title TEXT NOT NULL,
                    description TEXT,
                    organizer TEXT,
                    start_datetime TEXT NOT NULL,
                    end_datetime TEXT NOT NULL,
                    prev_start_datetime TEXT,
                    prev_end_datetime TEXT,
                    status TEXT NOT NULL,
                    calendar_added_flag INTEGER DEFAULT 0,
                    reminder_1_day_sent INTEGER DEFAULT 0,
                    reminder_1_hour_sent INTEGER DEFAULT 0,
                    created_timestamp TEXT NOT NULL,
                    updated_timestamp TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meeting_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id INTEGER NOT NULL,
                    participant_email TEXT NOT NULL,
                    participant_name TEXT,
                    FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_meetings_user ON meetings(user_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_meetings_url ON meetings(meeting_url);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_meetings_title_org ON meetings(meeting_title, organizer);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_meeting ON meeting_participants(meeting_id);")
            conn.commit()
        finally:
            conn.close()

    def create_meeting(self, meeting: Meeting) -> Meeting:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meetings (
                    user_id, source_email_id, source_platform, meeting_platform, meeting_url,
                    meeting_title, description, organizer, start_datetime, end_datetime,
                    prev_start_datetime, prev_end_datetime, status, calendar_added_flag,
                    reminder_1_day_sent, reminder_1_hour_sent, created_timestamp, updated_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting.user_id, meeting.source_email_id, meeting.source_platform, meeting.meeting_platform,
                meeting.meeting_url, meeting.meeting_title, meeting.description, meeting.organizer,
                meeting.start_datetime, meeting.end_datetime, meeting.prev_start_datetime, meeting.prev_end_datetime,
                meeting.status, meeting.calendar_added_flag, meeting.reminder_1_day_sent, meeting.reminder_1_hour_sent,
                meeting.created_timestamp, meeting.updated_timestamp
            ))
            meeting_id = cursor.lastrowid
            meeting.id = meeting_id

            for p in meeting.participants:
                cursor.execute("""
                    INSERT INTO meeting_participants (meeting_id, participant_email, participant_name)
                    VALUES (?, ?, ?)
                """, (meeting_id, p.participant_email, p.participant_name))
                p.meeting_id = meeting_id
            
            conn.commit()
            return meeting
        finally:
            conn.close()

    def _row_to_meeting(self, row, conn) -> Meeting:
        m_dict = dict(row)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meeting_participants WHERE meeting_id = ?", (m_dict["id"],))
        p_rows = cursor.fetchall()
        participants = []
        for pr in p_rows:
            participants.append(Participant(
                id=pr["id"],
                meeting_id=pr["meeting_id"],
                participant_email=pr["participant_email"],
                participant_name=pr["participant_name"]
            ))
        m_dict["participants"] = participants
        return Meeting(**m_dict)

    def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_meeting(row, conn)
            return None
        finally:
            conn.close()

    def get_meeting_by_source_email(self, user_id: str, source_email_id: str) -> Optional[Meeting]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meetings WHERE user_id = ? AND source_email_id = ?", (user_id, source_email_id))
            row = cursor.fetchone()
            if row:
                return self._row_to_meeting(row, conn)
            return None
        finally:
            conn.close()

    def get_meeting_by_url(self, user_id: str, meeting_url: str) -> Optional[Meeting]:
        if not meeting_url:
            return None
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meetings WHERE user_id = ? AND meeting_url = ?", (user_id, meeting_url))
            row = cursor.fetchone()
            if row:
                return self._row_to_meeting(row, conn)
            return None
        finally:
            conn.close()

    def get_meeting_by_title_and_organizer(self, user_id: str, title: str, organizer: str) -> Optional[Meeting]:
        if not title:
            return None
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            if organizer:
                cursor.execute(
                    "SELECT * FROM meetings WHERE user_id = ? AND meeting_title = ? AND organizer = ?",
                    (user_id, title, organizer)
                )
            else:
                cursor.execute(
                    "SELECT * FROM meetings WHERE user_id = ? AND meeting_title = ? AND organizer IS NULL",
                    (user_id, title)
                )
            row = cursor.fetchone()
            if row:
                return self._row_to_meeting(row, conn)
            return None
        finally:
            conn.close()

    def update_meeting(self, meeting: Meeting) -> Meeting:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE meetings SET
                    user_id = ?, source_email_id = ?, source_platform = ?, meeting_platform = ?, meeting_url = ?,
                    meeting_title = ?, description = ?, organizer = ?, start_datetime = ?, end_datetime = ?,
                    prev_start_datetime = ?, prev_end_datetime = ?, status = ?, calendar_added_flag = ?,
                    reminder_1_day_sent = ?, reminder_1_hour_sent = ?, created_timestamp = ?, updated_timestamp = ?
                WHERE id = ?
            """, (
                meeting.user_id, meeting.source_email_id, meeting.source_platform, meeting.meeting_platform,
                meeting.meeting_url, meeting.meeting_title, meeting.description, meeting.organizer,
                meeting.start_datetime, meeting.end_datetime, meeting.prev_start_datetime, meeting.prev_end_datetime,
                meeting.status, meeting.calendar_added_flag, meeting.reminder_1_day_sent, meeting.reminder_1_hour_sent,
                meeting.created_timestamp, meeting.updated_timestamp, meeting.id
            ))
            
            cursor.execute("DELETE FROM meeting_participants WHERE meeting_id = ?", (meeting.id,))
            for p in meeting.participants:
                cursor.execute("""
                    INSERT INTO meeting_participants (meeting_id, participant_email, participant_name)
                    VALUES (?, ?, ?)
                """, (meeting.id, p.participant_email, p.participant_name))
                p.meeting_id = meeting.id
                
            conn.commit()
            return meeting
        finally:
            conn.close()

    def delete_meeting(self, meeting_id: int) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_meetings(self, user_id: str, calendar_added_only: bool = False) -> List[Meeting]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            if calendar_added_only:
                cursor.execute(
                    "SELECT * FROM meetings WHERE user_id = ? AND calendar_added_flag = 1 ORDER BY start_datetime ASC",
                    (user_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM meetings WHERE user_id = ? ORDER BY start_datetime ASC",
                    (user_id,)
                )
            rows = cursor.fetchall()
            return [self._row_to_meeting(row, conn) for row in rows]
        finally:
            conn.close()

    def list_pending_meetings(self, user_id: str) -> List[Meeting]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM meetings WHERE user_id = ? AND calendar_added_flag = 0 AND status != 'Dismissed' ORDER BY start_datetime ASC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [self._row_to_meeting(row, conn) for row in rows]
        finally:
            conn.close()

    def list_upcoming_meetings(self, user_id: str) -> List[Meeting]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            now_str = datetime.utcnow().isoformat()
            cursor.execute(
                "SELECT * FROM meetings WHERE user_id = ? AND calendar_added_flag = 1 AND start_datetime >= ? ORDER BY start_datetime ASC",
                (user_id, now_str)
            )
            rows = cursor.fetchall()
            return [self._row_to_meeting(row, conn) for row in rows]
        finally:
            conn.close()
