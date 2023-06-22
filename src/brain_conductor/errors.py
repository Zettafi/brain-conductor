class RecoverableError(Exception):
    """
    Error that can be recovered. Implementations should try the
    request that failed at a later time.
    """

    pass


class QuotaExceededError(Exception):
    """
    The daily quota for a downstream service has been exceeded.
    """

    pass


class RateLimitError(RecoverableError):
    """
    The rate limit for a service has been exceeded. Implementations should try the
    request that failed at a later time.
    """

    pass


class TemporaryAPIError(RecoverableError):
    """
    The downstream service returned an error status code that is temporary.
    Implementations should try the request that failed at a later time. Examples
    of temporary error status codes would be 429, 500, and 502.
    """

    pass


class TooManyTokensError(Exception):
    """
    The service received tokens in excess of its limit.
    """

    pass


class NoCompletionResultError(RecoverableError):
    """Raised when the OpenAI completion calls return None"""

    pass
