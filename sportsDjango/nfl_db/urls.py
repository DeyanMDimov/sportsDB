from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('getGames/', views.getData, name='getgames'),
    path('loadModel/', views.loadModel, {'target': 'showModel'}, name="showModel"),
    path('loadModelSummary/', views.loadModel, {'target': 'showSummary'}, name="modelSummary"),
    path('fullTeamStats/', views.fullTeamStats, name="fullTeamStats"),
    path('loadYearlySummary/', views.loadModelYear, name="loadModelYear"),
    path('individualStat/', views.viewIndividualStat, name="individualStat")
]