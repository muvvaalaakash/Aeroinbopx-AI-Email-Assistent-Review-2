import os
import sys
import unittest
import sqlite3
import asyncio
from datetime import datetime

# Adjust Python path to import from services/meeting-service
sys.path.append(r"c:\Users\ASUS\OneDrive\Desktop\Ai_Assistan_Email\services\meeting-service")

# Mock environment variables
os.environ["DATABASE_PATH"] = "test_meetings.db"

import main
from repository import SQLiteMeetingRepository, Meeting, Participant

class TestMeetingServiceLogic(unittest.TestCase):
    def setUp(self):
        # Initialize test database
        if os.path.exists("test_meetings.db"):
            try:
                os.remove("test_meetings.db")
            except Exception:
                pass
        self.repo = SQLiteMeetingRepository("test_meetings.db")
        main.repo = self.repo

    def tearDown(self):
        # Clear main module repo so references are dropped
        main.repo = None
        self.repo = None
        if os.path.exists("test_meetings.db"):
            try:
                os.remove("test_meetings.db")
            except Exception:
                pass

    def test_regex_url_matching(self):
        meet_body = "Hi, join our Google Meet at https://meet.google.com/abc-defg-hij"
        zoom_body = "Please connect via Zoom: https://zoom.us/j/123456789?pwd=test"
        teams_body = "Teams link: https://teams.microsoft.com/l/meetup-join/19%3ameeting_xyz%40thread.v2/0?context=%7b%22Tid%22%3a%22abc%22%7d"
        no_meet_body = "Hello! See you tomorrow at the office."

        url, plat = main.extract_meeting_url(meet_body)
        self.assertEqual(plat, "Google Meet")
        self.assertEqual(url, "https://meet.google.com/abc-defg-hij")

        url, plat = main.extract_meeting_url(zoom_body)
        self.assertEqual(plat, "Zoom")
        self.assertEqual(url, "https://zoom.us/j/123456789?pwd=test")

        url, plat = main.extract_meeting_url(teams_body)
        self.assertEqual(plat, "Microsoft Teams")
        self.assertTrue("meetup-join" in url)

        url, plat = main.extract_meeting_url(no_meet_body)
        self.assertIsNone(url)
        self.assertIsNone(plat)

    def test_ics_parsing(self):
        ics_text = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Google Inc//Google Calendar 70.9054//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:test-uid-123
DTSTART:20260610T150000Z
DTEND:20260610T160000Z
SUMMARY:Sprint Review Planning
DESCRIPTION:Discuss sprint planning
ORGANIZER;CN=Aakash:mailto:aakash@example.com
ATTENDEE;CN=User;ROLE=REQ-PARTICIPANT:mailto:user@example.com
LOCATION:https://meet.google.com/abc-defg-hij
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""
        ics_data = main.parse_ics_content(ics_text)
        self.assertIsNotNone(ics_data)
        data, participants = ics_data
        
        self.assertEqual(data["title"], "Sprint Review Planning")
        self.assertEqual(data["organizer"], "aakash@example.com")
        self.assertEqual(main.convert_ics_datetime(data["dtstart"]), "2026-06-10T15:00:00Z")
        self.assertEqual(main.convert_ics_datetime(data["dtend"]), "2026-06-10T16:00:00Z")
        self.assertEqual(data["location"], "https://meet.google.com/abc-defg-hij")
        self.assertEqual(participants[0]["email"], "user@example.com")

    def test_keyword_filtering(self):
        self.assertTrue(main.has_meeting_keywords("Let's schedule a call tomorrow."))
        self.assertTrue(main.has_meeting_keywords("Invite you to a webinar."))
        self.assertFalse(main.has_meeting_keywords("Here is the monthly receipt for your subscription."))

    def test_repository_crud_and_uniqueness(self):
        # Create a meeting
        meet = Meeting(
            user_id="executive@example.com",
            source_email_id="msg-1",
            source_platform="gmail",
            meeting_platform="Zoom",
            meeting_url="https://zoom.us/j/99999",
            meeting_title="Initial Sync",
            description="Sync description",
            organizer="sender@example.com",
            start_datetime="2026-06-10T10:00:00",
            end_datetime="2026-06-10T11:00:00",
            status="Pending",
            calendar_added_flag=0,
            created_timestamp="2026-06-05T00:00:00",
            updated_timestamp="2026-06-05T00:00:00",
            participants=[
                Participant(participant_email="p1@example.com", participant_name="P1")
            ]
        )
        saved = self.repo.create_meeting(meet)
        self.assertIsNotNone(saved.id)
        
        # Verify normalization of participants
        conn = sqlite3.connect("test_meetings.db")
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM meeting_participants WHERE meeting_id = ?", (saved.id,)).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["participant_email"], "p1@example.com")
        finally:
            conn.close()

        # Test retrieval by URL
        found = self.repo.get_meeting_by_url("executive@example.com", "https://zoom.us/j/99999")
        self.assertIsNotNone(found)
        self.assertEqual(found.meeting_title, "Initial Sync")

        # Test duplicate skip
        # Same URL, same dates
        main.repo = self.repo
        
        asyncio.run(main.save_or_update_meeting(
            user_id="executive@example.com",
            source_email_id="msg-2",
            source_platform="gmail",
            meeting_platform="Zoom",
            meeting_url="https://zoom.us/j/99999",
            meeting_title="Initial Sync",
            description="Sync description duplicate",
            organizer="sender@example.com",
            start_datetime="2026-06-10T10:00:00",
            end_datetime="2026-06-10T11:00:00",
            status="Pending",
            participants=[]
        ))
        
        # Verify no duplicate is created (still 1 meeting in DB)
        all_meetings = self.repo.list_meetings("executive@example.com")
        self.assertEqual(len(all_meetings), 1)

        # Test Reschedule Update
        # Same URL, new dates
        asyncio.run(main.save_or_update_meeting(
            user_id="executive@example.com",
            source_email_id="msg-3",
            source_platform="gmail",
            meeting_platform="Zoom",
            meeting_url="https://zoom.us/j/99999",
            meeting_title="Initial Sync",
            description="Rescheduled description",
            organizer="sender@example.com",
            start_datetime="2026-06-10T12:00:00",
            end_datetime="2026-06-10T13:00:00",
            status="Pending",
            participants=[
                Participant(participant_email="p2@example.com", participant_name="P2")
            ]
        ))
        
        # Verify updated fields
        updated = self.repo.get_meeting(saved.id)
        self.assertEqual(updated.status, "Updated")
        self.assertEqual(updated.start_datetime, "2026-06-10T12:00:00")
        self.assertEqual(updated.prev_start_datetime, "2026-06-10T10:00:00")
        self.assertEqual(len(updated.participants), 2)  # Merged participants

        # Test cancellation
        asyncio.run(main.save_or_update_meeting(
            user_id="executive@example.com",
            source_email_id="msg-4",
            source_platform="gmail",
            meeting_platform="Zoom",
            meeting_url="https://zoom.us/j/99999",
            meeting_title="Initial Sync",
            description="Cancelled description",
            organizer="sender@example.com",
            start_datetime="2026-06-10T12:00:00",
            end_datetime="2026-06-10T13:00:00",
            status="Cancelled",
            participants=[]
        ))
        
        cancelled = self.repo.get_meeting(saved.id)
        self.assertEqual(cancelled.status, "Cancelled")

if __name__ == "__main__":
    unittest.main()
