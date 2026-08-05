from rest_framework import serializers
from .models import City, Country, State, Location
from .services import LocationService


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code']
        read_only_fields = ["name", "code"]

    def validate(self, attrs):
        data = attrs.copy()

        country_id = data.get("id")

        location_service = LocationService(None)
        country, error = location_service.fetch_country_by_id(country_id)

        if error:
            raise serializers.ValidationError(error.get_message())

        return country


class StateSerializer(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = State
        fields = ['id', 'name', 'code', "country"]
        read_only_fields = ["name", "code", "country"]


class CitySerializer(serializers.ModelSerializer):
    state = StateSerializer()

    class Meta:
        model = City
        fields = ['id', 'name', 'state']
        read_only_fields = ["name", "state"]


class LocationSerializer(serializers.ModelSerializer):
    state_id = serializers.PrimaryKeyRelatedField(source="state", queryset=State.objects.all(), write_only=True)
    city_id = serializers.PrimaryKeyRelatedField(source="city", queryset=City.objects.all(), write_only=True,
                                                 required=False)
    state = serializers.CharField(source="state.name", read_only=True)
    city = serializers.CharField(source="city.name", read_only=True)
    country = serializers.CharField(source="state.country.name", read_only=True)

    class Meta:
        model = Location
        fields = ["address_1", "address_2", "city_id", "state_id", "state", "city", "country"]
