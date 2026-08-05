from django.contrib import admin

from base.models import ApiRequestLogger, Activity


class BaseAdmin(admin.ModelAdmin):
    """
    A safe reusable base admin class that automatically ignores
    missing fields when applying readonly or exclude logic.
    """

    base_readonly_fields = ["updated_by", "updated_at", "created_at", "created_by"]
    base_exclude_fields = ["deactivated_by", "deleted_by", "is_deleted", "deleted_at", "deactivated_at", "password"]

    def get_readonly_fields(self, request, obj=None):
        """Return only readonly fields that exist in the model."""
        model_fields = [f.name for f in self.model._meta.get_fields()]
        return [f for f in self.base_readonly_fields if f in model_fields]

    def get_exclude(self, request, obj=None):
        """Return only exclude fields that exist in the model."""
        model_fields = [f.name for f in self.model._meta.get_fields()]
        return [f for f in self.base_exclude_fields if f in model_fields]

    def save_model(self, request, obj, form, change):
        """Auto-assign updated_by if present."""
        if not change and hasattr(obj, "created_by"):
            obj.created_by = request.user

        if hasattr(obj, "updated_by"):
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)


@admin.register(ApiRequestLogger)
class ApiRequestLoggerAdmin(BaseAdmin):
    list_display = ["ref_id", "path", "request_data", "response_body", "status", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Activity)
class ActivityAdmin(BaseAdmin):
    list_display = ["user__id", "created_at"]
    search_fields = ["user__id"]
