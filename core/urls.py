from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('sys-admin-path/', admin.site.urls),
    path('api/v1/', include('api.v1')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
]
