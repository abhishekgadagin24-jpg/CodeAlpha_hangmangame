
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=50, blank=True, default='')
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name if self.display_name else self.user.username

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class GameResult(models.Model):
    STATUS_CHOICES = [
        ('WON', 'Won'),
        ('LOST', 'Lost'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='game_results',
        help_text='Associated registered player or NULL for anonymous guests'
    )
    word = models.CharField(max_length=50, help_text='The secret word for the game')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, help_text='Result of the round')
    incorrect_guesses = models.PositiveIntegerField(default=0, help_text='Total count of wrong guesses (0 to 6)')
    attempts_used = models.PositiveIntegerField(default=0, help_text='Total letter guesses submitted')
    score = models.PositiveIntegerField(default=0, help_text='Calculated score for this match')
    played_at = models.DateTimeField(auto_now_add=True, help_text='Timestamp when the match concluded')

    class Meta:
        ordering = ['-played_at']
        verbose_name = 'Game Result'
        verbose_name_plural = 'Game Results'

    def __str__(self):
        player = self.user.username if self.user else 'Guest'
        return f"{player} - {self.word} ({self.status}) - Score: {self.score}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, display_name=instance.username)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
