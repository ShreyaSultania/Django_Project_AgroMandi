from django.urls import path
from .views import SimulateView

urlpatterns = [
    path('simulate', SimulateView.as_view(), name='simulate'),
    path('simulate/', SimulateView.as_view(), name='simulate-slash'),
]
