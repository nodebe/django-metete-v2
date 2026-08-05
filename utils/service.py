import logging
import random
import secrets
import string
import phonenumbers
from math import ceil
from django.shortcuts import render
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.timezone import is_aware, make_aware
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from typing import Union, TypeVar
from rest_framework import status
from django.contrib.auth.hashers import make_password
from base.tasks import make_api_request_log, update_api_request_log, report_activity
from utils.cache_util import CacheUtil
from utils.constants import ErrorMessages
from utils.decorators import CustomApiPermissionRequired
from utils.errors import OperationError, ServerError
from utils.encryption_util import AESCipher

T = TypeVar("T")


class AppLogger:
    @staticmethod
    def report(obj=None, error=None):
        path, class_name = None, None
        if obj:
            path = obj.__class__.__module__
            class_name = obj.__class__.__name__

        logging.error(f"{path}.{class_name}::{error}")

    @staticmethod
    def print(*message):
        logging.info(f"{message}")


class DefaultPagination(PageNumberPagination):
    max_page_size = int(settings.MAX_PAGE_SIZE)
    page_size = int(settings.DEFAULT_PAGE_SIZE)
    page_query_param = "page"
    page_size_query_param = 'page_size'


class CustomApiResponseUtil:
    response_payload_requires_encryption = True
    response_message_on_success = None
    response_serializer_requires_many = False
    response_serializer = None
    response_is_template_view = False
    wrap_response_in_data_object = True

    def response_with_json(self, data, status_code=None):
        if not data:
            data = {}
        elif not isinstance(data, dict):
            data = {"data": data}

        if self.response_message_on_success:
            data["message"] = self.response_message_on_success

        response = Response(data, status=status_code)
        response.context = {"response_payload_requires_encryption": self.response_payload_requires_encryption}

        return response

    def response_with_error(self, error_list, status_code=None):
        """
        Normalizes error_list (a string, a {field: messages} dict, or a list of either) into the
        shape CustomResponseRenderer._format_error expects: {"error": "message"} for plain messages,
        or {"error": {field: [messages]}} for field-level errors, so it renders as a clean
        {"success": False, "message": ..., "error": {"field", "label"}} payload instead of falling
        through to the renderer's stringified-dict fallback.
        """
        if not status_code:
            status_code = status.HTTP_400_BAD_REQUEST

        field_errors = {}
        messages = []

        def extract_errors(error_detail):
            if isinstance(error_detail, str):
                messages.append(error_detail)
            elif isinstance(error_detail, dict):
                for key, value in error_detail.items():
                    field_errors.setdefault(key, []).extend(value if isinstance(value, list) else [value])

        if isinstance(error_list, list):
            for error in error_list:
                extract_errors(error)
        else:
            extract_errors(error_list)

        if field_errors:
            response_data = {"error": field_errors}
        elif messages:
            response_data = {"error": messages[0] if len(messages) == 1 else "; ".join(messages)}
        else:
            response_data = {"error": ErrorMessages.bad_request}

        return self.response_with_json(response_data, status_code=status_code)

    def validation_error(self, errors, status_code=None):
        if status_code is None:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        if isinstance(errors, dict) and 'error' in errors:
            nested_errors = errors.pop("error")
            errors.pop("status_code", None)
            for key, value in nested_errors.items():
                errors.update({key: [value]})
        return self.response_with_json({
            "error": errors
        }, status_code=status_code)


