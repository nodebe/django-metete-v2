from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from location.models import Country, State
from location.v1.models import City
from location.v1.serializers import CitySerializer, CountrySerializer, StateSerializer


class CountryApiViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('country')
        self.country1 = Country.objects.create(name="Country1")
        self.country2 = Country.objects.create(name="Country2")

    @patch('location.v1.views.location_service.fetch_countries')
    def test_get_countries(self, mock_fetch_countries):
        mock_fetch_countries.return_value = [self.country1, self.country2]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data, CountrySerializer([self.country1, self.country2], many=True).data)

    @patch('location.v1.views.location_service.fetch_countries')
    def test_get_countries_with_error(self, mock_fetch_countries):
        mock_fetch_countries.side_effect = Exception("Test error")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class StateApiViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.country = Country.objects.create(name="Country1")
        self.state1 = State.objects.create(name="State1", country=self.country)
        self.state2 = State.objects.create(name="State2", country=self.country)
        self.url = reverse('state', kwargs={'country_id': self.country.id})

    @patch('location.v1.views.location_service.fetch_states')
    def test_get_states(self, mock_fetch_states):
        mock_fetch_states.return_value = [self.state1, self.state2]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data, StateSerializer([self.state1, self.state2], many=True).data)

    @patch('location.v1.views.location_service.fetch_states')
    def test_get_states_with_error(self, mock_fetch_states):
        mock_fetch_states.side_effect = Exception("Test error")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class CityApiViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.country = Country.objects.create(name="Country1")
        self.state = State.objects.create(name="State1", country=self.country)
        self.city1 = City.objects.create(name="City1", state=self.state)
        self.city2 = City.objects.create(name="City2", state=self.state)
        self.url = reverse('city',
                           kwargs={'state_id': self.state.id})  # Ensure this is the correct URL name for your view

    @patch('location.v1.views.location_service.fetch_cities')
    def test_get_cities(self, mock_fetch_cities):
        mock_fetch_cities.return_value = [self.city1, self.city2]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data, CitySerializer([self.city1, self.city2], many=True).data)

    @patch('location.v1.views.location_service.fetch_cities')
    def test_get_cities_with_error(self, mock_fetch_cities):
        mock_fetch_cities.side_effect = Exception("Test error")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
