from django.urls import path
from .views import PricesView

urlpatterns = [
    path('', PricesView.as_view(), name='prices'),
]
