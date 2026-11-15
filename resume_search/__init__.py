"""Core logic for Resume Search.

This package never imports Streamlit, so it can be tested and reused without a
user interface.
"""

from resume_search.config import APP_VERSION

__all__ = ["APP_VERSION"]
__version__ = APP_VERSION
