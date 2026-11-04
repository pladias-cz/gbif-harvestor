"""Orchestrates the harvest from snapshot discovery to import."""

from __future__ import annotations

import logging

from ..clients.gbif_open_data import GbifOpenDataClient
from ..config import Config
from ..db.connection import Database
from ..db.importer import RecordImporter
from .occurrences import OccurrenceFilter

logger = logging.getLogger(__name__)


class HarvestService:
    """Runs the whole harvest pipeline.

    Discovers the latest GBIF snapshot, streams its Parquet files
    through DuckDB with the configured filters and imports the
    result into PostgreSQL.
    """

    def __init__(
        self,
        config: Config,
        client: GbifOpenDataClient | None = None,
    ) -> None:
        self._config = config
        self._client = client or GbifOpenDataClient(
            config.s3_bucket,
            config.aws_region,
        )
        self._occurrences = OccurrenceFilter(config)
        self._importer = RecordImporter(
            Database(config.database_url),
            config.batch_size,
        )

    def run(self) -> int:
        """Run the harvest and return the number of imported records."""
        snapshot = self._client.latest_snapshot()

        files = self._client.parquet_files(snapshot)

        relation = self._occurrences.open(files)

        try:
            logger.info(
                "Filtered records: %d",
                relation.count("*").fetchone()[0]
            )

            return self._importer.import_records(relation)

        finally:
            relation.close()
