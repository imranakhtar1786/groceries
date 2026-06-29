from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from .models import Location, Lead
from .serializers import LocationSerializer, LeadSerializer
from .utils import haversine_distance

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    @action(detail=False, methods=['post'])
    def check_serviceability(self, request):
        pin_code = request.data.get('pin_code')
        location = Location.objects.filter(pin_code=pin_code, is_serviceable=True).first()
        if location:
            return Response({'available': True, 'location': LocationSerializer(location).data})
        return Response({'available': False})

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

class CheckDeliveryView(APIView):
    """
    POST /api/check-delivery/
    Request:
    {
      "latitude": 23.4050,
      "longitude": 85.3100
    }
    """
    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if latitude is None or longitude is None:
            return Response(
                {"detail": "latitude and longitude are required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user_lat = float(latitude)
            user_lon = float(longitude)
        except ValueError:
            return Response(
                {"detail": "latitude and longitude must be valid float/decimal values."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get active serviceable locations with coordinates populated
        active_locations = Location.objects.filter(
            is_serviceable=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        if not active_locations.exists():
            return Response({
                "serviceable": False,
                "distance": "N/A",
                "message": "Currently we are not delivering in your area"
            }, status=status.HTTP_200_OK)
            
        closest_location = None
        closest_distance = float('inf')
        
        for loc in active_locations:
            dist = haversine_distance(user_lat, user_lon, loc.latitude, loc.longitude)
            if dist < closest_distance:
                closest_distance = dist
                closest_location = loc
                
        def format_distance(dist):
            if dist.is_integer() or round(dist, 1) == round(dist):
                return f"{int(round(dist))} km"
            return f"{dist:.1f} km"
            
        if closest_location and closest_distance <= float(closest_location.service_radius):
            min_days = closest_location.delivery_time_days_min
            max_days = closest_location.delivery_time_days_max
            return Response({
                "serviceable": True,
                "distance": format_distance(closest_distance),
                "message": "Delivery available",
                "delivery_time": f"{min_days}-{max_days} days"
            }, status=status.HTTP_200_OK)
            
        return Response({
            "serviceable": False,
            "distance": format_distance(closest_distance) if closest_location else "N/A",
            "message": "Currently we are not delivering in your area"
        }, status=status.HTTP_200_OK)
