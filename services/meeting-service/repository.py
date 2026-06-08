from abc import ABC, abstractmethod
from typing import List, Optional
import json
import logging
import datetime
from pydantic import BaseModel, Field
import asyncpg
from azure.identity import DefaultAzureCredential
from config import settings

logger = logging.getLogger(__name__)

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
    async def initialize_db(self) -> None:
        pass

    @abstractmethod
    async def create_meeting(self, meeting: Meeting) -> Meeting:
        pass

    @abstractmethod
    async def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        pass

    @abstractmethod
    async def get_meeting_by_source_email(self, user_id: str, source_email_id: str) -> Optional[Meeting]:
        pass

    @abstractmethod
    async def get_meeting_by_url(self, user_id: str, meeting_url: str) -> Optional[Meeting]:
        pass

    @abstractmethod
    async def get_meeting_by_title_and_organizer(self, user_id: str, title: str, organizer: str) -> Optional[Meeting]:
        pass

    @abstractmethod
    async def update_meeting(self, meeting: Meeting) -> Meeting:
        pass

    @abstractmethod
    async def delete_meeting(self, meeting_id: int) -> bool:
        pass

    @abstractmethod
    async def list_meetings(self, user_id: str, calendar_added_only: bool = False) -> List[Meeting]:
        pass

    @abstractmethod
    async def list_pending_meetings(self, user_id: str) -> List[Meeting]:
        pass

    @abstractmethod
    async def list_upcoming_meetings(self, user_id: str) -> List[Meeting]:
        pass


