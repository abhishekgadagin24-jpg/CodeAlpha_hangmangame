import random
import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, Q

from .models import GameResult
from .forms import UserRegistrationForm, UserLoginForm, LetterGuessForm

PREDEFINED_WORDS = [
    'PYTHON',
    'DJANGO',
    'COMPUTER',
    'PROGRAM',
    'DATABASE',
]

MAX_INCORRECT_GUESSES = 6


def _init_new_game(request):
    selected_word = random.choice(PREDEFINED_WORDS).upper()
    game_state = {
        'word': selected_word,
        'guessed_letters': [],
        'incorrect_guesses': 0,
        'status': 'PLAYING',  # 'PLAYING', 'WON', 'LOST'
        'score': 0,
        'message': 'Welcome! Click any letter below to make your first guess.',
        'message_type': 'info',
        'game_saved': False,
    }
    request.session['hangman_game'] = game_state
    request.session.modified = True
    return game_state


def _get_or_create_game_state(request):
    state = request.session.get('hangman_game')
    if not state or 'word' not in state:
        state = _init_new_game(request)
    return state


def _calculate_score(status, incorrect_guesses):
    if status == 'WON':
        return max(0, 100 - (incorrect_guesses * 10))
    return 0


def _save_completed_game(request, game_state):
    if game_state.get('game_saved'):
        return

    user = request.user if request.user.is_authenticated else None
    GameResult.objects.create(
        user=user,
        word=game_state['word'],
        status=game_state['status'],
        incorrect_guesses=game_state['incorrect_guesses'],
        attempts_used=len(game_state.get('guessed_letters', [])),
        score=game_state['score']
    )
    game_state['game_saved'] = True


def _build_client_state(game_state):
    word = game_state['word']
    guessed = set(game_state['guessed_letters'])
    status = game_state['status']

    masked_word = [char if char in guessed else '_' for char in word]
    masked_display = ' '.join(masked_word)

    correct_letters = [char for char in game_state['guessed_letters'] if char in word]
    incorrect_letters = [char for char in game_state['guessed_letters'] if char not in word]

    client_state = {
        'masked_word': masked_word,
        'masked_display': masked_display,
        'guessed_letters': game_state['guessed_letters'],
        'correct_letters': correct_letters,
        'incorrect_letters': incorrect_letters,
        'incorrect_guesses': game_state['incorrect_guesses'],
        'max_incorrect_guesses': MAX_INCORRECT_GUESSES,
        'remaining_attempts': MAX_INCORRECT_GUESSES - game_state['incorrect_guesses'],
        'attempts_used': len(game_state['guessed_letters']),
        'status': status,
        'score': game_state['score'],
        'message': game_state.get('message', ''),
        'message_type': game_state.get('message_type', 'info'),
        'is_game_over': status in ('WON', 'LOST'),
    }

    if status in ('WON', 'LOST'):
        client_state['revealed_word'] = word
    else:
        client_state['revealed_word'] = None

    return client_state

def home_view(request):
    top_players = (
        GameResult.objects.filter(user__isnull=False)
        .values('user__username')
        .annotate(
            total_score=Sum('score'),
            games_played=Count('id'),
            games_won=Count('id', filter=Q(status='WON'))
        )
        .order_by('-total_score', '-games_won')[:5]
    )

    context = {
        'top_players': top_players,
    }
    return render(request, 'home.html', context)


def game_view(request):
    game_state = _get_or_create_game_state(request)
    client_state = _build_client_state(game_state)
    alphabet = []
    word = game_state['word']
    guessed = set(game_state['guessed_letters'])

    for code in range(ord('A'), ord('Z') + 1):
        char = chr(code)
        if char in guessed:
            state = 'correct' if char in word else 'incorrect'
            disabled = True
        else:
            state = 'available'
            disabled = client_state['is_game_over']

        alphabet.append({
            'letter': char,
            'state': state,
            'disabled': disabled
        })

    context = {
        'game': client_state,
        'alphabet': alphabet,
    }
    return render(request, 'game.html', context)


@require_http_methods(["GET", "POST"])
def new_game_view(request):
    game_state = _init_new_game(request)
    client_state = _build_client_state(game_state)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'game': client_state})

    messages.info(request, "New game started! Good luck!")
    return redirect('game')


