from utils.service import CustomApiRequestProcessorBase


class ModelService(CustomApiRequestProcessorBase):
    def __init__(self, request):
        super().__init__(request)

    def create_model_instance(self, model=None, payload=None):
        """Creates a model instance of the model passed using the payload data"""
        if payload is None:
            payload = {}

        if model is None:
            error = "Invalid model instance"
            return None, self.make_500(error, obj=self)

        has_created_by_attr = hasattr(model, "created_by")

        if isinstance(payload, list):
            payload_list = []
            for data in payload:
                data_creator = data.created_by or self.auth_user
                if has_created_by_attr:
                    data["created_by"] = data_creator
                payload_list.append(
                    model(**data)
                )
            main_object = model.objects.bulk_create(payload_list, ignore_conflicts=True)
        else:
            if has_created_by_attr:
                data_creator = payload.get("created_by", self.auth_user)
                payload["created_by"] = data_creator

            main_object = model.objects.create(**payload)
            main_object.save()

        return main_object, None

    def update_model_instance(self, model_instance=None, cache_keys=None, **kwargs):
        if cache_keys is None:
            cache_keys = list()

        if model_instance is None:
            error = "Invalid model instance"
            return None, self.make_500(error, obj=self)

        base_model_attributes = ["updated_by", "updated_at"]

        update_fields = []

        for attr in base_model_attributes:
            if hasattr(model_instance, attr):
                if attr == "updated_at":
                    update_fields.append(attr)
                elif attr == "updated_by":
                    kwargs[attr] = self.auth_user

        for field, value in kwargs.items():
            setattr(model_instance, field, value)
            update_fields.append(field)

        model_instance.save(update_fields=update_fields)

        if not isinstance(cache_keys, list):
            cache_keys = [cache_keys]

        cache_keys.append("id")

        for cache_key in cache_keys:
            cache_key_value = getattr(model_instance, cache_key, None)
            if cache_key_value:
                cache_key = self.generate_cache_key(model_instance.model_name(), cache_key_value)
            else:
                cache_key = self.generate_cache_key(model_instance.model_name(), cache_key)
            self.clear_cache(cache_key)

        return model_instance, None
