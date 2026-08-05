from rest_framework.generics import ListCreateAPIView, ListAPIView
from roles_permissions.constants import PermissionEnum
from roles_permissions.serializers import CreateEditRoleSerializer, RoleSerializer, PermissionSerializer
from roles_permissions.services import RoleService, PermissionService
from utils.service import CustomApiRequestProcessorBase


class ListPermissionsApiView(ListAPIView, CustomApiRequestProcessorBase):

    def get(self, request, *args, **k):
        filter_params = self.get_request_filter_params()
        self.response_serializer = PermissionSerializer
        self.response_serializer_requires_many = True

        service = PermissionService(request)
        return self.process_request(request, service.fetch_list, filter_params=filter_params)


class ListCreateRolesApiView(ListCreateAPIView, CustomApiRequestProcessorBase):
    serializer_class = CreateEditRoleSerializer

    def get(self, request, *args, **k):
        filter_params = self.get_request_filter_params()
        self.permission_required = PermissionEnum.view_roles

        service = RoleService(request)
        return self.process_request(request, service.fetch_paginated_list, filter_params=filter_params)

    def post(self, request, *args, **kwargs):
        self.permission_required = PermissionEnum.create_roles
        self.response_serializer = RoleSerializer

        service = RoleService(request)
        return self.process_request(request, service.create)
