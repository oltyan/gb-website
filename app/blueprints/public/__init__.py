# `bp` must be imported FIRST — feeds.py imports it from this package,
# so loading feeds before .views creates a circular import (cannot import
# name 'bp' from partially initialized module). Ruff's import sorter
# would otherwise alphabetize these and break the build.
from .views import bp  # noqa: I001
from . import feeds  # noqa: F401, E402, I001

__all__ = ["bp"]
