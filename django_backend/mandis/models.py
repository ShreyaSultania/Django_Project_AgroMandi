from django.db import models

class Mandi(models.Model):
    name = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'state'], name='unique_mandi_name_state')
        ]
        verbose_name = "Mandi"
        verbose_name_plural = "Mandis"

    def __str__(self):
        return f"{self.name} ({self.district}, {self.state})"


class Recommendation(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    # Farmer details
    farmer_village = models.CharField(max_length=255)
    farmer_district = models.CharField(max_length=255)
    farmer_state = models.CharField(max_length=255)
    farmer_latitude = models.FloatField(null=True, blank=True)
    farmer_longitude = models.FloatField(null=True, blank=True)

    # Crop details
    commodity = models.CharField(max_length=255)
    quantity = models.FloatField(default=10.0)
    crop_quality = models.CharField(max_length=50, default="80")

    # Selected mandi details
    selected_mandi_name = models.CharField(max_length=255)
    selected_mandi_district = models.CharField(max_length=255)
    distance_km = models.FloatField(default=0.0)
    modal_price = models.FloatField(default=0.0)
    min_price = models.FloatField(null=True, blank=True)
    max_price = models.FloatField(null=True, blank=True)
    transport_cost = models.FloatField(default=0.0)
    net_profit = models.FloatField(default=0.0)
    dps_now = models.FloatField(null=True, blank=True)
    dps_later = models.FloatField(null=True, blank=True)
    best_dps = models.FloatField(default=0.0)
    decision = models.CharField(max_length=100, default="Transport Now")
    rank = models.IntegerField(default=1)

    # Context
    weather_risk = models.FloatField(null=True, blank=True)
    transport_availability = models.CharField(max_length=50, null=True, blank=True)
    storage_availability = models.CharField(max_length=50, null=True, blank=True)
    total_mandis_evaluated = models.IntegerField(null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="confirmed")

    # Extra JSON blob to preserve raw nested structure
    raw_details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"

    def __str__(self):
        return f"Recommendation #{self.id} - {self.commodity} to {self.selected_mandi_name}"
