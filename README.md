# Smart Fitness Session Analyzer

Assignment II reads fitness CSV files, validates rows, analyses sessions and
writes reports.

The older Assignment I files are in `assignment1/`. Run them with:

```bash
python3 assignment1/run_generated_scenarios.py
```

Run:

```bash
python3 main.py
```

Tests:

```bash
python3 -m unittest discover -s tests -v
```

Main files:

- `models.py` - classes and analysis
- `csv_handler.py` - CSV reading and validation
- `reports.py` - report files

The program reads the unchanged files in `data/` and creates:

```text
output/analysis_summary.csv
output/analysis_report.txt
output/rejected_records.txt
```

IDs are checked with regex. Invalid rows are recorded with filename, row,
field and reason. Signal quality below `0.70` is rejected. Sessions with fewer
than three valid readings are marked `insufficient data`.
