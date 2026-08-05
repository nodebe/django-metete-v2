from rest_framework import serializers
from utils.constants import ErrorMessages
from utils.errors import ValidationError
from utils.service import format_phone_number


class RecursiveFieldSerializer(serializers.Field):
    def __init__(self, **kwargs):
        self.many = kwargs.pop("many", False)
        super().__init__(**kwargs)

    def to_representation(self, value):
        serializer_class = self.parent.__class__

        if self.many:
            return serializer_class(
                value, many=True, context=self.context
            ).data

        return serializer_class(value, context=self.context).data


class EmptySerializer(serializers.Serializer):
    pass


class ActivateDeactivateSerializer(serializers.Serializer):
    status = serializers.BooleanField(default=True)


def phone_number_serializer_validator(value):
    value = str(value)

    formatted_phone_number, error = format_phone_number(value)

    if error:
        return error

    if not formatted_phone_number:
        return ValidationError(ErrorMessages.invalid_phone_number, code="phone_number")

    return formatted_phone_number


class WebsocketChannelSerializer(serializers.Serializer):
    pass
