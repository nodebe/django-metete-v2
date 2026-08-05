from rest_framework import status, serializers
from utils.constants import ErrorMessages


class CustomError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = ErrorMessages.internal_server_error

    def __init__(self, message=None, status_code=None):
        if message is not None:
            self.message = message

        if status_code is not None:
            self.status_code = status_code

        super().__init__(self.message)


class ServerError(CustomError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = ErrorMessages.internal_server_error

    def __init__(self, error=None, obj=None):
        from utils.service import AppLogger

        if error:
            AppLogger.report(obj, error)


class UserError(CustomError):
    status_code = status.HTTP_400_BAD_REQUEST
    message = ErrorMessages.bad_request


class NotFoundError(CustomError):
    status_code = status.HTTP_404_NOT_FOUND
    message = ErrorMessages.resource_not_found


class PermissionDeniedError(CustomError):
    status_code = status.HTTP_403_FORBIDDEN
    message = ErrorMessages.permission_denied


class AccessDeniedError(CustomError):
    status_code = status.HTTP_403_FORBIDDEN
    message = ErrorMessages.access_denied


class NotAuthorizedError(CustomError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = ErrorMessages.access_denied


class CustomServerError(CustomError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = ErrorMessages.internal_server_error


class RateLimitException(CustomError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    message = ErrorMessages.too_many_requests


class UnprocessableEntityError(CustomError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = ErrorMessages.unprocessable_entity


class OperationError:
    def __init__(self, request=None, message=None, status_code=None):
        self.request = request
        self.message = message
        self.status_code = status_code

    def get_message(self):
        return self.message

    def get_status_code(self):
        if not self.status_code:
            return status.HTTP_400_BAD_REQUEST

        try:
            return int(self.status_code)

        except Exception:
            return status.HTTP_400_BAD_REQUEST

    def __str__(self):
        return self.message


class ValidationError:
    def __init__(self, message=None, code=None):
        message = message if message else ErrorMessages.validation_error
        raise serializers.ValidationError(detail=message, code=code)
