from django.db import models

class Config(models.Model):
    crop_quality = models.FloatField(default=0.2, help_text="Weight for crop quality")
    demand = models.FloatField(default=0.2, help_text="Weight for demand")
    price = models.FloatField(default=0.3, help_text="Weight for price")
    weather_risk = models.FloatField(default=0.15, help_text="Weight for weather risk")
    distance = models.FloatField(default=0.1, help_text="Weight for distance")
    transport_availability = models.FloatField(default=0.1, help_text="Weight for transport availability")
    storage_availability = models.FloatField(default=0.05, help_text="Weight for storage availability")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Weight Configuration"
        verbose_name_plural = "System Weight Configurations"

    def __str__(self):
        return f"Config(price={self.price}, demand={self.demand})"

    @classmethod
    def get_config(cls):
        """
        Retrieves the first configuration instance.
        If none exists, creates a default one.
        """
        config = cls.objects.first()
        if not config:
            config = cls.objects.create(
                crop_quality=0.2,
                demand=0.2,
                price=0.3,
                weather_risk=0.15,
                distance=0.1,
                transport_availability=0.1,
                storage_availability=0.05
            )
        return config
