import pygame
import speech_recognition as sr
import threading
import time
import queue
import os
from enum import Enum, auto

# --- Configuration ---
SCREEN_WIDTH = 1024  # Increased width for better game layout
SCREEN_HEIGHT = 768  # Increased height
FPS = 60             # Increased FPS for smoother animation

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (30, 30, 30) # Darker background for game feel
ACCENT_COLOR = (147, 197, 114) # Pista Green from original, now an accent

# --- Game States ---
class GameState(Enum):
    """
    Defines the different states of the game.
    This is crucial for structuring a real-time game.
    """
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    INSTRUCTIONS = auto()

# --- Voice Recognition Thread Class ---
class VoiceListener(threading.Thread):
    """
    Dedicated thread for continuous voice recognition.
    It puts recognized speech and status messages into a queue
    for the main Pygame thread to process.
    """
    def __init__(self, message_queue):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.message_queue = message_queue
        self.running = True
        self.is_calibrated = False

    def run(self):
        """
        Main loop for the voice listener thread.
        Handles microphone calibration and continuous listening.
        """
        self.message_queue.put("STATUS: Calibrating microphone for ambient noise... Please be silent.")
        try:
            with self.microphone as source:
                # Adjust for ambient noise to improve recognition accuracy
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.is_calibrated = True
            self.message_queue.put("STATUS: Calibration complete. Waiting for you to speak.")

            while self.running:
                try:
                    with self.microphone as source:
                        # Listen for audio input with a timeout and phrase time limit
                        audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=7)
                    self.message_queue.put("STATUS: Recognizing speech...")
                    # Use Google Speech Recognition to convert audio to text
                    text = self.recognizer.recognize_google(audio)
                    self.message_queue.put(f"RECOGNIZED: {text.lower()}")

                except sr.WaitTimeoutError:
                    # No speech detected within the timeout, just continue listening
                    pass
                except sr.UnknownValueError:
                    # Speech was detected but could not be understood
                    self.message_queue.put("ERROR: Google Speech Recognition could not understand audio. Try again.")
                except sr.RequestError as e:
                    # Problem with the Google Speech Recognition service (e.g., no internet)
                    self.message_queue.put(f"ERROR: Could not request results from Google Speech Recognition service; {e}. Check internet connection.")
                except Exception as e:
                    # Catch any other unexpected errors during audio processing
                    self.message_queue.put(f"ERROR: An unexpected audio error occurred: {e}. Attempting to reinitialize microphone.")
                    self.microphone = sr.Microphone() # Reinitialize microphone object
                    self.is_calibrated = False
                    self.message_queue.put("STATUS: Attempting to recalibrate microphone after error...")
                    time.sleep(1) # Give a moment before retrying calibration
                    try:
                        with self.microphone as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=2)
                        self.is_calibrated = True
                        self.message_queue.put("STATUS: Recalibration successful.")
                    except Exception as recal_e:
                        self.message_queue.put(f"FATAL_ERROR: Recalibration failed: {recal_e}. Please restart the program.")
                        self.running = False # Critical error, stop the thread

                time.sleep(0.1) # Small delay to prevent busy-waiting
        except Exception as e:
            # Fatal error during initial microphone setup
            self.message_queue.put(f"FATAL_ERROR: Voice listener failed to start: {e}. Ensure microphone is available and working.")
            self.running = False

    def stop(self):
        """Signals the thread to stop its execution."""
        self.running = False

