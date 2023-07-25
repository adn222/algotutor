from django.urls import path,include
from django.contrib import admin
from . import views

urlpatterns = [
    path('', views.dashboardPage, name='dashboard'),
    path('problems/', views.problemPage, name='problems'),
    path('problems/<int:problem_id>/', views.descriptionPage, name='description'),
   path('problems/<int:problem_id>/verdict/', views.verdictPage, name='verdict'),
 #   path('leaderboard/', views.leaderboardPage, name='leaderboard'),
]