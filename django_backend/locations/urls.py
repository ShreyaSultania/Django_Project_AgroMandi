from django.urls import path, re_path
from .views import ReverseGeocodeView

urlpatterns = [
    path('reverse', ReverseGeocodeView.as_view(), name='location-reverse'),
    path('reverse/', ReverseGeocodeView.as_view(), name='location-reverse-slash'),
]
