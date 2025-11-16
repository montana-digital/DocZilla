"""
Custom Exceptions

Error handling classes for DocZilla.
"""


class DocZillaError(Exception):
    """Base exception for DocZilla."""
    pass


class OperationalError(DocZillaError):
    """
    Operational errors - handle gracefully.
    
    These are expected errors during normal operations:
    - Network timeouts
    - File not found
    - Invalid user input
    - Permission denied
    """
    
    def __init__(self, message: str, user_message: str = None, suggestion: str = None):
        self.message = message
        self.user_message = user_message or message
        self.suggestion = suggestion
        super().__init__(self.message)


class ProgrammerError(DocZillaError):
    """
    Programmer errors - log and crash.
    
    These are bugs in code:
    - Null pointer exceptions
    - Type errors
    - Logic errors
    
    Don't catch these - let them crash and fix the bug.
    """
    pass


class ConversionError(OperationalError):
    """Error during format conversion."""
    pass


class ValidationError(OperationalError):
    """File validation error."""
    pass


class FileNotFoundError(OperationalError):
    """File not found error."""
    pass


class PermissionError(OperationalError):
    """Permission denied error."""
    pass

