from django.db import models

class Location(models.Model):
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    is_serviceable = models.BooleanField(default=True)
    delivery_time_days_min = models.IntegerField(default=1)
    delivery_time_days_max = models.IntegerField(default=3)

    class Meta:
        unique_together = ('city', 'area', 'pin_code')

    def __str__(self):
        return f"{self.area}, {self.city} ({self.pin_code}) - {'Active' if self.is_serviceable else 'Inactive'}"

class Lead(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead: {self.name} - {self.area}, {self.city}"
