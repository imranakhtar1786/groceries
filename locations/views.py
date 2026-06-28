from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Location, Lead
from .serializers import LocationSerializer, LeadSerializer

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
