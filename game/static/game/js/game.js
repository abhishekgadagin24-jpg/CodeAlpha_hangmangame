/**
 * Hangman Game - Interactive Frontend Controller
 * Communicates with Django backend endpoints via asynchronous fetch()
 */

document.addEventListener('DOMContentLoaded', () => {
    // ------------------------------------------------------------------------
    // DOM Element References
    // ------------------------------------------------------------------------
    const keyboardGrid = document.getElementById('keyboardGrid');
    const wordDisplay = document.getElementById('wordDisplay');
    const wordRevealBox = document.getElementById('wordRevealBox');
    const gameMessageBox = document.getElementById('gameMessageBox');
    const gameMessageText = document.getElementById('gameMessageText');
    const gameStatusBadge = document.getElementById('gameStatusBadge');
    const gameScoreValue = document.getElementById('gameScoreValue');

    const statIncorrectCount = document.getElementById('statIncorrectCount');
    const statRemainingCount = document.getElementById('statRemainingCount');
    const statAttemptsUsed = document.getElementById('statAttemptsUsed');
    const mistakeProgressBar = document.getElementById('mistakeProgressBar');

    const correctLettersList = document.getElementById('correctLettersList');
    const incorrectLettersList = document.getElementById('incorrectLettersList');

    const btnNewGame = document.getElementById('btnNewGame');
    const btnRestartGame = document.getElementById('btnRestartGame');

    // SVG Body Parts mapping (1 to 6)
    const bodyParts = [
        document.getElementById('partHead'),      // 1
        document.getElementById('partBody'),      // 2
        document.getElementById('partLeftArm'),   // 3
        document.getElementById('partRightArm'),  // 4
        document.getElementById('partLeftLeg'),   // 5
        document.getElementById('partRightLeg')   // 6
    ];

    // Concurrency lock to prevent double submissions
    let isSubmitting = false;

    // ------------------------------------------------------------------------
    // Helper: Retrieve CSRF Token from Meta or Cookie
    // ------------------------------------------------------------------------
    function getCsrfToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag && metaTag.content) {
            return metaTag.content;
        }

        // Fallback: parse cookie
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];

        return cookieValue || '';
    }

    // ------------------------------------------------------------------------
    // UI Update Functions
    // ------------------------------------------------------------------------
    function updateMessage(text, type = 'info') {
        if (!gameMessageBox || !gameMessageText) return;
        gameMessageText.textContent = text;
        gameMessageBox.className = `game-message alert alert-${type}`;
    }

    function updateHangmanSvg(incorrectCount) {
        bodyParts.forEach((part, index) => {
            if (!part) return;
            if (index < incorrectCount) {
                part.classList.add('part-visible');
            } else {
                part.classList.remove('part-visible');
            }
        });
    }

    function updateWordSlots(maskedWord) {
        if (!wordDisplay) return;
        wordDisplay.innerHTML = '';
        maskedWord.forEach(char => {
            const slot = document.createElement('span');
            slot.className = `letter-slot ${char !== '_' ? 'revealed' : ''}`;
            slot.textContent = char;
            wordDisplay.appendChild(slot);
        });
    }

    function updateLetterTags(container, letters, tagClass) {
        if (!container) return;
        container.innerHTML = '';
        if (!letters || letters.length === 0) {
            const emptySpan = document.createElement('span');
            emptySpan.className = 'text-muted small';
            emptySpan.textContent = 'None yet';
            container.appendChild(emptySpan);
            return;
        }

        letters.forEach(letter => {
            const tag = document.createElement('span');
            tag.className = `tag ${tagClass}`;
            tag.textContent = letter;
            container.appendChild(tag);
        });
    }

    function updateGameStateUI(gameState) {
        // 1. Update Word Slots
        updateWordSlots(gameState.masked_word);

        // 2. Update Hangman SVG Graphic
        updateHangmanSvg(gameState.incorrect_guesses);

        // 3. Update Statistics
        if (statIncorrectCount) statIncorrectCount.textContent = gameState.incorrect_guesses;
        if (statRemainingCount) statRemainingCount.textContent = gameState.remaining_attempts;
        if (statAttemptsUsed) statAttemptsUsed.textContent = gameState.attempts_used;
        if (gameScoreValue) gameScoreValue.textContent = gameState.score;

        // 4. Update Progress Bar
        if (mistakeProgressBar) {
            const percent = (gameState.incorrect_guesses / gameState.max_incorrect_guesses) * 100;
            mistakeProgressBar.style.width = `${percent}%`;
        }

        // 5. Update Correct / Incorrect Tag Badges
        updateLetterTags(correctLettersList, gameState.correct_letters, 'tag-correct');
        updateLetterTags(incorrectLettersList, gameState.incorrect_letters, 'tag-incorrect');

        // 6. Update Status Badge
        if (gameStatusBadge) {
            if (gameState.status === 'WON') {
                gameStatusBadge.className = 'badge badge-success';
                gameStatusBadge.textContent = '🎉 WON';
            } else if (gameState.status === 'LOST') {
                gameStatusBadge.className = 'badge badge-danger';
                gameStatusBadge.textContent = '💀 LOST';
            } else {
                gameStatusBadge.className = 'badge badge-info';
                gameStatusBadge.textContent = '🕹️ PLAYING';
            }
        }

        // 7. Update Feedback Message
        updateMessage(gameState.message, gameState.message_type);

        // 8. Handle Game End (Win or Loss)
        if (gameState.is_game_over) {
            // Disable all keyboard keys
            document.querySelectorAll('.key-btn').forEach(btn => btn.disabled = true);

            // Show secret word reveal box
            if (wordRevealBox && gameState.revealed_word) {
                wordRevealBox.innerHTML = `
                    <p class="reveal-text">
                        The correct word was: <strong class="revealed-word-text">${gameState.revealed_word}</strong>
                    </p>
                `;
                wordRevealBox.classList.add('is-visible');
            }
        } else {
            if (wordRevealBox) {
                wordRevealBox.classList.remove('is-visible');
                wordRevealBox.innerHTML = '';
            }
        }
    }

    // ------------------------------------------------------------------------
    // API: Submit a Letter Guess to Django Backend
    // ------------------------------------------------------------------------
    async function submitGuess(letter) {
        if (isSubmitting) return;

        const cleanLetter = letter.trim().toUpperCase();
        if (!/^[A-Z]$/.test(cleanLetter)) {
            updateMessage('Please select a valid letter from A to Z.', 'warning');
            return;
        }

        const button = document.querySelector(`.key-btn[data-letter="${cleanLetter}"]`);
        if (button && button.disabled) {
            return; // Already submitted this letter
        }

        isSubmitting = true;

        try {
            const response = await fetch('/game/guess/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ letter: cleanLetter })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Style and disable the guessed letter button
                if (button) {
                    button.disabled = true;
                    button.classList.remove('key-available');
                    button.classList.add(data.is_correct ? 'key-correct' : 'key-incorrect');
                }

                // Update full game state from server response
                updateGameStateUI(data.game);
            } else {
                // Display server error/warning message
                const errorMsg = data.error || 'Unable to process guess.';
                updateMessage(errorMsg, 'warning');
                if (data.game) {
                    updateGameStateUI(data.game);
                }
            }
        } catch (error) {
            console.error('Network or server error submitting guess:', error);
            updateMessage('Network error communicating with the server. Please check your connection.', 'danger');
        } finally {
            isSubmitting = false;
        }
    }

    // ------------------------------------------------------------------------
    // API: Start a New Game Round
    // ------------------------------------------------------------------------
    async function startNewGame() {
        if (isSubmitting) return;
        isSubmitting = true;

        try {
            const response = await fetch('/game/new/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Reset all keyboard buttons
                document.querySelectorAll('.key-btn').forEach(btn => {
                    btn.disabled = false;
                    btn.className = 'key-btn key-available';
                });

                // Update UI with fresh game state
                updateGameStateUI(data.game);
            } else {
                // Fallback to standard page reload if JSON was not returned
                window.location.reload();
            }
        } catch (error) {
            console.error('Error starting new game:', error);
            window.location.reload();
        } finally {
            isSubmitting = false;
        }
    }

    // ------------------------------------------------------------------------
    // Event Listeners: Virtual Keyboard & Physical Keyboard
    // ------------------------------------------------------------------------
    if (keyboardGrid) {
        keyboardGrid.addEventListener('click', (event) => {
            const btn = event.target.closest('.key-btn');
            if (!btn || btn.disabled) return;
            const letter = btn.getAttribute('data-letter');
            if (letter) {
                submitGuess(letter);
            }
        });
    }

    // Physical Keyboard Input
    window.addEventListener('keydown', (event) => {
        // Ignore if user is currently typing inside an input field
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }

        const key = event.key.toUpperCase();
        if (/^[A-Z]$/.test(key)) {
            const targetBtn = document.querySelector(`.key-btn[data-letter="${key}"]`);
            if (targetBtn && !targetBtn.disabled) {
                submitGuess(key);
            }
        }
    });

    // Button actions: New Game & Restart Game
    if (btnNewGame) {
        btnNewGame.addEventListener('click', () => {
            startNewGame();
        });
    }

    if (btnRestartGame) {
        btnRestartGame.addEventListener('click', () => {
            if (confirm('Are you sure you want to restart this round? A new word will be selected.')) {
                startNewGame();
            }
        });
    }
});
