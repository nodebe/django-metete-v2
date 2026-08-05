from django.contrib import admin
from .models import MessageTemplate, MessageVariable

# Register your models here.
models = [
    MessageTemplate, MessageVariable
]

for model in models:
    admin.site.register(model)
