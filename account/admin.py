from django.contrib import admin
from account.models import User
from base.admin import BaseAdmin


# Register your models here.
@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display = ["user_id", "first_name", "last_name", "email", "phone_number", "role", "last_login"]
    search_fields = ["user_id", "email"]

    def role(self, obj):
        for role in obj.roles.all():
            return role.name if role else "-"
        return None

    BaseAdmin.base_readonly_fields += ["user_id", "last_login"]

    role.short_description = "Role"