# --- Pygame Main Application (Game Class) ---
class VoiceGame(object):
    """
    The main game class, handling Pygame initialization, game states,
    rendering, and processing voice commands.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Voice Command Adventure") # Game-oriented caption
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = GameState.MAIN_MENU # Initial game state

        # Fonts (smaller title font)
        self.font_title = pygame.font.Font(None, 48)  # Decreased from 72 to 48
        self.font_header = pygame.font.Font(None, 36)
        self.font_body = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        self.font_tiny = pygame.font.Font(None, 14)

        self.status_messages = []        # Log for internal status/errors
        self.last_recognized_speech = "No speech detected yet." # Display last recognized speech
        self.message_queue = queue.Queue() # Queue for communication from VoiceListener thread

        # Initialize voice listener thread
        self.voice_listener_thread = VoiceListener(self.message_queue)
        self.voice_listener_thread.start()

        # Game-specific variables (placeholders)
        self.player_health = 100
        self.score = 0
        self.current_level = 1

    def _add_status_message(self, message):
        """Adds a message to the status display, keeping only the last few."""
        self.status_messages.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        if len(self.status_messages) > 15:
            self.status_messages = self.status_messages[-15:]

    def draw_text(self, surface, text, font, color, x, y, align="left"):
        """Helper to draw text on the screen with alignment options."""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "center":
            text_rect.center = (x, y)
        elif align == "right":
            text_rect.right = x
        else: # left (default)
            text_rect.topleft = (x, y)
        surface.blit(text_surface, text_rect)

    def draw_button(self, surface, text, font, color, rect_color, x, y, width, height, action=None):
        """
        Draws a button and returns its Rect object.
        Can be used to check for clicks.
        """
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, rect_color, button_rect, border_radius=10)
        self.draw_text(surface, text, font, color, button_rect.centerx, button_rect.centery, align="center")
        return button_rect

    def handle_voice_command(self, command_text):
        """
        Processes voice commands based on the current game state.
        This is where your game's voice logic will live.
        """
        self._add_status_message(f"YOU SAID: {command_text.upper()}")
        command_text = command_text.lower().strip()

        if command_text in ["exit", "quit", "close game", "shutdown"]:
            self._add_status_message("ACTION: Exiting application. Goodbye!")
            self.running = False
            return

        if self.game_state == GameState.MAIN_MENU:
            if "start game" in command_text or "play" in command_text:
                self._add_status_message("ACTION: Starting game!")
                self.game_state = GameState.PLAYING
            elif "instructions" in command_text or "how to play" in command_text:
                self._add_status_message("ACTION: Showing instructions.")
                self.game_state = GameState.INSTRUCTIONS
            elif "exit" in command_text: # Already handled above, but good for clarity
                self._add_status_message("ACTION: Exiting from main menu.")
                self.running = False

        elif self.game_state == GameState.PLAYING:
            # --- Game-specific voice commands go here ---
            if "move forward" in command_text or "go ahead" in command_text:
                self._add_status_message("GAME: Player moved forward.")
                # Implement game logic for moving forward
            elif "attack" in command_text or "fight" in command_text:
                self._add_status_message("GAME: Player attacked!")
                self.score += 10 # Example: increase score on attack
            elif "check health" in command_text or "my health" in command_text:
                self._add_status_message(f"GAME: Your current health is {self.player_health}.")
            elif "pause" in command_text:
                self._add_status_message("ACTION: Game paused.")
                self.game_state = GameState.PAUSED
            else:
                self._add_status_message(f"GAME: Unrecognized command in PLAYING state: '{command_text}'")

        elif self.game_state == GameState.PAUSED:
            if "resume" in command_text or "continue" in command_text:
                self._add_status_message("ACTION: Resuming game.")
                self.game_state = GameState.PLAYING
            elif "main menu" in command_text:
                self._add_status_message("ACTION: Returning to main menu.")
                self.game_state = GameState.MAIN_MENU
            else:
                self._add_status_message(f"GAME: Unrecognized command in PAUSED state: '{command_text}'")

        elif self.game_state == GameState.INSTRUCTIONS:
            if "back" in command_text or "main menu" in command_text:
                self._add_status_message("ACTION: Returning to main menu from instructions.")
                self.game_state = GameState.MAIN_MENU
            else:
                self._add_status_message(f"GAME: Unrecognized command in INSTRUCTIONS state: '{command_text}'")

        elif self.game_state == GameState.GAME_OVER:
            if "restart" in command_text or "play again" in command_text:
                self._add_status_message("ACTION: Restarting game.")
                self.reset_game() # Reset game state for new play
                self.game_state = GameState.PLAYING
            elif "main menu" in command_text:
                self._add_status_message("ACTION: Returning to main menu from game over.")
                self.game_state = GameState.MAIN_MENU
            else:
                self._add_status_message(f"GAME: Unrecognized command in GAME_OVER state: '{command_text}'")

    def reset_game(self):
        """Resets game variables for a new game."""
        self.player_health = 100
        self.score = 0
        self.current_level = 1
        self._add_status_message("GAME: Game state reset.")

    def handle_messages_from_thread(self):
        """Processes messages from the voice listener thread."""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            if message.startswith("RECOGNIZED:"):
                speech_text = message[len("RECOGNIZED:"):].strip()
                self.last_recognized_speech = speech_text.upper() # Update displayed speech
                self.handle_voice_command(speech_text) # Process as a game command
            elif message.startswith("STATUS:") or \
                 message.startswith("ERROR:") or \
                 message.startswith("INFO:") or \
                 message.startswith("COMMAND:") or \
                 message.startswith("FATAL_ERROR:"):
                self._add_status_message(message)

    def draw_robot(self, surface, x, y, size=60):
        """Draw a simple robot at (x, y) with given size (centered)"""
        body_color = (180, 180, 200)
        head_color = (200, 200, 220)
        eye_color = (0, 0, 0)
        antenna_color = (100, 100, 100)
        # Body
        pygame.draw.rect(surface, body_color, (x - size//3, y, size//1.5, size//1.2), border_radius=8)
        # Head
        pygame.draw.rect(surface, head_color, (x - size//2, y - size//2, size, size//2), border_radius=8)
        # Eyes
        pygame.draw.circle(surface, eye_color, (x - size//4, y - size//3), size//10)
        pygame.draw.circle(surface, eye_color, (x + size//4, y - size//3), size//10)
        # Antenna
        pygame.draw.line(surface, antenna_color, (x, y - size//2), (x, y - size//1.2), 3)
        pygame.draw.circle(surface, (255,0,0), (x, int(y - size//1.2)), size//15)

    def draw_game_ui(self):
        """Draws the main game UI elements."""
        # This is where you'd draw your game world, characters, etc.
        # For now, it's just placeholders.
        self.draw_text(self.screen, f"Health: {self.player_health}", self.font_body, WHITE, 50, 50)
        self.draw_text(self.screen, f"Score: {self.score}", self.font_body, WHITE, 50, 90)
        self.draw_text(self.screen, f"Level: {self.current_level}", self.font_body, WHITE, 50, 130)

        self.draw_text(self.screen, "ADVENTURE AWAITS!", self.font_title, ACCENT_COLOR, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, "center")
        self.draw_text(self.screen, "Speak commands like 'MOVE FORWARD', 'ATTACK', 'PAUSE'", self.font_small, LIGHT_GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60, "center")
        # Draw robot if speech detected
        if self.last_recognized_speech and self.last_recognized_speech != "No speech detected yet.":
            self.draw_robot(self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150, 60)

    def draw_main_menu(self):
        """Draws the main menu screen."""
        self.screen.fill(DARK_GRAY)
        self.draw_text(self.screen, "Voice Command Adventure", self.font_title, GREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, "center")

        # Buttons/Options
        start_button = self.draw_button(self.screen, "START GAME (Say 'Start Game')", self.font_header, WHITE, BLUE,
                                        SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50, 400, 70)
        instructions_button = self.draw_button(self.screen, "INSTRUCTIONS (Say 'Instructions')", self.font_header, WHITE, BLUE,
                                               SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 40, 400, 70)
        exit_button = self.draw_button(self.screen, "EXIT (Say 'Exit')", self.font_header, WHITE, RED,
                                       SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 130, 400, 70)

        # Handle mouse clicks on buttons (for non-voice navigation)
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(mouse_pos):
                    self._add_status_message("ACTION: Mouse click - Starting game!")
                    self.game_state = GameState.PLAYING
                elif instructions_button.collidepoint(mouse_pos):
                    self._add_status_message("ACTION: Mouse click - Showing instructions.")
                    self.game_state = GameState.INSTRUCTIONS
                elif exit_button.collidepoint(mouse_pos):
                    self._add_status_message("ACTION: Mouse click - Exiting.")
                    self.running = False
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def draw_paused_screen(self):
        """Draws the paused game screen."""
        # Overlay a semi-transparent layer
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180)) # Black with 180 alpha (out of 255)
        self.screen.blit(s, (0, 0))

        self.draw_text(self.screen, "PAUSED", self.font_title, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, "center")
        self.draw_text(self.screen, "Say 'Resume' to continue", self.font_body, LIGHT_GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, "center")
        self.draw_text(self.screen, "Say 'Main Menu' to go back", self.font_body, LIGHT_GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, "center")

    def draw_instructions_screen(self):
        """Draws the instructions screen."""
        self.screen.fill(DARK_GRAY)
        self.draw_text(self.screen, "Instructions", self.font_title, GREEN, SCREEN_WIDTH // 2, 50, "center")

        instructions_text = [
            "Welcome to Voice Command Adventure!",
            "",
            "Your voice is your controller. Speak clearly!",
            "",
            "In Game:",
            "  - Say 'Move Forward', 'Go Left', 'Attack', 'Use Item' to play.",
            "  - Say 'Check Health' to know your status.",
            "  - Say 'Pause' to temporarily stop the game.",
            "",
            "In Pause Menu:",
            "  - Say 'Resume' to continue your adventure.",
            "  - Say 'Main Menu' to return to the start.",
            "",
            "General Commands (anytime):",
            "  - Say 'Exit' or 'Quit' or 'Close Game' to close the application.",
            "",
            "Try to speak naturally and clearly. Have fun!",
            "",
            "Say 'Back' or 'Main Menu' to return."
        ]
        y_pos = 150
        for line in instructions_text:
            self.draw_text(self.screen, line, self.font_small, LIGHT_GRAY, SCREEN_WIDTH // 2, y_pos, "center")
            y_pos += 30

    def draw_game_over_screen(self):
        """Draws the game over screen."""
        self.screen.fill(DARK_GRAY)
        self.draw_text(self.screen, "GAME OVER!", self.font_title, RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, "center")
        self.draw_text(self.screen, f"Final Score: {self.score}", self.font_header, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30, "center")
        self.draw_text(self.screen, "Say 'Restart' to play again", self.font_body, LIGHT_GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, "center")
        self.draw_text(self.screen, "Say 'Main Menu' to go back", self.font_body, LIGHT_GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80, "center")


    def run(self):
        """
        The main game loop. Handles events, updates game state, and renders.
        """
        while self.running:
            # Event handling (keyboard, mouse, Pygame quit)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: # Press ESC to quickly quit
                        self.running = False
                    elif event.key == pygame.K_p and self.game_state == GameState.PLAYING:
                        self._add_status_message("ACTION: Keyboard - Game paused.")
                        self.game_state = GameState.PAUSED
                    elif event.key == pygame.K_r and self.game_state == GameState.PAUSED:
                        self._add_status_message("ACTION: Keyboard - Resuming game.")
                        self.game_state = GameState.PLAYING
                    elif event.key == pygame.K_m and self.game_state in [GameState.PAUSED, GameState.GAME_OVER, GameState.INSTRUCTIONS]:
                        self._add_status_message("ACTION: Keyboard - Returning to main menu.")
                        self.game_state = GameState.MAIN_MENU
                    elif event.key == pygame.K_s and self.game_state == GameState.MAIN_MENU:
                        self._add_status_message("ACTION: Keyboard - Starting game.")
                        self.game_state = GameState.PLAYING
                    elif event.key == pygame.K_i and self.game_state == GameState.MAIN_MENU:
                        self._add_status_message("ACTION: Keyboard - Showing instructions.")
                        self.game_state = GameState.INSTRUCTIONS
                    elif event.key == pygame.K_SPACE and self.game_state == GameState.GAME_OVER:
                        self._add_status_message("ACTION: Keyboard - Restarting game.")
                        self.reset_game()
                        self.game_state = GameState.PLAYING


            # Process messages from the voice listener thread
            self.handle_messages_from_thread()

            # --- Drawing based on Game State ---
            self.screen.fill(DARK_GRAY) # Clear screen each frame

            if self.game_state == GameState.MAIN_MENU:
                self.draw_main_menu()
            elif self.game_state == GameState.PLAYING:
                # In a real game, this is where you'd update game logic (e.g., character movement, enemy AI)
                # For now, it just draws the basic game UI.
                self.draw_game_ui()
            elif self.game_state == GameState.PAUSED:
                self.draw_game_ui() # Still show game behind overlay
                self.draw_paused_screen()
            elif self.game_state == GameState.INSTRUCTIONS:
                self.draw_instructions_screen()
            elif self.game_state == GameState.GAME_OVER:
                self.draw_game_over_screen()

            # Always draw the last recognized speech and activity log for debugging/status
            self.draw_text(self.screen, "Last Spoken:", self.font_small, WHITE, SCREEN_WIDTH - 300, 30)
            self.draw_text(self.screen, self.last_recognized_speech, self.font_body, ACCENT_COLOR, SCREEN_WIDTH - 300, 60)

            self.draw_text(self.screen, "Activity Log:", self.font_small, WHITE, SCREEN_WIDTH - 300, 120)
            y_offset = 150
            for msg in reversed(self.status_messages):
                color = LIGHT_GRAY
                if msg.startswith("ERROR:") or msg.startswith("FATAL_ERROR:"):
                    color = RED
                elif msg.startswith("ACTION:") or msg.startswith("GAME:"):
                    color = BLUE
                elif msg.startswith("YOU SAID:"):
                    color = GREEN
                elif msg.startswith("WARNING:"):
                    color = (255, 165, 0) # Orange
                self.draw_text(self.screen, msg, self.font_tiny, color, SCREEN_WIDTH - 300, y_offset, align="right")
                y_offset += 15

            pygame.display.flip() # Update the full display Surface to the screen
            self.clock.tick(FPS) # Control frame rate

        # --- Cleanup on exit ---
        self.voice_listener_thread.stop()
        self.voice_listener_thread.join() # Wait for the thread to finish
        pygame.quit()
        print("Application closed.")

if __name__ == "__main__":
    game = VoiceGame()
    game.run()
