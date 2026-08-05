from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import status

from base.models import QuerySetManagerTypes
from utils.constants import ErrorMessages
from utils.errors import OperationError, ServerError


class CacheUtil:
    def get_cache_value_or_default(self, cache_key, value_callback=None, require_fresh_data=False, timeout=None):
        cached_data = None
        error_details = None

        if not require_fresh_data:
            cached_data = cache.get(cache_key)

        if not cached_data and value_callback is not None:
            cached_data, error_details = value_callback()
            if cached_data:
                self.set_cache_value(cache_key, cached_data, timeout=timeout)

        return cached_data, error_details

    def set_cache_value(self, cache_key, cached_data, timeout=None):
        if not timeout:
            timeout = settings.DEFAULT_CACHE_TIMEOUT or 60 * 60 * 24 * 7
        cache.set(cache_key, cached_data, timeout=timeout)

    def clear_cache(self, *cache_keys):
        cache.delete_many(list(cache_keys))

    def generate_cache_key(self, *args, **kwargs):
        model = kwargs.get("model") or None
        list_args = list(args)
        if model:
            try:
                name = model().model_name()
            except Exception:
                try:
                    name = model()._meta.model_name
                except Exception:
                    name = model.model_name()

            list_args.insert(0, name)

        return ":".join(list(slugify(arg) for arg in list_args))

    def fetch_object(self, model, queryset_type=None, filters=None, exclude=None, order_by=None, many=False, timeout=None,
                     not_found_error=None, use_model_key=True, require_fresh_data=False, is_background=False,
                     **cache_key_parts):
        """
        Generic cached fetch covering the "query -> cache -> standard error handling"
        pattern repeated across services (single object, list, and filtered list).
        - model_queryset_init accepts Model.objects or Model.available_objects or anyone queryset manager
        - filters/exclude accept either a dict of ORM kwargs or a Q object.
        - many=False (default) returns a single object via .get(), translating Model.DoesNotExist into a 404
        OperationError (message=not_found_error).
        - many=True returns a queryset, optionally ordered via order_by (str or list).

        :return: tuple[Any | None, Any | None]
        """

        def __do_fetch():
            try:
                if queryset_type == QuerySetManagerTypes.active_objects:
                    queryset = model.active_objects
                elif queryset_type == QuerySetManagerTypes.available_objects:
                    queryset = model.available_objects
                elif queryset_type == QuerySetManagerTypes.active_available_objects:
                    queryset = model.active_available_objects
                elif queryset_type == QuerySetManagerTypes.deleted_objects:
                    queryset = model.deleted_objects
                else:
                    queryset = model.objects

                queryset = queryset.all()

                if filters is not None and many:
                    queryset = queryset.filter(filters) if isinstance(filters, Q) else queryset.filter(**filters)

                if exclude is not None:
                    queryset = queryset.exclude(exclude) if isinstance(exclude, Q) else queryset.exclude(**exclude)

                if not many:
                    queryset = queryset.get(filters) if isinstance(filters, Q) else queryset.get(**filters)
                    return queryset, None

                if order_by:
                    order_fields = order_by if isinstance(order_by, (list, tuple)) else [order_by]
                    queryset = queryset.order_by(*order_fields)

                return queryset, None

            except ObjectDoesNotExist:
                if is_background:
                    return None, None
                return None, OperationError(
                    getattr(self, "request", None),
                    message=not_found_error or ErrorMessages.resource_not_found,
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            except Exception as e:
                server_error = ServerError(error=e, obj=self)
                return None, OperationError(
                    getattr(self, "request", None), message=server_error.message, status_code=server_error.status_code
                )

        if use_model_key:
            cache_key = self.generate_cache_key(*cache_key_parts.values(), model=model)
        else:
            cache_key = self.generate_cache_key(*cache_key_parts.values())

        return self.get_cache_value_or_default(cache_key, __do_fetch, require_fresh_data=require_fresh_data,
                                               timeout=timeout)
