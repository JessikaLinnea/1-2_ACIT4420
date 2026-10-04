import argparse
from pathlib import Path

from fitness_analyzer.csv_handler import DataFileError, load_participants, load_sessions
from fitness_analyzer.reports import write_reports


# Read command-line file paths.
def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse fitness-session CSV files.")
    parser.add_argument("--profiles", type=Path, default=Path("data/participants.csv"))
    parser.add_argument("--sessions", type=Path, default=Path("data/fitness_sessions.csv"))
    parser.add_argument("--invalid-sessions", type=Path, default=Path("data/fitness_sessions_invalid.csv"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    return parser.parse_args()


# Load data, analyse sessions and create reports.
def main() -> int:
    args = arguments()
    rejected: list[dict] = []
    try:
        participants = load_participants(args.profiles, rejected)
        sessions = load_sessions(args.sessions, participants, rejected)
        for session_id, session in load_sessions(args.invalid_sessions, participants, rejected).items():
            if session_id in sessions:
                sessions[session_id].observations.extend(session.observations)
            else:
                sessions[session_id] = session
        results = [session.analyse() for session in sorted(sessions.values(), key=lambda item: item.session_id)]
        files = write_reports(results, rejected, args.output)
    except DataFileError as error:
        print(f"Could not complete analysis: {error}")
        return 1
    accepted = sum(result["usable_observations"] for result in results)
    print(f"Completed: {accepted} accepted rows, {len(rejected)} rejected rows, {len(results)} sessions.")
    print("Created: " + ", ".join(str(path) for path in files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
