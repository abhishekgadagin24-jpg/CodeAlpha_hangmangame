
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),

    path('game/', views.game_view, name='game'),
    path('game/new/', views.new_game_view, name='new_game'),
    path('game/guess/', views.guess_letter_view, name='guess_letter'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('history/', views.history_view, name='history'),
]
