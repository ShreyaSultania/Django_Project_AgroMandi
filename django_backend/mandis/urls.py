from django.urls import path
from .views import RecommendMandiView, ConfirmMandiView

urlpatterns = [
    path('recommend-mandi', RecommendMandiView.as_view(), name='recommend-mandi'),
    path('recommend-mandi/', RecommendMandiView.as_view(), name='recommend-mandi-slash'),
    path('confirm-mandi', ConfirmMandiView.as_view(), name='confirm-mandi'),
    path('confirm-mandi/', ConfirmMandiView.as_view(), name='confirm-mandi-slash'),
]