class PostgreSQLMeetingRepository(MeetingRepository):
    def __init__(self):
        self.pool = None
        self.token_expiry = None

    async def get_password(self) -> str:
        if settings.DB_AUTH_METHOD == "entra":
            try:
                credential = DefaultAzureCredential()
                token_obj = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
                # Parse expiration date
                self.token_expiry = datetime.datetime.fromtimestamp(token_obj.expires_on, datetime.timezone.utc)
                logger.info(f"Retrieved Entra ID token, expires at: {self.token_expiry}")
                return token_obj.token
            except Exception as e:
                logger.error(f"Failed to fetch Entra ID token: {str(e)}")
                # Fall back to standard password
                return settings.DB_PASSWORD
        else:
            return settings.DB_PASSWORD

    async def initialize_pool(self):
        password = await self.get_password()
        ssl_arg = "require" if settings.DB_SSL.lower() in ("true", "1", "yes") else None
        
        self.pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            database=settings.DB_NAME,
            password=password,
            ssl=ssl_arg,
            min_size=2,
            max_size=10,
            max_connection_lifetime=1800.0, # Recycle connections every 30 mins
        )
        logger.info("PostgreSQL connection pool initialized.")

    async def get_pool(self):
        # Refresh Entra ID token if it's within 5 minutes of expiring
        if settings.DB_AUTH_METHOD == "entra" and self.token_expiry:
            now = datetime.datetime.now(datetime.timezone.utc)
            if (self.token_expiry - now).total_seconds() < 300:
                logger.info("Entra ID token close to expiry, recreating pool...")
                await self.close()
                await self.initialize_pool()

        if not self.pool:
            await self.initialize_pool()
        return self.pool

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed.")

    async def execute(self, query: str, *args):
        pool = await self.get_pool()
        try:
            return await pool.execute(query, *args)
        except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
            logger.warning("Auth error encountered, refreshing pool...")
            await self.close()
            pool = await self.get_pool()
            return await pool.execute(query, *args)

    async def fetch(self, query: str, *args):
        pool = await self.get_pool()
        try:
            return await pool.fetch(query, *args)
        except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
            logger.warning("Auth error encountered, refreshing pool...")
            await self.close()
            pool = await self.get_pool()
            return await pool.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        pool = await self.get_pool()
        try:
            return await pool.fetchrow(query, *args)
        except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
            logger.warning("Auth error encountered, refreshing pool...")
            await self.close()
            pool = await self.get_pool()
            return await pool.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        pool = await self.get_pool()
        try:
            return await pool.fetchval(query, *args)
        except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
            logger.warning("Auth error encountered, refreshing pool...")
            await self.close()
            pool = await self.get_pool()
            return await pool.fetchval(query, *args)

    async def initialize_db(self) -> None:
        query_meetings = """
            CREATE TABLE IF NOT EXISTS meetings (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                source_email_id VARCHAR(255) NOT NULL,
                source_platform VARCHAR(100) NOT NULL,
                meeting_platform VARCHAR(100) NOT NULL,
                meeting_url TEXT,
                meeting_title VARCHAR(255) NOT NULL,
                description TEXT,
                organizer VARCHAR(255),
                start_datetime VARCHAR(100) NOT NULL,
                end_datetime VARCHAR(100) NOT NULL,
                prev_start_datetime VARCHAR(100),
                prev_end_datetime VARCHAR(100),
                status VARCHAR(100) NOT NULL,
                calendar_added_flag INTEGER DEFAULT 0,
                reminder_1_day_sent INTEGER DEFAULT 0,
                reminder_1_hour_sent INTEGER DEFAULT 0,
                created_timestamp VARCHAR(100) NOT NULL,
                updated_timestamp VARCHAR(100) NOT NULL,
                participants JSONB DEFAULT '[]'::jsonb
            );
        """
        await self.execute(query_meetings)
        await self.execute("CREATE INDEX IF NOT EXISTS idx_meetings_user ON meetings(user_id);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_meetings_url ON meetings(meeting_url);")
        await self.execute("CREATE INDEX IF NOT EXISTS idx_meetings_title_org ON meetings(meeting_title, organizer);")
        logger.info("Database tables and indexes initialized.")

    async def create_meeting(self, meeting: Meeting) -> Meeting:
        query = """
            INSERT INTO meetings (
                user_id, source_email_id, source_platform, meeting_platform, meeting_url,
                meeting_title, description, organizer, start_datetime, end_datetime,
                prev_start_datetime, prev_end_datetime, status, calendar_added_flag,
                reminder_1_day_sent, reminder_1_hour_sent, created_timestamp, updated_timestamp,
                participants
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            RETURNING id;
        """
        parts_json = json.dumps([p.dict() for p in meeting.participants])
        meeting_id = await self.fetchval(
            query,
            meeting.user_id, meeting.source_email_id, meeting.source_platform, meeting.meeting_platform,
            meeting.meeting_url, meeting.meeting_title, meeting.description, meeting.organizer,
            meeting.start_datetime, meeting.end_datetime, meeting.prev_start_datetime, meeting.prev_end_datetime,
            meeting.status, meeting.calendar_added_flag, meeting.reminder_1_day_sent, meeting.reminder_1_hour_sent,
            meeting.created_timestamp, meeting.updated_timestamp, parts_json
        )
        meeting.id = meeting_id
        for p in meeting.participants:
            p.meeting_id = meeting_id
        return meeting

    def _row_to_meeting(self, row) -> Meeting:
        m_dict = dict(row)
        parts_data = m_dict.pop("participants", None)
        participants = []
        if parts_data:
            if isinstance(parts_data, str):
                try:
                    parts_list = json.loads(parts_data)
                except Exception:
                    parts_list = []
            else:
                parts_list = parts_data
            
            if isinstance(parts_list, list):
                for pr in parts_list:
                    participants.append(Participant(
                        id=pr.get("id"),
                        meeting_id=pr.get("meeting_id") or m_dict.get("id"),
                        participant_email=pr.get("participant_email"),
                        participant_name=pr.get("participant_name")
                    ))
        
        return Meeting(
            id=m_dict["id"],
            user_id=m_dict["user_id"],
            source_email_id=m_dict["source_email_id"],
            source_platform=m_dict["source_platform"],
            meeting_platform=m_dict["meeting_platform"],
            meeting_url=m_dict.get("meeting_url"),
            meeting_title=m_dict["meeting_title"],
            description=m_dict.get("description"),
            organizer=m_dict.get("organizer"),
            start_datetime=m_dict["start_datetime"],
            end_datetime=m_dict["end_datetime"],
            prev_start_datetime=m_dict.get("prev_start_datetime"),
            prev_end_datetime=m_dict.get("prev_end_datetime"),
            status=m_dict["status"],
            calendar_added_flag=m_dict.get("calendar_added_flag") or 0,
            reminder_1_day_sent=m_dict.get("reminder_1_day_sent") or 0,
            reminder_1_hour_sent=m_dict.get("reminder_1_hour_sent") or 0,
            created_timestamp=m_dict["created_timestamp"],
            updated_timestamp=m_dict["updated_timestamp"],
            participants=participants
        )

    async def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        row = await self.fetchrow("SELECT * FROM meetings WHERE id = $1", meeting_id)
        if row:
            return self._row_to_meeting(row)
        return None

    async def get_meeting_by_source_email(self, user_id: str, source_email_id: str) -> Optional[Meeting]:
        row = await self.fetchrow("SELECT * FROM meetings WHERE user_id = $1 AND source_email_id = $2", user_id, source_email_id)
        if row:
            return self._row_to_meeting(row)
        return None

    async def get_meeting_by_url(self, user_id: str, meeting_url: str) -> Optional[Meeting]:
        if not meeting_url:
            return None
        row = await self.fetchrow("SELECT * FROM meetings WHERE user_id = $1 AND meeting_url = $2", user_id, meeting_url)
        if row:
            return self._row_to_meeting(row)
        return None

    async def get_meeting_by_title_and_organizer(self, user_id: str, title: str, organizer: str) -> Optional[Meeting]:
        if not title:
            return None
        if organizer:
            row = await self.fetchrow(
                "SELECT * FROM meetings WHERE user_id = $1 AND meeting_title = $2 AND organizer = $3",
                user_id, title, organizer
            )
        else:
            row = await self.fetchrow(
                "SELECT * FROM meetings WHERE user_id = $1 AND meeting_title = $2 AND organizer IS NULL",
                user_id, title
            )
        if row:
            return self._row_to_meeting(row)
        return None

    async def update_meeting(self, meeting: Meeting) -> Meeting:
        query = """
            UPDATE meetings SET
                user_id = $1, source_email_id = $2, source_platform = $3, meeting_platform = $4, meeting_url = $5,
                meeting_title = $6, description = $7, organizer = $8, start_datetime = $9, end_datetime = $10,
                prev_start_datetime = $11, prev_end_datetime = $12, status = $13, calendar_added_flag = $14,
                reminder_1_day_sent = $15, reminder_1_hour_sent = $16, created_timestamp = $17, updated_timestamp = $18,
                participants = $19
            WHERE id = $20;
        """
        parts_json = json.dumps([p.dict() for p in meeting.participants])
        await self.execute(
            query,
            meeting.user_id, meeting.source_email_id, meeting.source_platform, meeting.meeting_platform,
            meeting.meeting_url, meeting.meeting_title, meeting.description, meeting.organizer,
            meeting.start_datetime, meeting.end_datetime, meeting.prev_start_datetime, meeting.prev_end_datetime,
            meeting.status, meeting.calendar_added_flag, meeting.reminder_1_day_sent, meeting.reminder_1_hour_sent,
            meeting.created_timestamp, meeting.updated_timestamp, parts_json, meeting.id
        )
        return meeting

    async def delete_meeting(self, meeting_id: int) -> bool:
        res = await self.execute("DELETE FROM meetings WHERE id = $1", meeting_id)
        if res and res.startswith("DELETE"):
            try:
                count = int(res.split(" ")[1])
                return count > 0
            except (IndexError, ValueError):
                pass
        return False

    async def list_meetings(self, user_id: str, calendar_added_only: bool = False) -> List[Meeting]:
        if calendar_added_only:
            rows = await self.fetch(
                "SELECT * FROM meetings WHERE user_id = $1 AND calendar_added_flag = 1 ORDER BY start_datetime ASC",
                user_id
            )
        else:
            rows = await self.fetch(
                "SELECT * FROM meetings WHERE user_id = $1 ORDER BY start_datetime ASC",
                user_id
            )
        return [self._row_to_meeting(row) for row in rows]

    async def list_pending_meetings(self, user_id: str) -> List[Meeting]:
        rows = await self.fetch(
            "SELECT * FROM meetings WHERE user_id = $1 AND calendar_added_flag = 0 AND status != 'Dismissed' ORDER BY start_datetime ASC",
            user_id
        )
        return [self._row_to_meeting(row) for row in rows]

    async def list_upcoming_meetings(self, user_id: str) -> List[Meeting]:
        now_str = datetime.datetime.utcnow().isoformat()
        rows = await self.fetch(
            "SELECT * FROM meetings WHERE user_id = $1 AND calendar_added_flag = 1 AND start_datetime >= $2 ORDER BY start_datetime ASC",
            user_id, now_str
        )
        return [self._row_to_meeting(row) for row in rows]
