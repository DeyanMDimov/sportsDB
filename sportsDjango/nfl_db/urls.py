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
    path('individualStat/', views.viewIndividualStat, name="individualStat"),
    path('players/', views.getPlayers, name="getPlayers"),
    path('plays/', views.getPlays, name="getPlays"),
    path('touchdowns/', views.getTouchdowns, name="getTouchdowns"),
    path('touchdowns-mp/', views.predictTouchdowns, name="predictTouchdowns"),
    path('ajax/playerSignificance/', views.playerSignificance, name="playerSignificance"),
    path('ajax/getInjuryStatus/', views.getInjuryStatus, name="getInjuryStatus")
]