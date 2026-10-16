
from django.contrib import admin
from .models import GameResult, UserProfile


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_player_name',
        'word',
        'status',
        'score',
        'incorrect_guesses',
        'attempts_used',
        'played_at'
    )
    list_filter = ('status', 'played_at')
    search_fields = ('word', 'user__username', 'user__email')
    ordering = ('-played_at',)
    readonly_fields = ('played_at',)
    list_per_page = 25

    def get_player_name(self, obj):
        return obj.user.username if obj.user else 'Guest (Anonymous)'
    get_player_name.short_description = 'Player'
    get_player_name.admin_order_field = 'user__username'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'registration_date')
    search_fields = ('user__username', 'display_name', 'user__email')
    ordering = ('-registration_date',)
