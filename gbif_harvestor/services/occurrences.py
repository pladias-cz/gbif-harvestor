"""Filters GBIF occurrences with DuckDB."""

from __future__ import annotations

import logging
from typing import Any, Sequence

import duckdb

from ..config import Config

logger = logging.getLogger(__name__)


class OccurrenceFilter:
    """Opens the GBIF Parquet export in DuckDB and filters it.

    :meth:`open` returns a connection whose pending result holds
    the filtered occurrences; the caller streams rows from it
    with ``fetchmany`` and is responsible for closing it.
    """

    def __init__(self, config: Config) -> None:
        self._config = config

    def open(self, files: Sequence[str]) -> duckdb.DuckDBPyConnection:
        """Open the Parquet files and execute the filtered query."""
        con = duckdb.connect()
        try:
            self._load_extensions(con)

            logger.info("Opening GBIF Parquet files")

            con.read_parquet(
                list(files),
                union_by_name=True
            ).create_view("occurrences")

            query, params = self._build_query()

            logger.info("Applying occurrence filters")

            con.execute(query, params)
        except Exception:
            con.close()
            raise

        return con

    @staticmethod
    def _load_extensions(con: duckdb.DuckDBPyConnection) -> None:
        con.execute("INSTALL httpfs")
        con.execute("LOAD httpfs")

        con.execute("INSTALL spatial")
        con.execute("LOAD spatial")

    def _build_query(self) -> tuple[str, list[Any]]:
        config = self._config

        conditions: list[str] = []
        params: list[Any] = []

        conditions.append("occurrencestatus = ?")
        params.append(config.occurrence_status)

        conditions.append("decimallatitude IS NOT NULL")
        conditions.append("decimallongitude IS NOT NULL")

        conditions.append(
            "ST_Within("
            "ST_Point(decimallongitude, decimallatitude), "
            "ST_GeomFromText(?))"
        )
        params.append(config.polygon)

        if config.taxon_key is not None:
            conditions.append("taxonkey = ?")
            params.append(config.taxon_key)

        if config.taxon_rank is not None:
            conditions.append("taxonrank = ?")
            params.append(config.taxon_rank)

        if config.excluded_issues:
            conditions.append("NOT list_has_any(issue, ?)")
            params.append(config.excluded_issues)

        where = " AND ".join(conditions)

        query = f"""
            SELECT
                CAST(gbifid AS BIGINT) AS gbif_id,
                locality,
                array_to_string(recordedby, '; ') AS recorded_by,
                institutioncode AS institution_code,
                collectioncode AS collection_code,

                decimallongitude AS longitude,
                decimallatitude AS latitude,

                coordinateprecision AS coords_precision,

                day,
                month,
                year,

                taxonrank AS taxon_rank,
                verbatimscientificname AS verbatim_scientific_name,
                datasetkey AS dataset_key,

                CAST(taxonkey AS BIGINT) AS taxon_key,

                lastinterpreted AS last_interpreted

            FROM occurrences
            WHERE {where}
        """

        return query, params
