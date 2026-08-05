from rest_framework import serializers


class TokenSigninSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
