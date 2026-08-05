from django.urls import path, include, re_path


urlpatterns = [
    path("auth/", include("account.v1.urls.auth")),
    path("profile/", include("account.v1.urls.profile")),
    path("roles/", include("roles_permissions.urls")),
    path("users/", include("account.v1.urls.user")),
    # path("crm/", include("crm.v1.urls.crm")),
    path("media/", include("media.urls")),
    path("location/", include("location.v1.urls")),
]
