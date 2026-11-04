"""Imports filtered occurrences into PostgreSQL."""

from __future__ import annotations

import csv
import io
import logging

import duckdb

from .connection import Database

logger = logging.getLogger(__name__)

CREATE_STAGING = """
CREATE TEMP TABLE gbif_staging (
    gbif_id BIGINT,
    locality TEXT,
    recorded_by TEXT,
    institution_code TEXT,
    collection_code TEXT,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    coords_precision INTEGER,
    day INTEGER,
    month INTEGER,
    year INTEGER,
    taxon_rank TEXT,
    verbatim_scientific_name TEXT,
    dataset_key VARCHAR,
    taxon_key BIGINT,
    last_interpreted TIMESTAMP
) ON COMMIT DROP
"""

COPY_STAGING = """
COPY gbif_staging (
    gbif_id,
    locality,
    recorded_by,
    institution_code,
    collection_code,
    longitude,
    latitude,
    coords_precision,
    day,
    month,
    year,
    taxon_rank,
    verbatim_scientific_name,
    dataset_key,
    taxon_key,
    last_interpreted
)
FROM STDIN WITH (FORMAT CSV)
"""

COUNT_UNMATCHED_TAXA = """
SELECT COUNT(*)
FROM gbif_staging s
LEFT JOIN gbif.taxa t
    ON t.gbif_taxon_key = s.taxon_key
WHERE t.col_id IS NULL
"""

INSERT_RECORDS = """
INSERT INTO gbif.records (
    gbif_id,
    locality,
    recorded_by,
    institution_code,
    collection_code,
    coords,
    coords_precision,
    day,
    month,
    year,
    taxon_rank,
    verbatim_scientific_name,
    dataset_key,
    taxon_col_id,
    last_interpreted,
    imported_at,
    deleted_at
)
SELECT
    s.gbif_id,
    s.locality,
    s.recorded_by,
    s.institution_code,
    s.collection_code,

    ST_SetSRID(
        ST_MakePoint(s.longitude, s.latitude),
        4326
    ),

    s.coords_precision,
    s.day,
    s.month,
    s.year,
    s.taxon_rank,
    s.verbatim_scientific_name,
    s.dataset_key,
    t.col_id,
    s.last_interpreted,
    now(),
    NULL

FROM gbif_staging s

JOIN gbif.taxa t
    ON t.gbif_taxon_key = s.taxon_key

ON CONFLICT (gbif_id)
DO UPDATE SET
    locality = EXCLUDED.locality,
    recorded_by = EXCLUDED.recorded_by,
    institution_code = EXCLUDED.institution_code,
    collection_code = EXCLUDED.collection_code,
    coords = EXCLUDED.coords,
    coords_precision = EXCLUDED.coords_precision,
    day = EXCLUDED.day,
    month = EXCLUDED.month,
    year = EXCLUDED.year,
    taxon_rank = EXCLUDED.taxon_rank,
    verbatim_scientific_name =
        EXCLUDED.verbatim_scientific_name,
    dataset_key = EXCLUDED.dataset_key,
    taxon_col_id = EXCLUDED.taxon_col_id,
    last_interpreted = EXCLUDED.last_interpreted,
    imported_at = now(),
    deleted_at = NULL
"""


class RecordImporter:
    """Streams filtered occurrences into ``gbif.records``.

    Rows are copied from the DuckDB relation into a temporary
    staging table and then upserted into ``gbif.records``,
    resolving each record's taxon against ``gbif.taxa``.
    """

    def __init__(self, database: Database, batch_size: int = 10_000) -> None:
        self._database = database
        self._batch_size = batch_size

    def import_records(self, relation: duckdb.DuckDBPyConnection) -> int:
        """Import the relation's pending result, return the row count."""
        total = 0

        with self._database.transaction() as conn:
            with conn.cursor() as cur:

                cur.execute(CREATE_STAGING)

                logger.info("Copying records to PostgreSQL staging")

                with cur.copy(COPY_STAGING) as copy:

                    while True:
                        batch = relation.fetchmany(self._batch_size)

                        if not batch:
                            break

                        buffer = io.StringIO()

                        writer = csv.writer(buffer)

                        writer.writerows(batch)

                        copy.write(buffer.getvalue())

                        total += len(batch)

                        logger.info("Staged %d records", total)

                # Count records without a matching local taxon
                cur.execute(COUNT_UNMATCHED_TAXA)

                unmatched = cur.fetchone()[0]

                logger.info(
                    "Records without matching taxon: %d",
                    unmatched
                )

                cur.execute(INSERT_RECORDS)

                logger.info(
                    "Inserted/updated %d records",
                    cur.rowcount
                )

        logger.info("Import finished: %d records", total)

        return total
