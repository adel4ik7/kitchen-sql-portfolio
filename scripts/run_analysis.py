from pathlib import Path
import sqlite3
import csv

root = Path(__file__).resolve().parents[1]
with sqlite3.connect(f"file:{(root / 'kitchen.db').as_posix()}?mode=ro", uri=True) as db:
    for path in sorted((root / 'sql').glob('*_analysis_*.sql')):
        cursor = db.execute(path.read_text(encoding='utf-8'))
        rows = cursor.fetchall()
        key = path.stem.replace('_analysis_', '_')
        with (root / 'results' / (key + '.csv')).open('w', newline='', encoding='utf-8') as output:
            writer = csv.writer(output)
            writer.writerow([column[0] for column in cursor.description])
            writer.writerows(rows)
        print(f"{path.name}: {len(rows)} rows")
