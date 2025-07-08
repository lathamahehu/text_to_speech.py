import pygame
import speech_recognition as sr
import threading
import time
import queue
import os
import sys

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException

# --- Configuration Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
PISTA_GREEN = "#93C572"

# Paths
# This robust path handling helps PyInstaller find assets when bundled,
# and also works when running the script directly during development.
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not running as a PyInstaller bundle, use the script's directory
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# IMPORTANT: Ensure your 'doraemon_face.png' is in the 'assets/images/' subfolder
# relative to this script's location.
DORAEMON_IMAGE_PATH = get_resource_path('assets/images/doraemon_face.png')
DORAEMON_IMAGE_SIZE = (40, 40)

# Voice Recognition Settings
MICROPHONE_CALIBRATION_DURATION = 2
SPEECH_TIMEOUT = 4
PHRASE_TIME_LIMIT = 7

# UI Settings
MAX_STATUS_MESSAGES = 15
DEFAULT_BROWSER_TYPE = 'chrome'

# --- Voice Recognition Thread Class ---
class VoiceListener(threading.Thread):
    def __init__(self, message_queue):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.message_queue = message_queue
        self.running = True
        self.is_calibrated = False

    def run(self):
        self.message_queue.put("STATUS: Calibrating microphone for ambient noise... Please be silent.")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=MICROPHONE_CALIBRATION_DURATION)
            self.is_calibrated = True
            self.message_queue.put("STATUS: Calibration complete. Waiting for you to speak.")

            while self.running:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=SPEECH_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
                    self.message_queue.put("STATUS: Recognizing speech...")
                    text = self.recognizer.recognize_google(audio)
                    self.message_queue.put(f"RECOGNIZED: {text.lower()}")

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    self.message_queue.put("ERROR: Google Speech Recognition could not understand audio. Try again.")
                except sr.RequestError as e:
                    self.message_queue.put(f"ERROR: Could not request results from Google Speech Recognition service; {e}. Check internet.")
                except Exception as e:
                    self.message_queue.put(f"ERROR: An unexpected audio error occurred: {e}. Attempting to reinitialize.")
                    # Re-create microphone instance to attempt recovery
                    self.microphone = sr.Microphone() 
                    self.is_calibrated = False
                    self.message_queue.put("STATUS: Attempting to recalibrate microphone after error...")
                    time.sleep(1)
                    try:
                        with self.microphone as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=MICROPHONE_CALIBRATION_DURATION)
                        self.is_calibrated = True
                        self.message_queue.put("STATUS: Recalibration successful.")
                    except Exception as recal_e:
                        self.message_queue.put(f"FATAL_ERROR: Recalibration failed: {recal_e}. Please restart the program.")
                        self.running = False # Stop thread if recalibration fails critically

                time.sleep(0.1) # Small delay to prevent busy-waiting
        except Exception as e:
            self.message_queue.put(f"FATAL_ERROR: Voice listener failed to start: {e}. Ensure microphone is available and working.")
            self.running = False # Stop thread if initial microphone setup fails

    def stop(self):
        self.running = False

