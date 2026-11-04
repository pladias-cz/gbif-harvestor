"""Harvest configuration.

The defaults mirror the constants of the legacy ``legacy.py``
script; every value can be overridden through environment
variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping

S3_BUCKET = "gbif-opendata-eu-central-1"
AWS_REGION = "eu-central-1"

DEFAULT_OCCURRENCE_STATUS = "PRESENT"

# Polygon from the original GBIF search URL (roughly the Czech Republic).
DEFAULT_POLYGON = """
POLYGON((
    11.83149 51.29958,
    11.66493 48.09954,
    19.16497 48.09965,
    19.33152 51.29969,
    14.64381 51.29962,
    11.83149 51.29958
))
"""

# Geospatial issues that exclude an occurrence from the harvest.
# This list should be adjusted to match the exact geospatial
# issue semantics required by the application.
DEFAULT_EXCLUDED_ISSUES = [
    "COORDINATE_OUT_OF_RANGE",
    "ZERO_COORDINATE",
    "COORDINATE_INVALID",
    "COORDINATE_REPROJECTION_FAILED",
]

DEFAULT_BATCH_SIZE = 10_000


@dataclass(frozen=True)
class Config:
    """Configuration of a single harvest run.

    ``taxon_key``/``taxon_rank`` of ``None`` mean "all taxa".
    """

    database_url: str
    s3_bucket: str = S3_BUCKET
    aws_region: str = AWS_REGION
    polygon: str = DEFAULT_POLYGON
    taxon_key: int | None = None
    taxon_rank: str | None = None
    occurrence_status: str = DEFAULT_OCCURRENCE_STATUS
    excluded_issues: list[str] = field(
        default_factory=lambda: list(DEFAULT_EXCLUDED_ISSUES)
    )
    batch_size: int = DEFAULT_BATCH_SIZE

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Config":
        """Build a configuration from environment variables.

        ``env`` defaults to ``os.environ``.
        """
        env = os.environ if env is None else env

        database_url = _optional_str(env.get("DATABASE_URL"))
        if database_url is None:
            raise ValueError(
                "DATABASE_URL is not set; it must point to the "
                "PostgreSQL database to import into"
            )

        return cls(
            database_url=database_url,
            s3_bucket=_optional_str(env.get("GBIF_S3_BUCKET")) or S3_BUCKET,
            aws_region=_optional_str(env.get("GBIF_AWS_REGION")) or AWS_REGION,
            polygon=_optional_str(env.get("GBIF_POLYGON")) or DEFAULT_POLYGON,
            taxon_key=_optional_int(env.get("GBIF_TAXON_KEY")),
            taxon_rank=_optional_str(env.get("GBIF_TAXON_RANK")),
            occurrence_status=(
                _optional_str(env.get("GBIF_OCCURRENCE_STATUS"))
                or DEFAULT_OCCURRENCE_STATUS
            ),
            excluded_issues=_issues(env.get("GBIF_EXCLUDED_ISSUES")),
            batch_size=(
                _optional_int(env.get("GBIF_BATCH_SIZE"))
                or DEFAULT_BATCH_SIZE
            ),
        )


def _optional_str(value: str | None) -> str | None:
    """Return the stripped value, or ``None`` when missing/empty."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def _optional_int(value: str | None) -> int | None:
    """Parse an optional integer environment value."""
    text = _optional_str(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"Expected an integer, got {text!r}") from None


def _issues(value: str | None) -> list[str]:
    """Parse a comma-separated list of geospatial issues."""
    if value is None:
        return list(DEFAULT_EXCLUDED_ISSUES)
    return [item.strip() for item in value.split(",") if item.strip()]
