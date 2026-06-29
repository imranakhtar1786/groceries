from django.db import models
from .utils import fetch_coordinates_nominatim

class Location(models.Model):
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    
    # Coordinates and Radius
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    service_radius = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, help_text="Service radius in kilometers")
    
    is_serviceable = models.BooleanField(default=True)
    delivery_time_days_min = models.IntegerField(default=1)
    delivery_time_days_max = models.IntegerField(default=3)

    class Meta:
        unique_together = ('city', 'area', 'pin_code')

    def __str__(self):
        return f"{self.area}, {self.city} ({self.pin_code}) - {'Active' if self.is_serviceable else 'Inactive'}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        should_fetch = self.latitude is None or self.longitude is None
        
        if not is_new and not should_fetch:
            try:
                orig = Location.objects.get(pk=self.pk)
                if orig.city != self.city or orig.area != self.area or orig.pin_code != self.pin_code:
                    should_fetch = True
            except Location.DoesNotExist:
                pass
                
        if should_fetch:
            lat, lon = fetch_coordinates_nominatim(self.city, self.area, self.pin_code)
            if lat is not None and lon is not None:
                self.latitude = lat
                self.longitude = lon
                
        super().save(*args, **kwargs)

class Lead(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead: {self.name} - {self.area}, {self.city}"