class CustomApiRequestUtil(DefaultPagination):
    serializer_class = None

    AUTHORIZATION_KEYS = ["X-API-KEY", "HTTP_AUTHORIZATION", "X-Api-Key", "Authorization"]

    def __init__(self, request=None):
        super().__init__()
        self.page_size = int(settings.DEFAULT_PAGE_SIZE)
        self.current_page = 1
        self.request = request

    @property
    def auth_user(self):
        user = self.request.user if self.request and self.request.user else None
        if isinstance(user, AnonymousUser):
            user = None

        return user

    def split_ids(self, key):
        val = self.get_request_filter_params().get(key)
        return val.split(",") if val else None

    def report_activity(self, user=None, activity_type=None, data=None, description=None):
        user_id = None

        if not description:
            description = str(activity_type) + " records related to " + str(data)

        if not user:
            user = self.auth_user

        if user:
            user_id = user.id

        report_activity.delay(user_id=user_id, activity_type=activity_type, description=description,
                              data=str(data))

    def digify_number(self, digit, name):
        try:
            return int(digit), None
        except Exception as e:
            return None, self.make_400(ErrorMessages.not_a_number.format(name=name), e)

    def check_profile_owner(self, profile):
        """Check if the person performing any activity on the profile is the owner of the profile"""
        if profile.user != self.auth_user:
            return None, self.make_403(ErrorMessages.permission_denied)

        return True, None

    def check_resource_owner(self, resource, message=None, *additional_user_attr):
        user_attrs = list(additional_user_attr)

        user_attrs.append("user")

        pass_checks = []

        for attr in user_attrs:
            if hasattr(resource, attr):
                if getattr(resource, attr) == self.auth_user:
                    return True, None
                else:
                    pass_checks.append(False)

        if not any(pass_checks):
            return False, self.make_403(message)

        return False, None

    def make_error(self, error: str):
        return OperationError(self.request, message=error)

    def make_400(self, error: str, *extra_detail):
        AppLogger.print(*extra_detail)
        return OperationError(self.request, message=error, status_code=status.HTTP_400_BAD_REQUEST)

    def make_404(self, error: str, *extra_detail):
        AppLogger.print(*extra_detail)
        return OperationError(self.request, message=error, status_code=status.HTTP_404_NOT_FOUND)

    def make_403(self, error: str, *extra_detail):
        AppLogger.print(*extra_detail)
        return OperationError(self.request, message=error, status_code=status.HTTP_403_FORBIDDEN)

    def make_401(self, error: str, *extra_detail):
        AppLogger.print(*extra_detail)
        return OperationError(self.request, message=error, status_code=status.HTTP_401_UNAUTHORIZED)

    def make_500(self, exception, obj):
        AppLogger.report(obj, exception)
        return OperationError(
            self.request, message="Operation error: {}".format(str(exception)),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def get_request_filter_params(self, *additional_params):
        if additional_params is None:
            additional_params = []

        data = {}

        filter_bucket = self.request.query_params
        general_params = ['keyword', 'search', 'filter', 'from_date', 'to_date', 'page', 'page_size', 'ordering',
                          "is_active"] + list(additional_params)

        for param in general_params:
            field_value = filter_bucket.get(param, None)
            if field_value is not None:
                if str(field_value).lower() in ['true', 'false']:
                    data[param] = str(filter_bucket.get(param))
                else:
                    data[param] = filter_bucket.get(param) or ''
            else:
                data[param] = None

        if data['filter'] and not data['keyword']:
            data['keyword'] = data['filter']
        if data['search'] and not data['keyword']:
            data['keyword'] = data['search']

        try:
            data['page'] = int(data.get('page') or 1)

        except Exception as e:
            AppLogger.report(self, e)
            data['page'] = 1

        try:
            data['page_size'] = int(data.get('page_size') or 10)
        except Exception as e:
            AppLogger.report(self, e)
            data['page_size'] = int(settings.DEFAULT_PAGE_SIZE)

        self.current_page = data.get("page")
        self.page_size = data.get("page_size")

        return data

    def get_paginated_list_response(self, data, count_all):
        return self.__make_pages(self.__get_pagination_data(count_all, data))

    def fetch_list(self, filter_params, **extra_args):
        raise Exception("Not implemented")

    def fetch_paginated_list(self, **extra_args):
        queryset = self.fetch_list(**extra_args)
        page = self.paginate_queryset(queryset, request=self.request)
        data = self.serializer_class(page, many=True, context={"request": self.request}).data

        return self.get_paginated_list_response(data, queryset.count())

    def __get_pagination_data(self, total, data):
        query_params = self.request.query_params

        try:
            self.current_page = int(query_params.get("page", self.current_page)) or self.current_page
            self.page_size = int(query_params.get("page_size", self.page_size)) or self.page_size
        except Exception:
            AppLogger.print("Incorrect Page Number")

        prev_page_no = int(self.current_page) - 1
        last_page = ceil(total / self.page_size) if self.page_size > 0 else 0
        has_next_page = total > 0 and len(data) > 0 and total > ((self.page_size * prev_page_no) + len(data))
        has_previous_page = (prev_page_no > 0) and (total >= (self.page_size * prev_page_no))

        return prev_page_no, data, total, last_page, has_next_page, has_previous_page

    def __make_pages(self, pagination_data):
        prev_page_no, data, total, last_page, has_next_page, has_prev_page = pagination_data

        prev_page_url = None
        next_page_url = None

        request_url = self.request.path

        q_list = []
        if has_next_page or has_prev_page:
            query_list = self.request.query_params or {}
            for key in query_list:
                if key != "page":
                    q_list.append(f"{key}={query_list[key]}")

        if has_next_page:
            new_list = q_list.copy()
            new_list.append("page=" + str((+self.current_page + 1)))
            q = "&".join(new_list)
            next_page_url = f"{request_url}?{q}"

        if has_prev_page:
            new_list = q_list.copy()
            new_list.append("page=" + str((+self.current_page - 1)))
            q = "&".join(new_list)
            prev_page_url = f"{request_url}?{q}"

        return {
            "page_size": self.page_size,
            "current_page": self.current_page if self.current_page <= last_page else last_page,
            "last_page": last_page,
            "total": total,
            "next_page_url": next_page_url,
            "prev_page_url": prev_page_url,
            "data": data
        }


class CustomApiRequestProcessorBase(CustomApiPermissionRequired, CustomApiRequestUtil, CustomApiResponseUtil,
                                    CacheUtil):
    context: Union[dict, None] = None
    extra_context_data = dict()
    context_object_name = None
    template_name = None
    logging_enabled = settings.API_REQUEST_LOGGING_ENABLED
    status_code_on_success = status.HTTP_200_OK
    allow_empty_request_serializer = False
    permission_classes = [IsAuthenticated]
    serializer_class = None
    payload = {}
    ref_id = None
    request_serializer_requires_many = False
    request_payload_requires_decryption = True

    def process_request(self, request, target_function, **extra_args):
        self.check_required_roles_and_permissions()

        if self.request_payload_requires_decryption and settings.APP_ENC_ENABLED:
            encryption_util = AESCipher(settings.APP_ENC_KEY, settings.APP_ENC_VEC)
            request_data = encryption_util.decrypt_body(request.data)
        else:
            request_data = request.data

        if self.logging_enabled:
            self.ref_id = get_unique_id(length=18)
            try:
                make_api_request_log(
                    request.user.id if request.user else "",
                    request.data, request.get_full_path(), self.ref_id,
                    headers={k: v for k, v in request.headers.items() if k not in self.AUTHORIZATION_KEYS}
                )
            except Exception as e:
                AppLogger.report(self, e)

        if not self.context:
            self.context = dict()

        self.context['request'] = request

        if self.extra_context_data:
            for key, val in self.extra_context_data.items():
                self.context[key] = val

        try:
            if self.serializer_class and request.method in {"PUT", "POST"}:
                data = request_data or (list() if self.request_serializer_requires_many else dict())
                if self.allow_empty_request_serializer:
                    serializer = self.serializer_class(
                        data=data,
                        context=self.context,
                        many=self.request_serializer_requires_many,
                        allow_empty=self.allow_empty_request_serializer
                    )
                else:
                    serializer = self.serializer_class(
                        data=data,
                        context=self.context,
                        many=self.request_serializer_requires_many
                    )

                if serializer.is_valid():
                    response_raw_data: Union[tuple, T] = target_function(serializer.validated_data, **extra_args)
                else:
                    return self.validation_error(serializer.errors)

            else:
                if self.payload:
                    response_raw_data: Union[tuple, T] = target_function(self.payload, **extra_args)
                else:
                    response_raw_data: Union[tuple, T] = target_function(**extra_args)

            return self.__handle_request_response(response_raw_data)

        except Exception as e:
            AppLogger.report(self, e)

            response_data = {"error": str(e), "message": "Server error"}

            if self.ref_id:
                try:
                    update_api_request_log.delay(ref_id=self.ref_id, response_status="Error",
                                                 response_body=response_data)

                except Exception as e:
                    AppLogger.report(self, e)

            return self.response_with_json(response_data, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def __handle_request_response(self, response_raw_data):
        response_data, error_detail = None, None

        if isinstance(response_raw_data, tuple):
            response_data, error_detail = response_raw_data
        elif isinstance(response_raw_data, str):
            self.response_message_on_success = response_data
            response_data = {}
        else:
            response_data = response_raw_data

        if error_detail:
            status_code = None
            if isinstance(error_detail, OperationError):
                status_code = error_detail.get_status_code()
                error_detail = error_detail.get_message()

                if self.ref_id:
                    try:
                        update_api_request_log.delay(ref_id=self.ref_id, response_status="Error",
                                                     response_body=error_detail)
                    except Exception as e:
                        AppLogger.report(self, e)

            return self.response_with_error(error_detail, status_code=status_code)

        # Code for if there's a template needed as the response
        if self.response_is_template_view:
            if self.context_object_name is None:
                self.context_object_name = "data"

            self.context[self.context_object_name] = response_data
            return render(self.request, self.template_name, self.context)

        if self.response_serializer is not None and response_data:
            response_data = self.response_serializer(response_data, many=self.response_serializer_requires_many).data

        if self.wrap_response_in_data_object:
            response_data = {"data": response_data}

        if self.ref_id:
            try:
                update_api_request_log.delay(ref_id=self.ref_id, response_status="Success",
                                             response_body=response_data)
            except Exception as e:
                AppLogger.report(self, e)

        return self.response_with_json(response_data, self.status_code_on_success)


def get_unique_id(prefix="", suffix="", length=None, is_secret_key=False):
    date_str = timezone.now().strftime("%Y%m%d%H%M%S")[3:]

    fixed_parts_len = len(prefix) + len(suffix)

    if length:
        target_len = max(length, fixed_parts_len + 6)
        random_len = target_len - fixed_parts_len - len(date_str)

        if random_len < 4:
            date_str = date_str
            random_len = target_len - fixed_parts_len - len(date_str)
    else:
        random_len = 6

    allowed_chars = string.ascii_lowercase + string.digits if is_secret_key else string.digits

    random_part = get_random_string(max(0, random_len), allowed_chars=allowed_chars)

    generated_id = f"{prefix}{date_str}{random_part}{suffix}"

    if length:
        return generated_id[:length], None

    return generated_id


def generate_password():
    if settings.DEBUG:
        password = settings.DEFAULT_PASSWORD
    else:
        password = secrets.token_hex(6)

    return password


def generate_otp():
    otp = str(random.randint(1, 999999)).zfill(6)

    hashed_otp = make_password(otp)

    return otp, hashed_otp


def generate_random_username():
    # List of words to combine for the username
    adjectives = ['fast', 'bright', 'cool', 'brave', 'happy', 'silent', 'lucky']
    nouns = ['lion', 'tiger', 'eagle', 'panda', 'shark', 'falcon', 'wolf']

    # Choose a random adjective and noun
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)

    # Generate a random number
    number = random.randint(1, 999)

    # Combine the parts to form the username
    username = f"{adjective.capitalize()}{noun.capitalize()}{number}"

    return username


def check_time_expired(time_to_check, duration=10):
    """
    Returns True if the otp has expired and False if the otp is still valid.
    Returns True if the current time is greater than the time_to_check by the number of duration.
    """

    if not is_aware(time_to_check):
        time_to_check = make_aware(time_to_check)

    created_at = time_to_check
    current_time = timezone.now()

    time_difference = current_time - created_at
    time_difference_minutes = time_difference.total_seconds() / 60

    return time_difference_minutes > duration


def format_phone_number(phone_number, region="NG"):
    try:
        number = phonenumbers.parse(phone_number, region)
        if not phonenumbers.is_valid_number(number):
            return None, ErrorMessages.invalid_phone_number

        formatted_number = str(phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164))

        return formatted_number, None

    except Exception as e:
        AppLogger.report(error=e)
        return None, ServerError(e)


def format_otp(otp):
    otp = str(otp)  # ensure it's a string
    if len(otp) != 6 or not otp.isdigit():
        raise ValueError("OTP must be a 6-digit number")

    return f"{otp[:3]}-{otp[3:]}"
