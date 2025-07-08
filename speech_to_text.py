import pygame
import speech_recognition as sr
import threading
import time
import queue
import os

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException

# --- Configuration ---
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
PISTA_GREEN = "#93C572" # Hex code for a nice 'pista' green

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
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.is_calibrated = True
            self.message_queue.put("STATUS: Calibration complete. Waiting for you to speak.")

            while self.running:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=7)
                    self.message_queue.put("STATUS: Recognizing speech...")
                    text = self.recognizer.recognize_google(audio)
                    self.message_queue.put(f"RECOGNIZED: {text.lower()}")

                except sr.WaitTimeoutError:
                    pass # Continue waiting quietly if no speech detected
                except sr.UnknownValueError:
                    self.message_queue.put("ERROR: Google Speech Recognition could not understand audio. Try again.")
                except sr.RequestError as e:
                    self.message_queue.put(f"ERROR: Could not request results from Google Speech Recognition service; {e}. Check internet.")
                except Exception as e:
                    self.message_queue.put(f"ERROR: An unexpected audio error occurred: {e}. Attempting to reinitialize.")
                    self.microphone = sr.Microphone()
                    self.is_calibrated = False
                    self.message_queue.put("STATUS: Attempting to recalibrate microphone after error...")
                    time.sleep(1)
                    try:
                        with self.microphone as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=2)
                        self.is_calibrated = True
                        self.message_queue.put("STATUS: Recalibration successful.")
                    except Exception as recal_e:
                        self.message_queue.put(f"FATAL_ERROR: Recalibration failed: {recal_e}. Please restart the program.")
                        self.running = False

                time.sleep(0.1)
        except Exception as e:
            self.message_queue.put(f"FATAL_ERROR: Voice listener failed to start: {e}. Ensure microphone is available and working.")
            self.running = False


    def stop(self):
        self.running = False

# --- Pygame Main Application ---
class PygameVoiceEcho:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Voice Echo Browser") # Updated caption
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)

        self.status_messages = []
        self.last_recognized_speech = "No speech detected yet."
        self.message_queue = queue.Queue()
        self.browser_driver = None # Will hold the Selenium WebDriver instance
        # current_listener_status and doraemon_image removed

        self.voice_listener_thread = VoiceListener(self.message_queue)
        self.voice_listener_thread.start()

    def _add_status_message(self, message):
        """Adds a message to the status display, keeping only the last few."""
        self.status_messages.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        if len(self.status_messages) > 15:
            self.status_messages = self.status_messages[-15:]
        # No update to current_listener_status needed here anymore

    def _initialize_browser_once(self, browser_type='chrome'):
        """Initializes a Selenium WebDriver instance if not already open."""
        if self.browser_driver:
            return True # Browser is already open

        self._add_status_message(f"ACTION: Opening {browser_type.capitalize()} browser for display...")
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
                self._add_status_message("ERROR: Unsupported browser type requested. Using Chrome as default.")
                service = ChromeService(ChromeDriverManager().install())
                self.browser_driver = webdriver.Chrome(service=service)

            self._add_status_message(f"STATUS: {self.browser_driver.name.capitalize()} browser launched successfully.")
            return True
        except SessionNotCreatedException as e:
            self._add_status_message(f"FATAL_ERROR: Failed to create browser session: {e}.")
            self._add_status_message("INFO: Browser/driver version might be incompatible. Update your browser.")
            return False
        except WebDriverException as e:
            self._add_status_message(f"FATAL_ERROR: WebDriver error launching browser: {e}")
            self._add_status_message("INFO: Ensure browser is installed and `webdriver-manager` can download its driver.")
            return False
        except Exception as e:
            self._add_status_message(f"FATAL_ERROR: Unexpected error launching browser: {e}")
            return False

    def display_speech_in_browser(self, text_to_display):
        """Displays text directly in the Selenium-controlled browser."""
        if not self._initialize_browser_once('chrome'): # Ensure browser is open (default to Chrome)
            self._add_status_message("ERROR: Could not open browser to display speech.")
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
            self._add_status_message(f"ACTION: Displaying speech in browser: '{text_to_display[:30]}...'")
            self.browser_driver.get(f"data:text/html;charset=utf-8,{html_content}")
            return True
        except WebDriverException as e:
            self._add_status_message(f"ERROR: Failed to display speech in browser: {e}")
            self._add_status_message("INFO: Browser might have been closed unexpectedly. Trying to re-open.")
            self.browser_driver = None # Reset driver so it tries to re-initialize next time
            return False

    def close_browser_driver(self):
        """Closes the active Selenium browser instance."""
        if self.browser_driver:
            self._add_status_message("ACTION: Closing browser...")
            try:
                self.browser_driver.quit()
                self._add_status_message("STATUS: Browser closed.")
            except WebDriverException as e:
                self._add_status_message(f"WARNING: Browser already closed or error during quit: {e}")
            self.browser_driver = None
        else:
            self._add_status_message("INFO: No browser is currently open.")

    def process_recognized_speech(self, recognized_text):
        """Handles the recognized speech."""
        if recognized_text is None:
            return

        self.last_recognized_speech = recognized_text # Store the recognized text

        # Check for simple exit commands
        if "exit" in recognized_text or "quit" in recognized_text or "close game" in recognized_text:
            self._add_status_message("ACTION: Exiting application. Goodbye!")
            self.running = False # This will stop the main Pygame loop
        elif "close browser" in recognized_text: # Allow closing browser explicitly
            self.close_browser_driver()
        else:
            # Default action: display whatever was said in the browser
            self.display_speech_in_browser(recognized_text.upper())

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
            self.draw_text(self.screen, "Voice Echo", self.font_large, GREEN, SCREEN_WIDTH // 2, 30, "center") # Updated Title

            # Current Spoken Text (Last Recognized Speech)
            self.draw_text(self.screen, "Last Spoken:", self.font_medium, WHITE, 50, 100)
            self.draw_text(self.screen, self.last_recognized_speech.upper(), self.font_large, BLUE, 50, 140)

            # Listener Status
            listener_status_x = 50
            listener_status_y = 220
            self.draw_text(self.screen, "Listener Status:", self.font_medium, WHITE, listener_status_x, listener_status_y)
            # Doraemon image code removed here
            self.draw_text(self.screen, self.current_listener_status, self.font_small, LIGHT_GRAY, listener_status_x + 20, listener_status_y + 40)


            # Instructions (simplified)
            instruction_start_y = 300
            instruction_spacing = 25
            self.draw_text(self.screen, "How it works:", self.font_medium, WHITE, 50, instruction_start_y)
            self.draw_text(self.screen, "- Speak anything, and it will appear in the browser!", self.font_small, LIGHT_GRAY, 50, instruction_start_y + instruction_spacing)
            self.draw_text(self.screen, "- Say 'Close Browser' to close the browser window.", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 2))
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
                    color = (255, 165, 0)
                self.draw_text(self.screen, msg, self.font_tiny, color, 50, y_offset)
                y_offset += 15

            pygame.display.flip()
            self.clock.tick(FPS)

        # --- Cleanup ---
        self.voice_listener_thread.stop()
        self.voice_listener_thread.join()
        self.close_browser_driver() # Ensure Selenium browser is closed on exit
        pygame.quit()
        print("Application closed.")

if __name__ == "__main__":
    game = PygameVoiceEcho()
    game.run()