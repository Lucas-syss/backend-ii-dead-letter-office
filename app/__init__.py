"""Dead Letter Office application package."""

import sys

try:
    import pysqlite3 as _pysqlite3
except ImportError:
    pass
else:
    sys.modules["sqlite3"] = _pysqlite3
