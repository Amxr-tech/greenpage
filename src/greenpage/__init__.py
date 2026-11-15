"""greenpage: estimate and budget the carbon footprint of web pages."""

__version__ = "0.1.1"

from .model import Estimate, estimate, rating_for  # noqa: E402
from .scan import PageScan, Resource, scan_directory, scan_file, scan_url  # noqa: E402

__all__ = [
    "Estimate", "PageScan", "Resource", "estimate", "rating_for",
    "scan_directory", "scan_file", "scan_url", "__version__",
]
