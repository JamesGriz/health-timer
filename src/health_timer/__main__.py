"""Allow ``python -m health_timer``."""

from .daemon import main

raise SystemExit(main())
