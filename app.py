"""Backwards-compatible entry point.

The application itself now lives in the ``gbif_harvestor``
package; run it with ``python -m gbif_harvestor``.
"""

from gbif_harvestor.cli import main

if __name__ == "__main__":
    main()
