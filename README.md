# gbif-harvestor

Harvests GBIF occurrences matching a geographic/taxonomic filter
from the public GBIF open-data snapshots and imports them into
PostgreSQL.

```shell

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

DATABASE_URL=postgresql://pladias:pladias@localhost:7777/pladias \
    python -m gbif_harvestor

```

Configuration is read from environment variables,
see [`.env.sample`](.env.sample).
