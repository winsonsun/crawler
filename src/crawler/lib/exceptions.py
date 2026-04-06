# -*- coding: utf-8 -*-

class CrawlerError(Exception):
    """Base exception for all crawler-related errors."""
    pass

class SearchFailedError(CrawlerError):
    """Raised when a scene search fails to produce a usable result."""
    pass

class PageParseError(CrawlerError):
    """Raised when the detail page for a scene cannot be parsed."""
    pass

class DownloadError(CrawlerError):
    """Base exception for download-related errors."""
    pass

class DownloadHttpError(DownloadError):
    """Raised for HTTP errors during downloads (e.g., 404, 503)."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class DownloadUrlError(DownloadError):
    """Raised for URL-related errors during downloads (e.g., connection refused)."""
    pass
