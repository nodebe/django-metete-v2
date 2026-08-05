from typing import Any

from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_str
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from utils.constants import ErrorMessages
from utils.encryption_util import AESCipher
from utils.errors import CustomError
from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomExceptionMiddleware(MiddlewareMixin):
    """
        Import this in the middleware list in your settings.py file
        MIDDLEWARE = [
            # Other middlewares
            'utils.middlewares.CustomExceptionMiddleware',
            # Other middlewares
        ]
    """

    def process_exception(self, request, exception):
        if isinstance(exception, CustomError):
            response_data = {
                'error': exception.message
            }

            return JsonResponse(response_data, status=exception.status_code)

        return None


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if not user.is_active:
            raise AuthenticationFailed(
                detail={
                    "error": ErrorMessages.inactive_account,
                }
            )

        return user


class CustomResponseRenderer(JSONRenderer):
    """
    Ensures all API responses (success & error) follow a consistent schema.
    """

    PAGINATION_KEYS = frozenset({"page_size", "current_page", "last_page", "total", "next_page_url", "prev_page_url"})
    SKIP_FIELDS = frozenset({"detail", "code", "message", "non_field_errors"})

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        status_code = getattr(response, "status_code", status.HTTP_200_OK)
        context = getattr(response, "context", {})
        response_payload_requires_encryption = context.get("response_payload_requires_encryption", False)

        if status_code >= status.HTTP_400_BAD_REQUEST:
            response_data = self._format_error(data)
        else:
            response_data = self._format_success(data)

        response_data.setdefault("meta", {})["timestamp"] = timezone.now().isoformat()

        if response_payload_requires_encryption and settings.APP_ENC_ENABLED:
            cipher = AESCipher(settings.APP_ENC_KEY, settings.APP_ENC_VEC)
            response_data = cipher.encrypt_nested(response_data)

        return super().render(response_data, accepted_media_type, renderer_context)

    # ──────────────────────────────────────────────────────────────
    # SUCCESS HANDLING
    # ──────────────────────────────────────────────────────────────

    def _format_success(self, data: Any) -> dict:
        if not isinstance(data, dict):
            return self._success_template(data=data)

        # Check for pagination at top level
        if pagination_meta := self._extract_pagination(data):
            return self._success_template(
                message=data.get("message"),
                data=data.get("data"),
                meta=pagination_meta,
            )

        # Check for nested pagination (wrapped response)
        nested = data.get("data")
        if isinstance(nested, dict) and (pagination_meta := self._extract_pagination(nested)):
            return self._success_template(
                message=data.get("message"),
                data=nested.get("data"),
                meta=pagination_meta,
            )

        # Standard response - no mutation
        return self._success_template(
            message=data.get("message"),
            data=data.get("data") if "data" in data else self._exclude_keys(data, {"message"}),
        )

    def _extract_pagination(self, data: dict) -> dict | None:
        """Extract pagination metadata if all required keys are present."""
        if self.PAGINATION_KEYS.issubset(data.keys()) and "data" in data:
            return {key: data[key] for key in self.PAGINATION_KEYS}
        return None

    @staticmethod
    def _exclude_keys(data: dict, keys: set) -> dict:
        return {k: v for k, v in data.items() if k not in keys}

    @staticmethod
    def _success_template(
        message: str = None,
        data: Any = None,
        meta: dict | None = None,
    ) -> dict:
        result = {"success": True, "message": message, "data": data}
        if meta:
            result["meta"] = meta
        return result

    # ──────────────────────────────────────────────────────────────
    # ERROR HANDLING
    # ──────────────────────────────────────────────────────────────

    def _format_error(self, data: Any) -> dict:
        if not isinstance(data, dict):
            return self._error_template(message=str(data))

        error_value = data.get("error")

        if isinstance(error_value, str):
            return self._error_template(message=error_value)

        if isinstance(error_value, dict) and error_value:
            field, message, label = self._extract_error_details(error_value)
            return self._error_template(field=field, message=message, label=label)

        # Fall through: extract from top-level data
        field, message, label = self._extract_error_details(data)
        return self._error_template(field=field, message=message, label=label)

    @staticmethod
    def _error_template(
        field: str | None = None,
        message: str = "An error occurred",
        label: str = "error",
    ) -> dict:
        result = {"success": False, "message": message}

        if field:
            result["error"] = {"field": field, "label": label}

        return result

    def _extract_error_details(self, data: dict) -> tuple[str | None, str, str]:
        for field, messages in data.items():
            if field in self.SKIP_FIELDS:
                continue

            if isinstance(messages, list) and messages:
                return field, str(messages[0]), "invalid_data"

            if isinstance(messages, dict) and messages:  # Added empty check
                nested_field, nested_messages = next(iter(messages.items()))
                if isinstance(nested_messages, list) and nested_messages:
                    return f"{field}.{nested_field}", str(nested_messages[0]), "invalid_data"

        detail = data.get("detail") or data.get("message") or force_str(data)
        return None, str(detail), data.get("label", "error")
