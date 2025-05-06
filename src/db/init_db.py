from pathlib import Path
import csv

from sqlalchemy import create_engine, text
from psycopg2.extensions import connection as PgConn  # type: ignore
from psycopg2.extras import execute_values  # noqa: F401  (kept for IDEs)

from config import settings

CSV_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "raw" / "fact_resultats_epreuves.csv"
)
TABLE = "jo"
DATE_COL = "date_debut_edition"


def get_columns() -> list[str]:
    """Return CSV header row as a list of column names."""
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return next(reader)  # header row


def main() -> None:
    cols = get_columns()
    col_list = ", ".join(f'"{c}"' for c in cols)  # quoted identifiers

    engine = create_engine(
        f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}",
        pool_pre_ping=True,
    )

    # 1 — recreate table (all TEXT)
    with engine.begin() as conn:
        ddl_cols = ", ".join(f'"{c}" TEXT' for c in cols)
        conn.execute(text(f'DROP TABLE IF EXISTS "{TABLE}";'))
        conn.execute(text(f'CREATE TABLE "{TABLE}" ({ddl_cols});'))

    # 2 — COPY CSV
    raw: PgConn = engine.raw_connection()
    with raw.cursor() as cur, CSV_PATH.open("r", encoding="utf-8") as f:
        cur.copy_expert(
            f'COPY "{TABLE}" ({col_list}) FROM STDIN WITH CSV HEADER', f
        )
    raw.commit()
    raw.close()

    # 3 — cast date column
    with engine.begin() as conn:
        conn.execute(
            text(
                f'''
                ALTER TABLE "{TABLE}"
                ALTER COLUMN "{DATE_COL}"
                TYPE DATE
                USING NULLIF("{DATE_COL}", '')::DATE;
                '''
            )
        )

    


if __name__ == "__main__":
    main()