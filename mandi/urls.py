from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("chart/<int:commodity_id>/<str:district>.png", views.trend_chart, name="trend_chart"),
    path("alerts/", views.create_alert, name="create_alert"),
    path("alerts/stop/<str:token>/", views.unsubscribe, name="unsubscribe"),
    path("lang/<str:lang>/", views.set_language, name="set_language"),
]
