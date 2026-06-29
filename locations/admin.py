from django.contrib import admin
from .models import Location, Lead

class LocationAdmin(admin.ModelAdmin):
    readonly_fields = ('latitude', 'longitude')
    list_display = ('area', 'city', 'pin_code', 'latitude', 'longitude', 'service_radius', 'is_serviceable')
    search_fields = ('city', 'area', 'pin_code')
    list_filter = ('is_serviceable', 'city')

class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'city', 'area', 'created_at')
    search_fields = ('name', 'phone', 'city', 'area')
    list_filter = ('city', 'created_at')

admin.site.register(Location, LocationAdmin)
admin.site.register(Lead, LeadAdmin)
