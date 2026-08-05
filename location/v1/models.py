from django.db import models
from base.models import BaseModel, AppDbModel


class Country(AppDbModel):
    """Model to Store Country"""
    name = models.CharField(max_length=300, null=False)
    code = models.CharField(max_length=300, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Countries"


class State(AppDbModel):
    """Model to store states"""
    name = models.CharField(max_length=300, null=False)
    code = models.CharField(max_length=300, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}, {self.country}"

    class Meta:
        verbose_name_plural = "States"


class City(AppDbModel):
    """Model to store cities"""
    name = models.CharField(max_length=300, null=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}, {self.state}"

    class Meta:
        verbose_name_plural = "Cities"


class Location(BaseModel):
    """Model to store addresses"""
    address_1 = models.CharField(max_length=500, null=True)
    address_2 = models.CharField(max_length=500, null=True)
    landmark = models.CharField(max_length=255, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.address_1}, {self.address_2}, {self.landmark}, {self.city}"
