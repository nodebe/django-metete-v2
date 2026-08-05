from rest_framework.generics import ListAPIView
from location.v1.services import LocationService
from location.v1.serializers import CitySerializer, CountrySerializer, StateSerializer
from utils.service import CustomApiRequestProcessorBase


class CountryApiView(ListAPIView, CustomApiRequestProcessorBase):

    def get(self, request, *args, **kwargs):
        self.response_serializer_requires_many = True
        self.response_serializer = CountrySerializer

        service = LocationService(request)

        return self.process_request(request, service.fetch_active_countries)


class StateApiView(ListAPIView, CustomApiRequestProcessorBase):

    def get(self, request, *args, **kwargs):
        self.response_serializer_requires_many = True
        self.response_serializer = StateSerializer

        country_id = self.kwargs.get("country_id")
        service = LocationService(request)

        return self.process_request(request, service.fetch_active_states, country_id=country_id)


class CityApiView(ListAPIView, CustomApiRequestProcessorBase):

    def get(self, request, *args, **kwargs):
        self.response_serializer_requires_many = True
        self.response_serializer = CitySerializer

        state_id = self.kwargs.get("state_id")
        service = LocationService(request)

        return self.process_request(request, service.fetch_active_cities, state_id=state_id)
