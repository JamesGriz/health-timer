"""Allow ``python -m life_os``."""

from .daemon import main

raise SystemExit(main())