# --- Browser Controller Class ---
class BrowserController:
    def __init__(self, message_logger_callback):
        self.browser_driver = None
        self._log = message_logger_callback # Store the callback for logging messages to the UI

    def _initialize_browser_instance(self, browser_type=DEFAULT_BROWSER_TYPE):
        """Initializes a Selenium WebDriver instance. Closes any existing one first."""
        
        # Explicitly close any existing browser before opening a new one
        if self.browser_driver:
            self._log("ACTION: Closing previous browser instance...")
            try:
                self.browser_driver.quit()
            except WebDriverException:
                pass # Already closed or not reachable
            self.browser_driver = None # Ensure it's truly nullified

        self._log(f"ACTION: Opening NEW {browser_type.capitalize()} browser for display...")
        try:
            if browser_type == 'chrome':
                service = ChromeService(ChromeDriverManager().install())
                self.browser_driver = webdriver.Chrome(service=service)
            elif browser_type == 'firefox':
                service = FirefoxService(GeckoDriverManager().install())
                self.browser_driver = webdriver.Firefox(service=service)
            elif browser_type == 'edge':
                service = EdgeService(EdgeChromiumDriverManager().install())
                self.browser_driver = webdriver.Edge(service=service)
            else:
                self._log("ERROR: Unsupported browser type requested. Using Chrome as default.")
                service = ChromeService(ChromeDriverManager().install())
                self.browser_driver = webdriver.Chrome(service=service)

            self._log(f"STATUS: NEW {self.browser_driver.name.capitalize()} browser launched successfully.")
            return True
        except SessionNotCreatedException as e:
            self._log(f"FATAL_ERROR: Failed to create browser session: {e}.")
            self._log("INFO: Browser/driver version might be incompatible. Update your browser.")
            return False
        except WebDriverException as e:
            self._log(f"FATAL_ERROR: WebDriver error launching browser: {e}")
            self._log("INFO: Ensure browser is installed and `webdriver-manager` can download its driver.")
            return False
        except Exception as e:
            self._log(f"FATAL_ERROR: Unexpected error launching browser: {e}")
            return False

    def display_text_in_new_browser(self, text_to_display):
        """Displays text directly in a BRAND NEW Selenium-controlled browser."""
        
        # Force a new browser instance every time speech is displayed
        if not self._initialize_browser_instance(): # Opens a new Chrome instance (or default)
            self._log("ERROR: Could not open a new browser to display speech.")
            return False

        # Create a simple HTML page as a data URI with Pista Green font color
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Your Speech Echo</title>
            <style>
                body {{ font-family: sans-serif; background-color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                h1 {{ font-size: 4em; text-align: center; max-width: 90%; word-wrap: break-word; color: {PISTA_GREEN}; }}
            </style>
        </head>
        <body>
            <h1>"{text_to_display}"</h1>
        </body>
        </html>
        """
        try:
            self._log(f"ACTION: Displaying speech in NEW browser: '{text_to_display[:30]}...'")
            self.browser_driver.get(f"data:text/html;charset=utf-8,{html_content}")
            return True
        except WebDriverException as e:
            self._log(f"ERROR: Failed to display speech in new browser: {e}")
            self._log("INFO: Browser might have closed immediately. Trying to re-open next time.")
            self.browser_driver = None # Reset driver so it tries to re-initialize next time
            return False

    def close_browser(self):
        """Closes the active Selenium browser instance."""
        if self.browser_driver:
            self._log("ACTION: Closing browser...")
            try:
                self.browser_driver.quit()
                self._log("STATUS: Browser closed.")
            except WebDriverException as e:
                self._log(f"WARNING: Browser already closed or error during quit: {e}")
            self.browser_driver = None
        else:
            self._log("INFO: No browser is currently open.")

# --- Pygame Main Application ---
class PygameVoiceEcho:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Voice Echo Browser (Doraemon)")
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)

        self.status_messages = []
        self.last_recognized_speech = "No speech detected yet."
        self.message_queue = queue.Queue()
        self.current_listener_status = "Initializing..."

        # Pass the _add_status_message method as the logger callback
        self.browser_controller = BrowserController(self._add_status_message) 

        self.doraemon_image = None
        try:
            # The get_resource_path function ensures this works both in dev and with PyInstaller
            # Ensure your 'assets/images/doraemon_face.png' exists relative to the script.
            self.doraemon_image = pygame.image.load(DORAEMON_IMAGE_PATH).convert_alpha()
            self.doraemon_image = pygame.transform.scale(self.doraemon_image, DORAEMON_IMAGE_SIZE)
            self._add_status_message(f"INFO: Loaded Doraemon image from: {DORAEMON_IMAGE_PATH}")
        except pygame.error as e:
            self._add_status_message(f"ERROR: Could not load Doraemon image: {e}. Ensure '{DORAEMON_IMAGE_PATH}' exists and is a valid image file.")
            self.doraemon_image = None

        self.voice_listener_thread = VoiceListener(self.message_queue)
        self.voice_listener_thread.start()

    def _add_status_message(self, message):
        """Adds a message to the status display, keeping only the last few."""
        self.status_messages.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.status_messages = self.status_messages[-MAX_STATUS_MESSAGES:]
        
        # Update current listener status for emoji display
        if message.startswith("STATUS:"):
            self.current_listener_status = message[len("STATUS:"):].strip()

    def process_recognized_speech(self, recognized_text):
        """Handles the recognized speech."""
        if recognized_text is None:
            return

        self.last_recognized_speech = recognized_text # Store the recognized text

        # Check for simple exit commands (case-insensitive)
        lower_text = recognized_text.lower()
        if "exit" in lower_text or "quit" in lower_text or "close game" in lower_text:
            self._add_status_message("ACTION: Exiting application. Goodbye!")
            self.running = False # This will stop the main Pygame loop
        elif "close browser" in lower_text: # Allow closing browser explicitly
            self.browser_controller.close_browser()
        else:
            # Default action: display whatever was said in a NEW browser
            self.browser_controller.display_text_in_new_browser(recognized_text.upper())

    def handle_messages_from_thread(self):
        """Processes messages from the voice listener thread."""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            if message.startswith("RECOGNIZED:"):
                speech_text = message[len("RECOGNIZED:"):].strip()
                self._add_status_message(f"YOU SAID: {speech_text.upper()}")
                self.process_recognized_speech(speech_text)
            elif message.startswith("STATUS:") or \
                 message.startswith("ERROR:") or \
                 message.startswith("INFO:") or \
                 message.startswith("COMMAND:") or \
                 message.startswith("FATAL_ERROR:"):
                self._add_status_message(message)

    def draw_text(self, surface, text, font, color, x, y, align="left"):
        """Helper to draw text on the screen."""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "center":
            text_rect.center = (x, y)
        elif align == "right":
            text_rect.right = x
        else: # left (default)
            text_rect.topleft = (x, y)
        surface.blit(text_surface, text_rect)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: # Press ESC to quickly quit
                        self.running = False

            # Process messages from the voice listener thread
            self.handle_messages_from_thread()

            # --- Drawing ---
            self.screen.fill(DARK_GRAY)

            # Title
            self.draw_text(self.screen, "Voice Echo (Doraemon)", self.font_large, GREEN, SCREEN_WIDTH // 2, 30, "center")

            # Current Spoken Text (Last Recognized Speech)
            self.draw_text(self.screen, "Last Spoken:", self.font_medium, WHITE, 50, 100)
            self.draw_text(self.screen, self.last_recognized_speech.upper(), self.font_large, BLUE, 50, 140)

            # Listener Status with Doraemon
            listener_status_x = 50
            listener_status_y = 220
            self.draw_text(self.screen, "Listener Status:", self.font_medium, WHITE, listener_status_x, listener_status_y)
            
            status_text = self.font_small.render(self.current_listener_status, True, LIGHT_GRAY)
            status_rect = status_text.get_rect(topleft=(listener_status_x + 20, listener_status_y + 40))

            if self.doraemon_image:
                image_x = status_rect.x - DORAEMON_IMAGE_SIZE[0] - 10
                image_y = status_rect.centery - DORAEMON_IMAGE_SIZE[1] // 2
                self.screen.blit(self.doraemon_image, (image_x, image_y))
            
            self.screen.blit(status_text, status_rect)

            # Instructions (simplified)
            instruction_start_y = 300
            instruction_spacing = 25
            self.draw_text(self.screen, "How it works:", self.font_medium, WHITE, 50, instruction_start_y)
            self.draw_text(self.screen, "- Speak anything, and it will appear in a NEW browser window!", self.font_small, LIGHT_GRAY, 50, instruction_start_y + instruction_spacing)
            self.draw_text(self.screen, "- Say 'Close Browser' to close the last opened browser window.", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 2))
            self.draw_text(self.screen, "- Say 'Exit' or 'Quit' or 'Close Game' to stop this app.", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 3))

            # Status Messages Log
            self.draw_text(self.screen, "Activity Log:", self.font_medium, WHITE, 50, 420)
            y_offset = 450
            for msg in reversed(self.status_messages):
                color = LIGHT_GRAY
                if msg.startswith("ERROR:") or msg.startswith("FATAL_ERROR:"):
                    color = RED
                elif msg.startswith("ACTION:"):
                    color = BLUE
                elif msg.startswith("YOU SAID:"):
                    color = GREEN
                elif msg.startswith("WARNING:"):
                    color = (255, 165, 0) # Orange
                self.draw_text(self.screen, msg, self.font_tiny, color, 50, y_offset)
                y_offset += 15

            pygame.display.flip()
            self.clock.tick(FPS)

        # --- Cleanup ---
        self.voice_listener_thread.stop()
        self.voice_listener_thread.join()
        self.browser_controller.close_browser() # Ensure Selenium browser is closed on exit
        pygame.quit()
        print("Application closed.")

if __name__ == "__main__":
    game = PygameVoiceEcho()
    game.run()