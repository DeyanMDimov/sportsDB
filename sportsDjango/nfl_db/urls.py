from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('getGames/', views.index, name='getgames'),
    path('loadModel/', views.loadModel, {'target': 'showModel'}, name="showModel"),
    path('loadModelSummary/', views.loadModel, {'target': 'showSummary'}, name="modelSummary"),
    path('fullTeamStats/', views.fullTeamStats, name="fullTeamStats")
]