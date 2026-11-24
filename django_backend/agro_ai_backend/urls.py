from django.contrib import admin
from django.urls import path, re_path, include
from core.views import root_view, socket_io_handler

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_view, name='root'),
    path('api/shipments/', include('mandis.urls')),
    path('api/shipments', include('mandis.urls')),
    path('api/weather', include('weather.urls')),
    path('api/weather/', include('weather.urls')),
    path('api/prices', include('prices.urls')),
    path('api/prices/', include('prices.urls')),
    path('api/location/', include('locations.urls')),
    path('api/location', include('locations.urls')),
    path('api/', include('predictions.urls')),
    # Socket.io fallback handler
    re_path(r'^socket\.io/.*', socket_io_handler, name='socket_io'),
]
