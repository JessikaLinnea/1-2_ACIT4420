import csv
from pathlib import Path

from .csv_handler import DataFileError


# Create the three required report files
def write_reports(results: list[dict], rejected: list[dict], output_dir: Path) -> list[Path]:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "analysis_summary.csv"
        with summary_path.open("w", encoding="utf-8", newline="") as file:
            fields = ("session_id", "participant_id", "participant_name", "usable_observations", "classification", "recovery_detected", "reason")
            writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for result in results:
                row = {}
                for field in fields:
                    row[field] = result[field]
                writer.writerow(row)

        report_path = output_dir / "analysis_report.txt"
        with report_path.open("w", encoding="utf-8") as file:
            for result in results:
                file.write(f"{result['session_id']} - {result['participant_name']}\n")
                file.write(f"Classification: {result['classification']} ({result['reason']})\n")
                file.write(f"Usable observations: {result['usable_observations']}\n")
                if result["summary"]:
                    heart = result["summary"]["heart_rate"]
                    file.write(f"Heart rate: average {heart['average']}, min {heart['minimum']}, max {heart['maximum']}\n")
                    file.write(f"Reference difference: {result['reference_difference']}\n")
                file.write("\n")

        rejected_path = output_dir / "rejected_records.txt"
        with rejected_path.open("w", encoding="utf-8") as file:
            for item in rejected:
                file.write(f"{item['source']}, row {item['row']}, {item['field']}: {item['reason']}\n")
    except PermissionError as error:
        raise DataFileError(f"permission denied while writing {output_dir}") from error
    except OSError as error:
        raise DataFileError(f"could not create reports in {output_dir}: {error}") from error
    return [summary_path, report_path, rejected_path]
