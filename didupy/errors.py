class DidUPyError(Exception):
    """Base class for exceptions in this module."""


class AuthenticationError(DidUPyError):
    """Exception raised for authentication errors."""


class ResponseError(DidUPyError):
    """Exception raised for errors in the response from the server."""

    def __init__(
        self, status_code: int, message: str = "Error in response from server"
    ):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{message} (status code: {status_code})")
