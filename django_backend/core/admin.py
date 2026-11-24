from django.contrib import admin
from .models import Config

@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'crop_quality', 'demand', 'price', 'weather_risk', 'distance', 'transport_availability', 'storage_availability', 'updated_at')
