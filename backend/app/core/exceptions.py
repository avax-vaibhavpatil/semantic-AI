"""
Custom Domain Exceptions

Domain-specific exceptions for the application.
These represent business logic errors, not technical errors.
"""


class DomainException(Exception):
    """Base exception for all domain exceptions"""
    pass


class QueryValidationError(DomainException):
    """Raised when a query fails validation"""
    pass


class SQLGenerationError(DomainException):
    """Raised when AI fails to generate SQL"""
    pass


class SQLExecutionError(DomainException):
    """Raised when SQL execution fails"""
    pass


class ReportNotFoundError(DomainException):
    """Raised when a report is not found"""
    pass


class ReportAccessDeniedError(DomainException):
    """Raised when user doesn't have access to a report"""
    pass


class SemanticLayerError(DomainException):
    """Raised when semantic layer operations fail"""
    pass


class InvalidTableError(SemanticLayerError):
    """Raised when a table doesn't exist in semantic layer"""
    pass


class InvalidColumnError(SemanticLayerError):
    """Raised when a column doesn't exist in semantic layer"""
    pass

