"""Entry point: python -m priced_deferral <demo|evaluate|decide>."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
