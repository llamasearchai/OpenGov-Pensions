"""Custom exceptions for OpenPension application.

This module defines a comprehensive hierarchy of custom exceptions
for proper error handling and API responses.
"""

from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status


class BaseOpenPensionException(Exception):
    """Base exception for all OpenPension application errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        internal_message: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.internal_message = internal_message or message
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


# Authentication & Authorization Exceptions
class AuthenticationError(BaseOpenPensionException):
    """Base class for authentication errors."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""

    def __init__(self, message: str = "Invalid credentials", **kwargs):
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS",
            **kwargs
        )


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""

    def __init__(self, message: str = "Token has expired", **kwargs):
        super().__init__(
            message=message,
            error_code="TOKEN_EXPIRED",
            **kwargs
        )


class TokenInvalidError(AuthenticationError):
    """JWT token is invalid."""

    def __init__(self, message: str = "Invalid token", **kwargs):
        super().__init__(
            message=message,
            error_code="TOKEN_INVALID",
            **kwargs
        )


class InsufficientPermissionsError(AuthenticationError):
    """User lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PERMISSIONS",
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs
        )


class AccountLockedError(AuthenticationError):
    """Account is temporarily locked due to failed login attempts."""

    def __init__(self, message: str = "Account temporarily locked", **kwargs):
        super().__init__(
            message=message,
            error_code="ACCOUNT_LOCKED",
            **kwargs
        )


# Validation Exceptions
class ValidationError(BaseOpenPensionException):
    """Base class for validation errors."""

    def __init__(self, message: str = "Validation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs
        )


class InvalidInputError(ValidationError):
    """Invalid input data provided."""

    def __init__(self, message: str = "Invalid input data", **kwargs):
        super().__init__(
            message=message,
            error_code="INVALID_INPUT",
            **kwargs
        )


class MissingRequiredFieldError(ValidationError):
    """Required field is missing."""

    def __init__(self, field_name: str, message: Optional[str] = None, **kwargs):
        if message is None:
            message = f"Required field '{field_name}' is missing"
        super().__init__(
            message=message,
            error_code="MISSING_REQUIRED_FIELD",
            details={"field": field_name},
            **kwargs
        )


# Resource Exceptions
class ResourceNotFoundError(BaseOpenPensionException):
    """Requested resource not found."""

    def __init__(self, resource_type: str, resource_id: Union[str, int], **kwargs):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
            **kwargs
        )


class ResourceAlreadyExistsError(BaseOpenPensionException):
    """Resource already exists."""

    def __init__(self, resource_type: str, resource_id: Union[str, int], **kwargs):
        message = f"{resource_type} with ID '{resource_id}' already exists"
        super().__init__(
            message=message,
            error_code="RESOURCE_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
            **kwargs
        )


# Database Exceptions
class DatabaseError(BaseOpenPensionException):
    """Base class for database errors."""

    def __init__(self, message: str = "Database operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            **kwargs
        )


class ConnectionError(DatabaseError):
    """Database connection error."""

    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(
            message=message,
            error_code="CONNECTION_ERROR",
            **kwargs
        )


class TransactionError(DatabaseError):
    """Database transaction error."""

    def __init__(self, message: str = "Database transaction failed", **kwargs):
        super().__init__(
            message=message,
            error_code="TRANSACTION_ERROR",
            **kwargs
        )


class IntegrityError(DatabaseError):
    """Database integrity constraint violation."""

    def __init__(self, message: str = "Data integrity constraint violated", **kwargs):
        super().__init__(
            message=message,
            error_code="INTEGRITY_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs
        )


# External Service Exceptions
class ExternalServiceError(BaseOpenPensionException):
    """Base class for external service errors."""

    def __init__(self, service_name: str, message: str = "External service error", **kwargs):
        super().__init__(
            message=f"{service_name}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"service": service_name},
            **kwargs
        )


class OpenAIError(ExternalServiceError):
    """OpenAI API error."""

    def __init__(self, message: str = "OpenAI service error", **kwargs):
        super().__init__(
            service_name="OpenAI",
            message=message,
            error_code="OPENAI_ERROR",
            **kwargs
        )


class OllamaError(ExternalServiceError):
    """Ollama service error."""

    def __init__(self, message: str = "Ollama service error", **kwargs):
        super().__init__(
            service_name="Ollama",
            message=message,
            error_code="OLLAMA_ERROR",
            **kwargs
        )


# Rate Limiting Exceptions
class RateLimitError(BaseOpenPensionException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            **kwargs
        )


# Configuration Exceptions
class ConfigurationError(BaseOpenPensionException):
    """Configuration error."""

    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            **kwargs
        )


# Business Logic Exceptions
class BusinessRuleViolationError(BaseOpenPensionException):
    """Business rule violation."""

    def __init__(self, message: str = "Business rule violation", **kwargs):
        super().__init__(
            message=message,
            error_code="BUSINESS_RULE_VIOLATION",
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs
        )


class InsufficientFundsError(BusinessRuleViolationError):
    """Insufficient funds for operation."""

    def __init__(self, message: str = "Insufficient funds", **kwargs):
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_FUNDS",
            **kwargs
        )


# File Processing Exceptions
class FileProcessingError(BaseOpenPensionException):
    """File processing error."""

    def __init__(self, message: str = "File processing failed", **kwargs):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs
        )


class UnsupportedFileTypeError(FileProcessingError):
    """Unsupported file type."""

    def __init__(self, file_type: str, supported_types: list, **kwargs):
        message = f"Unsupported file type: {file_type}. Supported types: {', '.join(supported_types)}"
        super().__init__(
            message=message,
            error_code="UNSUPPORTED_FILE_TYPE",
            details={"file_type": file_type, "supported_types": supported_types},
            **kwargs
        )


class FileTooLargeError(FileProcessingError):
    """File size exceeds limit."""

    def __init__(self, file_size: int, max_size: int, **kwargs):
        message = f"File size {file_size} bytes exceeds maximum allowed size of {max_size} bytes"
        super().__init__(
            message=message,
            error_code="FILE_TOO_LARGE",
            details={"file_size": file_size, "max_size": max_size},
            **kwargs
        )


# Utility Functions
def create_http_exception_from_openpension_exception(exc: BaseOpenPensionException) -> HTTPException:
    """Convert OpenPension exception to FastAPI HTTPException."""
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.to_dict()
    )


def handle_openpension_exception(handler):
    """Decorator to handle OpenPension exceptions in FastAPI routes."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseOpenPensionException as e:
                raise create_http_exception_from_openpension_exception(e)
            except Exception as e:
                # Log unexpected exceptions
                import logging
                logger = logging.getLogger(__name__)
                logger.exception(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": "An unexpected error occurred"
                        }
                    }
                )
        return wrapper
    return decorator