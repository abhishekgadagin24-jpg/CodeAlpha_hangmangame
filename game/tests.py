
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import GameResult, UserProfile
from .views import PREDEFINED_WORDS, MAX_INCORRECT_GUESSES, _calculate_score


class HangmanGameLogicTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_predefined_words_list(self):
        expected_words = ['PYTHON', 'DJANGO', 'COMPUTER', 'PROGRAM', 'DATABASE']
        self.assertEqual(len(PREDEFINED_WORDS), 5)
        self.assertEqual(sorted(PREDEFINED_WORDS), sorted(expected_words))

    def test_start_new_game(self):
        response = self.client.get(reverse('game'))
        self.assertEqual(response.status_code, 200)

        session = self.client.session
        self.assertIn('hangman_game', session)
        game_state = session['hangman_game']
        self.assertIn(game_state['word'], PREDEFINED_WORDS)
        self.assertEqual(game_state['incorrect_guesses'], 0)
        self.assertEqual(game_state['status'], 'PLAYING')
        self.assertEqual(game_state['score'], 0)

    def test_secret_word_hidden_during_play(self):
        response = self.client.get(reverse('game'))
        self.assertEqual(response.status_code, 200)
        game_context = response.context['game']
        self.assertIsNone(game_context['revealed_word'])
        self.assertNotIn(self.client.session['hangman_game']['word'], response.content.decode('utf-8'))

    def test_correct_letter_guess(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': [],
            'incorrect_guesses': 0,
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()

        response = self.client.post(
            reverse('guess_letter'),
            data={'letter': 'P'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_correct'])
        self.assertEqual(data['game']['incorrect_guesses'], 0)
        self.assertEqual(data['game']['remaining_attempts'], 6)
        self.assertIn('P', data['game']['masked_word'])

    def test_case_insensitive_guess(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': [],
            'incorrect_guesses': 0,
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()

        response = self.client.post(
            reverse('guess_letter'),
            data={'letter': 'p'},  # lowercase
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('P', data['game']['guessed_letters'])

    def test_incorrect_letter_guess(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': [],
            'incorrect_guesses': 0,
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()

        response = self.client.post(
            reverse('guess_letter'),
            data={'letter': 'Z'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_correct'])
        self.assertEqual(data['game']['incorrect_guesses'], 1)
        self.assertEqual(data['game']['remaining_attempts'], 5)

    def test_repeated_letter_guess(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': ['P'],
            'incorrect_guesses': 0,
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()

        response = self.client.post(
            reverse('guess_letter'),
            data={'letter': 'P'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['game']['incorrect_guesses'], 0)
        self.assertEqual(data['game']['remaining_attempts'], 6)

    def test_invalid_input(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': [],
            'incorrect_guesses': 0,
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()
        res1 = self.client.post(reverse('guess_letter'), {'letter': '9'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res1.status_code, 400)
        res2 = self.client.post(reverse('guess_letter'), {'letter': 'AB'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res2.status_code, 400)
        res3 = self.client.post(reverse('guess_letter'), {'letter': '$'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res3.status_code, 400)

    def test_winning_condition_and_score_calculation(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': ['P', 'Y', 'T', 'H', 'O'],
            'incorrect_guesses': 2,  # 2 wrong guesses previously
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()
        response = self.client.post(
            reverse('guess_letter'),
            data={'letter': 'N'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['game']['status'], 'WON')
        self.assertEqual(data['game']['score'], 80)
        self.assertEqual(data['game']['revealed_word'], 'PYTHON')

        saved_result = GameResult.objects.first()
        self.assertIsNotNone(saved_result)
        self.assertEqual(saved_result.word, 'PYTHON')
        self.assertEqual(saved_result.status, 'WON')
        self.assertEqual(saved_result.score, 80)
        self.assertEqual(saved_result.incorrect_guesses, 2)

    def test_losing_condition_after_6_incorrect_guesses(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': ['A', 'B', 'C', 'D', 'E'],
            'incorrect_guesses': 5,
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()
        response = self.client.post(
            reverse('guess_letter'),
            data={'letter': 'F'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['game']['status'], 'LOST')
        self.assertEqual(data['game']['score'], 0)
        self.assertEqual(data['game']['revealed_word'], 'PYTHON')

        saved_result = GameResult.objects.first()
        self.assertIsNotNone(saved_result)
        self.assertEqual(saved_result.status, 'LOST')
        self.assertEqual(saved_result.score, 0)
        self.assertEqual(saved_result.incorrect_guesses, 6)

    def test_prevent_guesses_after_game_ends(self):
        session = self.client.session
        session['hangman_game'] = {
            'word': 'PYTHON',
            'guessed_letters': ['P', 'Y', 'T', 'H', 'O', 'N'],
            'incorrect_guesses': 1,
            'status': 'WON',
            'score': 90,
            'game_saved': True
        }
        session.save()

        response = self.client.post(
            reverse('guess_letter'),
            data={'letter': 'A'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)


class UserAuthenticationAndLeaderboardTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration_and_profile_creation(self):
        response = self.client.post(reverse('register'), {
            'username': 'playerone',
            'email': 'playerone@example.com',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123'
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='playerone')
        self.assertTrue(user.check_password('StrongPassword123'))
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.display_name, 'playerone')

    def test_user_registration_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'playertwo',
            'email': 'playertwo@example.com',
            'password': 'PasswordA123',
            'confirm_password': 'PasswordB123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='playertwo').exists())

    def test_authenticated_user_game_persistence(self):
        user = User.objects.create_user(username='testplayer', password='testpassword123')
        self.client.login(username='testplayer', password='testpassword123')

        session = self.client.session
        session['hangman_game'] = {
            'word': 'DJANGO',
            'guessed_letters': ['D', 'J', 'A', 'N', 'G'],
            'incorrect_guesses': 1,
            'status': 'PLAYING',
            'score': 0,
            'game_saved': False
        }
        session.save()
        self.client.post(reverse('guess_letter'), {'letter': 'O'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        saved_result = GameResult.objects.get(word='DJANGO')
        self.assertEqual(saved_result.user, user)
        self.assertEqual(saved_result.score, 90)

    def test_leaderboard_calculation(self):
        user1 = User.objects.create_user(username='alice', password='password123')
        user2 = User.objects.create_user(username='bob', password='password123')
        GameResult.objects.create(user=user1, word='PYTHON', status='WON', score=90, incorrect_guesses=1, attempts_used=7)
        GameResult.objects.create(user=user1, word='DJANGO', status='WON', score=80, incorrect_guesses=2, attempts_used=8)
        GameResult.objects.create(user=user2, word='COMPUTER', status='WON', score=100, incorrect_guesses=0, attempts_used=8)

        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)
        leaderboard = response.context['leaderboard']

        self.assertEqual(leaderboard[0]['username'], 'alice')
        self.assertEqual(leaderboard[0]['total_score'], 170)
        self.assertEqual(leaderboard[0]['rank'], 1)

        self.assertEqual(leaderboard[1]['username'], 'bob')
        self.assertEqual(leaderboard[1]['total_score'], 100)
        self.assertEqual(leaderboard[1]['rank'], 2)
