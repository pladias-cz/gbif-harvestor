"""Client for the GBIF open-data bucket on S3.

GBIF publishes regular occurrence snapshots as Parquet files in
a public, unsigned S3 bucket.
"""

from __future__ import annotations

import logging
from datetime import datetime

import boto3
from botocore import UNSIGNED
from botocore.config import Config as BotoConfig

from ..config import AWS_REGION, S3_BUCKET

logger = logging.getLogger(__name__)


class GbifOpenDataClient:
    """Discovers occurrence snapshots in the GBIF open-data bucket."""

    def __init__(
        self,
        bucket: str = S3_BUCKET,
        region: str = AWS_REGION,
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._s3 = boto3.client(
            "s3",
            region_name=region,
            config=BotoConfig(signature_version=UNSIGNED),
        )

    def latest_snapshot(self) -> str:
        """Return the ISO date of the most recent occurrence snapshot."""
        response = self._s3.list_objects_v2(
            Bucket=self._bucket,
            Prefix="occurrence/",
            Delimiter="/",
        )

        dates = []

        for item in response.get("CommonPrefixes", []):
            path = item["Prefix"].strip("/").split("/")[-1]

            try:
                dates.append(datetime.strptime(path, "%Y-%m-%d").date())
            except ValueError:
                continue

        if not dates:
            raise RuntimeError("No GBIF snapshots found")

        snapshot = max(dates).isoformat()

        logger.info("Latest GBIF snapshot: %s", snapshot)

        return snapshot

    def parquet_files(self, snapshot: str) -> list[str]:
        """Return the HTTPS URLs of a snapshot's Parquet files."""
        prefix = f"occurrence/{snapshot}/occurrence.parquet/"

        paginator = self._s3.get_paginator("list_objects_v2")

        files = []

        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for item in page.get("Contents", []):
                key = item["Key"]

                if key.endswith(".parquet") or key.split("/")[-1].isdigit():
                    files.append(self._url(key))

        if not files:
            raise RuntimeError(f"No Parquet files found for {snapshot}")

        logger.info("Found %d Parquet files", len(files))

        return files

    def _url(self, key: str) -> str:
        return f"https://{self._bucket}.s3.{self._region}.amazonaws.com/{key}"
