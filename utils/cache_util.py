from django.core.cache import cache
from django.utils.text import slugify


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
            timeout = 60 * 60 * 24 * 7
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
