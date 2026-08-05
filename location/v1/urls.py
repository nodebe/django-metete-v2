from django.urls import path

from location.v1.views import CountryApiView, StateApiView, CityApiView


urlpatterns = [
    path("countries", CountryApiView.as_view(), name="country"),
    path("countries/<int:country_id>/states", StateApiView.as_view(), name="state"),
    path("states/<int:state_id>/cities", CityApiView.as_view(), name="city"),
]