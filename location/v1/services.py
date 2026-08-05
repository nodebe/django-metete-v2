import time
import json
import os
from location.v1.models import City, Country, State, Location
from utils.constants import ErrorMessages
from utils.service import CustomApiRequestProcessorBase


class LocationService(CustomApiRequestProcessorBase):
    def __init__(self, request=None):
        super().__init__(request)
        self.country_code = None
        self.country_name = None
        self.state_code = None
        self.state_name = None
        self.city_name = None

    def create_cities(self, country=None):
        file_path = os.path.join(os.path.dirname(__file__), 'data', 'cities.json')

        with open(file_path, 'r') as file:
            data = json.loads(file.read())

        if country:
            return self.create_city_for_country(country=country, data=data)
        else:
            return self.create_all_cities(data=data)

    def create_all_cities(self, data):
        for city_detail in data:
            self.populate_city(city_detail)

        return True

    def create_city_for_country(self, country, data):
        for city_detail in data:
            country_name = city_detail.get("country_name")
            if country_name == country:
                self.populate_city(city_detail)

    def populate_city(self, city_detail):
        try:
            self.city_name = city_detail.get("name")
            self.state_name = city_detail.get("state_name")
            self.state_code = city_detail.get("state_code")
            self.country_name = city_detail.get("country_name")
            self.country_code = city_detail.get("country_code")

            created = self.get_or_create_city()

            print(f'{created.id}. {self.city_name}==>{self.state_name}==>{self.country_name}')
        except Exception as e:
            print(e)
            time.sleep(5)

        return True

    def get_or_create_country(self):
        country, is_created = Country.objects.get_or_create(name=self.country_name, code=self.country_code)

        return country

    def get_or_create_state(self):
        state, is_created = State.objects.get_or_create(
            name=self.state_name,
            code=self.state_code,
            country=self.get_or_create_country()
        )

        return state

    def get_or_create_city(self):
        city, is_created = City.objects.get_or_create(
            name=self.city_name,
            state=self.get_or_create_state()
        )

        return city

    def fetch_countries(self):
        def __do_fetch():
            try:
                countries = Country.objects.all()
                return countries, None

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key("countries")
        return self.get_cache_value_or_default(cache_key, __do_fetch)

    def fetch_active_countries(self):
        def __do_fetch():
            try:
                countries = Country.objects.filter(is_active=True)
                return countries, None

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key("active_countries")
        return self.get_cache_value_or_default(cache_key, __do_fetch)

    def fetch_states(self, country_id):
        def __do_fetch():
            try:
                states = State.objects.filter(country_id=country_id)
                return states, None

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key("states", country_id)
        return self.get_cache_value_or_default(cache_key, __do_fetch)

    def fetch_active_states(self, country_id):
        def __do_fetch():
            try:
                states = State.objects.filter(country_id=country_id, is_active=True)
                return states, None

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key(country_id, "active_states", model=Country)
        return self.get_cache_value_or_default(cache_key, __do_fetch)

    def fetch_cities(self, state_id):
        def __do_fetch():
            try:
                cities = City.objects.filter(state_id=state_id)
                return cities, None

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key(state_id, "cities", model=State)
        return self.get_cache_value_or_default(cache_key, __do_fetch)

    def fetch_active_cities(self, state_id):
        def __do_fetch():
            try:
                cities = City.objects.filter(state_id=state_id, is_active=True)
                return cities, None

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key(state_id, "active_cities", model=State)
        return self.get_cache_value_or_default(cache_key, __do_fetch)

    def fetch_country_by_id(self, country_id):
        def __do_fetch():
            try:
                country = Country.objects.get(pk=country_id)
                return country, None

            except Country.DoesNotExist:
                return None, self.make_404(ErrorMessages.country_not_found)

            except Exception as e:
                return None, self.make_500(e, self)

        cache_key = self.generate_cache_key("country", country_id)
        return self.get_cache_value_or_default(cache_key, __do_fetch)

    def create_location(self, address):
        try:
            location = Location.objects.create(**address)
            return location, None

        except Exception as e:
            return None, self.make_500(e, self)
