import tempfile
import unittest
from pathlib import Path

from fitness_analyzer.csv_handler import (DataFileError, InvalidIdentifierError,
                                          PARTICIPANT_ID, load_participants,
                                          load_sessions, check_id)

ROOT = Path(__file__).resolve().parents[1]


class FitnessTests(unittest.TestCase):
    def test_valid_data(self):
        rejected = []
        participants = load_participants(ROOT / "data/participants.csv", rejected)
        sessions = load_sessions(ROOT / "data/fitness_sessions.csv", participants, rejected)
        self.assertEqual(len(participants), 3)
        self.assertEqual(len(sessions), 5)
        self.assertEqual(sum(len(session.observations) for session in sessions.values()), 24)
        self.assertEqual(len(rejected), 5)

    def test_invalid_id(self):
        with self.assertRaises(InvalidIdentifierError):
            check_id("P01", PARTICIPANT_ID, "participant_id")

    def test_missing_file(self):
        with self.assertRaises(DataFileError):
            load_participants(ROOT / "data/not_here.csv", [])

    def test_quality_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.csv"
            path.write_text("session_id,participant_id,timestamp,heart_rate,skin_response,temperature,activity_level,signal_quality\nFIT-2026-999,P001,0,70,1.2,32.4,0.2,0.70\n", encoding="utf-8")
            participants = load_participants(ROOT / "data/participants.csv", [])
            rejected = []
            sessions = load_sessions(path, participants, rejected)
            self.assertEqual(len(sessions["FIT-2026-999"].observations), 1)
            self.assertEqual(rejected, [])


if __name__ == "__main__":
    unittest.main()
