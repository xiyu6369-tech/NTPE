"""Read-only public corpus governance API."""

from .governance import manage
from .models import CorpusView

__all__ = ["CorpusView", "manage"]