@require_http_methods(["POST"])
def guess_letter_view(request):
    game_state = _get_or_create_game_state(request)

    if game_state['status'] in ('WON', 'LOST'):
        msg = "The game has already concluded. Click 'New Game' to play again."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': msg, 'game': _build_client_state(game_state)}, status=400)
        messages.warning(request, msg)
        return redirect('game')

    # Parse submitted letter from JSON or POST form data
    raw_letter = None
    if request.content_type == 'application/json':
        try:
            body_data = json.loads(request.body.decode('utf-8'))
            raw_letter = body_data.get('letter')
        except (json.JSONDecodeError, UnicodeDecodeError):
            raw_letter = None
    else:
        raw_letter = request.POST.get('letter')

    form = LetterGuessForm({'letter': raw_letter})
    if not form.is_valid():
        error_msg = form.errors['letter'][0] if 'letter' in form.errors else "Invalid guess. Please submit a single letter."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': error_msg, 'game': _build_client_state(game_state)}, status=400)
        messages.error(request, error_msg)
        return redirect('game')

    letter = form.cleaned_data['letter']  # Sanitized single uppercase char (A-Z)
    word = game_state['word']
    guessed_letters = game_state['guessed_letters']

    if letter in guessed_letters:
        msg = f"You already guessed the letter '{letter}'. Try a different one!"
        game_state['message'] = msg
        game_state['message_type'] = 'warning'
        request.session.modified = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': msg, 'game': _build_client_state(game_state)}, status=400)
        messages.warning(request, msg)
        return redirect('game')

    guessed_letters.append(letter)
    unique_word_letters = set(word)
    guessed_set = set(guessed_letters)

    if letter in unique_word_letters:
        if unique_word_letters.issubset(guessed_set):
            game_state['status'] = 'WON'
            game_state['score'] = _calculate_score('WON', game_state['incorrect_guesses'])
            game_state['message'] = f"Congratulations! You Won! You scored {game_state['score']} points!"
            game_state['message_type'] = 'success'
            _save_completed_game(request, game_state)
        else:
            game_state['message'] = f"Correct Guess! '{letter}' is in the word."
            game_state['message_type'] = 'success'
    else:
        game_state['incorrect_guesses'] += 1
        if game_state['incorrect_guesses'] >= MAX_INCORRECT_GUESSES:
            game_state['status'] = 'LOST'
            game_state['score'] = 0
            game_state['message'] = f"Game Over! You Lost. The correct word was: {word}"
            game_state['message_type'] = 'danger'
            _save_completed_game(request, game_state)
        else:
            remaining = MAX_INCORRECT_GUESSES - game_state['incorrect_guesses']
            game_state['message'] = f"Incorrect Guess! '{letter}' is not in the word. {remaining} chances remaining."
            game_state['message_type'] = 'danger'

    request.session.modified = True
    client_state = _build_client_state(game_state)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'letter': letter,
            'is_correct': letter in unique_word_letters,
            'game': client_state
        })

    return redirect('game')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('game')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Hangman Game, {user.username}! Your account has been created.")
            return redirect('game')
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('game')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', 'game')
            return redirect(next_url)
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been logged out successfully.")
    return redirect('home')

def leaderboard_view(request):
    leaderboard_data = (
        GameResult.objects.filter(user__isnull=False)
        .values('user__username')
        .annotate(
            total_games=Count('id'),
            games_won=Count('id', filter=Q(status='WON')),
            games_lost=Count('id', filter=Q(status='LOST')),
            total_score=Sum('score')
        )
        .order_by('-total_score', '-games_won', 'total_games')
    )
    leaderboard = []
    for rank, entry in enumerate(leaderboard_data, start=1):
        total_games = entry['total_games']
        games_won = entry['games_won']
        win_rate = round((games_won / total_games) * 100, 1) if total_games > 0 else 0
        leaderboard.append({
            'rank': rank,
            'username': entry['user__username'],
            'total_games': total_games,
            'games_won': games_won,
            'games_lost': entry['games_lost'],
            'total_score': entry['total_score'] or 0,
            'win_rate': win_rate,
        })

    return render(request, 'leaderboard.html', {'leaderboard': leaderboard})


@login_required
def history_view(request):
    user_games = GameResult.objects.filter(user=request.user).order_by('-played_at')
    
    total_games = user_games.count()
    games_won = user_games.filter(status='WON').count()
    total_score = user_games.aggregate(Sum('score'))['score__sum'] or 0
    win_rate = round((games_won / total_games) * 100, 1) if total_games > 0 else 0

    context = {
        'games': user_games,
        'total_games': total_games,
        'games_won': games_won,
        'total_score': total_score,
        'win_rate': win_rate,
    }
    return render(request, 'history.html', context)
