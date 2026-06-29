import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Location
from .utils import haversine_distance

class GeocodingAndDistanceTestCase(TestCase):
    def test_haversine_distance(self):
        # Coordinates of Ranchi Kanke: 23.4123, 85.3214
        # Coordinates of a test user near Kanke: 23.4050, 85.3100
        # Distance should be around 1.4-1.5 km
        dist = haversine_distance(23.4123, 85.3214, 23.4050, 85.3100)
        self.assertAlmostEqual(dist, 1.43, places=1)

    @patch('urllib.request.urlopen')
    def test_location_geocoding_on_save(self, mock_urlopen):
        # Mock Nominatim API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"lat": "23.4123", "lon": "85.3214"}
        ]).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Creating a location should trigger auto-geocoding
        location = Location.objects.create(
            city="Ranchi",
            area="Kanke",
            pin_code="834006",
            service_radius=5.00,
            delivery_time_days_min=1,
            delivery_time_days_max=3
        )

        self.assertIsNotNone(location.latitude)
        self.assertIsNotNone(location.longitude)
        self.assertEqual(float(location.latitude), 23.4123)
        self.assertEqual(float(location.longitude), 85.3214)

class CheckDeliveryAPITestCase(APITestCase):
    def setUp(self):
        # Bypassing the network call by manually setting coordinates in DB
        self.service_location = Location.objects.create(
            city="Ranchi",
            area="Kanke",
            pin_code="834006",
            latitude=23.4123,
            longitude=85.3214,
            service_radius=5.00,
            delivery_time_days_min=1,
            delivery_time_days_max=3,
            is_serviceable=True
        )

    def test_check_delivery_serviceable(self):
        url = reverse('check-delivery')
        # Ranchi user within 5km radius: distance is approx 1.43km
        data = {
            "latitude": 23.4050,
            "longitude": 85.3100
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["serviceable"])
        self.assertIn("1.4 km", response.data["distance"])
        self.assertEqual(response.data["message"], "Delivery available")
        self.assertEqual(response.data["delivery_time"], "1-3 days")

    def test_check_delivery_not_serviceable(self):
        url = reverse('check-delivery')
        # Ranchi user far away: distance is approx 9.2km
        data = {
            "latitude": 23.4500,
            "longitude": 85.4000
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["serviceable"])
        self.assertIn("9 km", response.data["distance"])
        self.assertEqual(response.data["message"], "Currently we are not delivering in your area")

    def test_check_delivery_missing_params(self):
        url = reverse('check-delivery')
        data = {
            "latitude": 23.4050
            # longitude is missing
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("latitude and longitude are required", response.data["detail"])
