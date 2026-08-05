from rest_framework import serializers
from roles_permissions.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "label",  "group_name"]


class CreateEditRoleSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    user_can_be_created_by = serializers.ListField()
    permission_ids = serializers.ListField(child=serializers.IntegerField())


class VerySimpleRoleSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    is_default = serializers.BooleanField(default=False)


class SimpleRoleSerializer(VerySimpleRoleSerializer):
    description = serializers.CharField(required=True)


class RoleSerializer(SimpleRoleSerializer):
    label = serializers.CharField(required=True)
    permissions = PermissionSerializer(many=True)
