from django.db import models


class AuthProviders(models.TextChoices):
    email = "Email"
    google = "Google"
    facebook = "Facebook"
