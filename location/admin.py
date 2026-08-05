from django.contrib import admin
from location.v1.models import City, State, Country, Location


# @admin.register(City)
# class CityAdmin(admin.ModelAdmin):
#     list_display = ["id", "name"]
#
#
# @admin.register(State)
# class StateAdmin(admin.ModelAdmin):
#     list_display = ["id", "name", "code"]
#
#
# @admin.register(Country)
# class CountryAdmin(admin.ModelAdmin):
#     list_display = ["id", "name", "code"]
#
#
# @admin.register(Location)
# class LocationAdmin(admin.ModelAdmin):
#     list_display = ["id", "address_1", "address_2", "landmark"]
