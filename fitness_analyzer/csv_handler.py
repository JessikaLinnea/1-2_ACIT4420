import csv
import re
from pathlib import Path

from .models import FitnessSession, Observation, Participant, ReferenceMeasurements


class InvalidIdentifierError(ValueError):
    """Raised when an identifier has an invalid format."""
    pass


# Custom error when a CSV row cannot be used.
class InvalidRecordError(ValueError):
    """Raised when a CSV record cannot be accepted."""
    def __init__(self, field, reason):
        self.field = field
        super().__init__(reason)


class DataFileError(OSError):
    """Raised when a file cannot be read or written."""
    pass


# Regex patterns for participant and session IDs.
PARTICIPANT_ID = re.compile(r"P\d{3}")
SESSION_ID = re.compile(r"FIT-\d{4}-\d{3}")

# Required column names in the CSV files.
PROFILE_FIELDS = ("participant_id", "name", "baseline_heart_rate", "baseline_skin_response", "baseline_temperature")
SESSION_FIELDS = ("session_id", "participant_id", "timestamp", "heart_rate", "skin_response", "temperature", "activity_level", "signal_quality")

# Accepted ranges for session measurements.
RANGES = {"timestamp": (0, float("inf")), "heart_rate": (30, 230), "skin_response": (0, 20),
          "temperature": (15, 45), "activity_level": (0, 1), "signal_quality": (.70, 1)}



# Check ID format with regex.
def check_id(value, pattern, field):
    if not pattern.fullmatch(value or ""):
        raise InvalidIdentifierError(field, value)

    return value


# Check for missing cells or extra cells.
def check_row(row, fields):
    if row.get(None):
        raise InvalidRecordError("row", "unexpected extra value")
    for field in fields:
        if row.get(field) in (None, ""):
            raise InvalidRecordError(field, "missing value")


# Convert text from CSV to a number.
def number(row, field, as_int=False):
    try:
        if as_int:
            return int(row[field])
        return float(row[field])

    except KeyError as error:
        raise InvalidRecordError(field, "missing column") from error

    except ValueError as error:
        if as_int:
            raise InvalidRecordError(field, "must be an integer") from error
        raise InvalidRecordError(field, "must be a number") from error


# Check that each sensor value is possible.
def check_ranges(values):
    for field, (low, high) in RANGES.items():
        if not low <= values[field] <= high:
            raise InvalidRecordError(
                field,
                f"must be between {low} and {high}"
            )


# Save a rejected-row description.
def add_rejection(rejected, path, row_number, error):
    rejected.append({"source": Path(path).name, 
                     "row": row_number,
                     "field": getattr(error, "field", "row"), 
                     "reason": str(error)})


# Read participants from the profile CSV file.
def load_participants(path, rejected):
    participants = {}
    try:
        with open(path, encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if tuple(reader.fieldnames or ()) != PROFILE_FIELDS:
                raise DataFileError(f"unexpected profile columns in {path}")
            for row_number, row in enumerate(reader, 2):
                try:
                    check_row(row, PROFILE_FIELDS)
                    participant_id = check_id(row["participant_id"], PARTICIPANT_ID, "participant_id")
                    heart = number(row, "baseline_heart_rate")
                    skin = number(row, "baseline_skin_response")
                    temperature = number(row, "baseline_temperature")

                    for value, field, low, high in ((heart, "baseline_heart_rate", 30, 150), (skin, "baseline_skin_response", 0, 20), (temperature, "baseline_temperature", 15, 45)):
                        if not low <= value <= high:
                            raise InvalidRecordError(field, f"must be between {low} and {high}")
                        
                    participants[participant_id] = Participant(participant_id, row["name"], ReferenceMeasurements(heart, skin, temperature))

                except (InvalidIdentifierError, InvalidRecordError, ValueError) as error:
                    add_rejection(rejected, path, row_number, error)
                    
    except FileNotFoundError as error:
        raise DataFileError(f"input file not found: {path}") from error
    except PermissionError as error:
        raise DataFileError(f"permission denied for input file: {path}") from error
    except csv.Error as error:
        raise DataFileError(f"CSV error in {path}: {error}") from error
    return participants


# Read session rows and group accepted rows by session ID.
def load_sessions(path, participants, rejected):
    sessions = {}
    try:
        with open(path, encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if tuple(reader.fieldnames or ()) != SESSION_FIELDS:
                raise DataFileError(f"unexpected session columns in {path}")
            for row_number, row in enumerate(reader, 2):
                try:
                    check_row(row, SESSION_FIELDS)
                    session_id = check_id(row["session_id"], SESSION_ID, "session_id")
                    participant_id = check_id(row["participant_id"], PARTICIPANT_ID, "participant_id")

                    if participant_id not in participants:
                        raise InvalidRecordError("participant_id", "unknown participant")
                    session = sessions.setdefault(session_id, FitnessSession(session_id, participants[participant_id]))

                    if session.participant.participant_id != participant_id:
                        raise InvalidRecordError("participant_id", "does not match this session")
                    values = {"timestamp": number(row, "timestamp", True), "heart_rate": number(row, "heart_rate"),
                              "skin_response": number(row, "skin_response"), "temperature": number(row, "temperature"),
                              "activity_level": number(row, "activity_level"), "signal_quality": number(row, "signal_quality")}
                    check_ranges(values)
                    session.add(Observation(values))

                except (InvalidIdentifierError, InvalidRecordError) as error:
                    add_rejection(rejected, path, row_number, error)
    except FileNotFoundError as error:
        raise DataFileError(f"input file not found: {path}") from error
    except PermissionError as error:
        raise DataFileError(f"permission denied for input file: {path}") from error
    except csv.Error as error:
        raise DataFileError(f"CSV error in {path}: {error}") from error
    return sessions
