from django.urls import path

from roles_permissions.views import ListPermissionsApiView, ListCreateRolesApiView


app_name = "roles_permissions"

urlpatterns = [
    path('permissions', ListPermissionsApiView.as_view(), name="list_all_permissions"),
    path('', ListCreateRolesApiView.as_view(), name="list_all_roles")
]
