# Generated migration for Hangman Game models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(blank=True, default='', max_length=50)),
                ('registration_date', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
        ),
        migrations.CreateModel(
            name='GameResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(help_text='The secret word for the game', max_length=50)),
                ('status', models.CharField(choices=[('WON', 'Won'), ('LOST', 'Lost')], help_text='Result of the round', max_length=10)),
                ('incorrect_guesses', models.PositiveIntegerField(default=0, help_text='Total count of wrong guesses (0 to 6)')),
                ('attempts_used', models.PositiveIntegerField(default=0, help_text='Total letter guesses submitted')),
                ('score', models.PositiveIntegerField(default=0, help_text='Calculated score for this match')),
                ('played_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp when the match concluded')),
                ('user', models.ForeignKey(blank=True, help_text='Associated registered player or NULL for anonymous guests', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='game_results', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Game Result',
                'verbose_name_plural': 'Game Results',
                'ordering': ['-played_at'],
            },
        ),
    ]
