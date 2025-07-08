import pygame
import speech_recognition as sr
import webbrowser
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
                self.recognizer.adjust_for_ambient_noise(source, duration=2) # Longer duration for better calibration
            self.is_calibrated = True
            self.message_queue.put("STATUS: Calibration complete. Ready for commands!")
            self.message_queue.put("COMMAND: Say 'Open Google in Chrome', 'Display What I Said', etc.")

            while self.running:
                self.message_queue.put("STATUS: Listening for command...")
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=7)
                    self.message_queue.put("STATUS: Recognizing speech...")
                    text = self.recognizer.recognize_google(audio)
                    self.message_queue.put(f"RECOGNIZED: {text.lower()}")

                except sr.WaitTimeoutError:
                    self.message_queue.put("STATUS: No speech detected. Listening again...")
                except sr.UnknownValueError:
                    self.message_queue.put("ERROR: Google Speech Recognition could not understand audio. Please speak more clearly.")
                except sr.RequestError as e:
                    self.message_queue.put(f"ERROR: Could not request results from Google Speech Recognition service; {e}. Check internet.")
                except Exception as e:
                    # Catch broad exceptions for microphone issues
                    self.message_queue.put(f"ERROR: An unexpected audio error occurred: {e}. Attempting to reinitialize.")
                    self.microphone = sr.Microphone() # Reinitialize microphone object
                    self.is_calibrated = False # Need to recalibrate
                    self.message_queue.put("STATUS: Attempting to recalibrate microphone after error...")
                    time.sleep(1) # Give a moment before trying to recalibrate
                    try:
                        with self.microphone as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=2)
                        self.is_calibrated = True
                        self.message_queue.put("STATUS: Recalibration successful.")
                    except Exception as recal_e:
                        self.message_queue.put(f"FATAL_ERROR: Recalibration failed: {recal_e}. Please restart the program.")
                        self.running = False # Stop if cannot recover microphone

                time.sleep(0.1) # Small delay to prevent busy-waiting
        except Exception as e:
            self.message_queue.put(f"FATAL_ERROR: Voice listener failed to start: {e}. Ensure microphone is available and working.")
            self.running = False


    def stop(self):
        self.running = False

# --- Pygame Main Application ---
class PygameVoiceBrowser:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Voice-Controlled Browser Launcher (Selenium)")
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)

        self.status_messages = []
        self.last_recognized_command = "None"
        self.message_queue = queue.Queue() # Queue for thread communication
        self.browser_driver = None # Will hold the Selenium WebDriver instance

        self.voice_listener_thread = VoiceListener(self.message_queue)
        self.voice_listener_thread.start() # Start the voice listener thread

    def _add_status_message(self, message):
        """Adds a message to the status display, keeping only the last few."""
        self.status_messages.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        if len(self.status_messages) > 15: # Keep last 15 messages for more history
            self.status_messages = self.status_messages[-15:]

    def initialize_browser(self, browser_type='chrome'):
        """Initializes a Selenium WebDriver instance for the specified browser."""
        if self.browser_driver:
            self._add_status_message(f"INFO: Browser already open ({self.browser_driver.name}). Closing current instance.")
            try:
                self.browser_driver.quit()
            except WebDriverException:
                pass # Already closed or not reachable
            self.browser_driver = None

        try:
            if browser_type == 'chrome':
                self._add_status_message("ACTION: Initializing Chrome browser...")
                service = ChromeService(ChromeDriverManager().install())
                self.browser_driver = webdriver.Chrome(service=service)
            elif browser_type == 'firefox':
                self._add_status_message("ACTION: Initializing Firefox browser...")
                service = FirefoxService(GeckoDriverManager().install())
                self.browser_driver = webdriver.Firefox(service=service)
            elif browser_type == 'edge':
                self._add_status_message("ACTION: Initializing Edge browser...")
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
            self._add_status_message("INFO: This often means the browser version and driver version are incompatible.")
            self._add_status_message("INFO: Please ensure your browser is updated or try 'pip install --upgrade webdriver-manager'.")
            return False
        except WebDriverException as e:
            self._add_status_message(f"FATAL_ERROR: WebDriver error launching browser: {e}")
            self._add_status_message("INFO: Ensure browser is installed and `webdriver-manager` can download its driver.")
            return False
        except Exception as e:
            self._add_status_message(f"FATAL_ERROR: Unexpected error launching browser: {e}")
            return False


    def open_url_in_selenium(self, url, browser_type=None):
        """Opens a URL in the Selenium-controlled browser."""
        if not self.browser_driver:
            # If no browser is open, try to initialize it (default to chrome)
            if not self.initialize_browser(browser_type if browser_type in ['chrome', 'firefox', 'edge'] else 'chrome'):
                self._add_status_message("ERROR: Could not open browser to navigate.")
                return False
        
        try:
            self._add_status_message(f"ACTION: Navigating browser to: {url}")
            self.browser_driver.get(url)
            return True
        except WebDriverException as e:
            self._add_status_message(f"ERROR: Failed to navigate browser: {e}")
            self._add_status_message("INFO: Browser might have been closed unexpectedly.")
            self.browser_driver = None # Reset driver state
            return False

    def display_text_in_browser(self, text_to_display):
        """Displays text directly in the Selenium-controlled browser."""
        if not self.browser_driver:
            self._add_status_message("ERROR: No browser open to display text in. Opening Chrome...")
            if not self.initialize_browser('chrome'): # Open default if not already open
                return False

        # Create a simple HTML page as a data URI
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Recognized Speech</title>
            <style>
                body {{ font-family: sans-serif; background-color: #333; color: #EEE; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                h1 {{ font-size: 4em; text-align: center; max-width: 90%; word-wrap: break-word; }}
            </style>
        </head>
        <body>
            <h1>"{text_to_display}"</h1>
        </body>
        </html>
        """
        # Encode for data URI
        encoded_html = html_content.replace('"', "'").encode('utf-8').hex()
        data_uri = f"data:text/html;charset=utf-8,%s" % encoded_html # %s will be the hex string

        try:
            self._add_status_message(f"ACTION: Displaying text in browser: '{text_to_display[:30]}...'")
            self.browser_driver.get(f"data:text/html;charset=utf-8,{html_content}")
            return True
        except WebDriverException as e:
            self._add_status_message(f"ERROR: Failed to display text in browser: {e}")
            self._add_status_message("INFO: Browser might have been closed unexpectedly.")
            self.browser_driver = None
            return False


    def close_browser(self):
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

    def execute_command(self, command_text):
        """Executes actions based on the recognized command text."""
        if command_text is None:
            return

        self.last_recognized_command = command_text

        target_browser_type = None
        # Check for browser specifiers first and remove them from the command
        if "in chrome" in command_text:
            target_browser_type = 'chrome'
            command_text = command_text.replace("in chrome", "").strip()
        elif "in firefox" in command_text:
            target_browser_type = 'firefox'
            command_text = command_text.replace("in firefox", "").strip()
        elif "in edge" in command_text:
            target_browser_type = 'edge'
            command_text = command_text.replace("in edge", "").strip()
        elif "in default" in command_text: # Allow explicitly asking for default browser (will use system default if no Selenium driver active)
            target_browser_type = 'default' # Special handling for default system browser
            command_text = command_text.replace("in default", "").strip()


        # --- Primary Commands ---
        if "open google" in command_text:
            if target_browser_type == 'default':
                webbrowser.open("https://www.google.com")
                self._add_status_message("ACTION: Opening Google in system default browser.")
            else:
                self.open_url_in_selenium("https://www.google.com", target_browser_type)
        elif "open youtube" in command_text:
            if target_browser_type == 'default':
                webbrowser.open("https://www.youtube.com")
                self._add_status_message("ACTION: Opening YouTube in system default browser.")
            else:
                self.open_url_in_selenium("https://www.youtube.com", target_browser_type)
        elif "open wikipedia" in command_text:
            if target_browser_type == 'default':
                webbrowser.open("https://www.wikipedia.org")
                self._add_status_message("ACTION: Opening Wikipedia in system default browser.")
            else:
                self.open_url_in_selenium("https://www.wikipedia.org", target_browser_type)
        elif "open my github" in command_text:
            if target_browser_type == 'default':
                webbrowser.open("https://github.com/your-username") # <<< REMEMBER TO CHANGE THIS TO YOUR GITHUB USERNAME!
                self._add_status_message("ACTION: Opening GitHub in system default browser.")
            else:
                self.open_url_in_selenium("https://github.com/your-username", target_browser_type) # <<< REMEMBER TO CHANGE THIS!
        elif "open website" in command_text:
            parts = command_text.split("open website")
            if len(parts) > 1 and parts[1].strip():
                raw_url_part = parts[1].strip()
                url_to_open = raw_url_part.split(" ")[0] # Take the first word after "open website"

                if not url_to_open.startswith(("http://", "https://")):
                    url_to_open = "https://" + url_to_open # Default to HTTPS if no schema
                
                if target_browser_type == 'default':
                    webbrowser.open(url_to_open)
                    self._add_status_message(f"ACTION: Opening {url_to_open} in system default browser.")
                else:
                    self.open_url_in_selenium(url_to_open, target_browser_type)
            else:
                self._add_status_message("ERROR: No specific URL provided with 'open website'.")
                self._add_status_message("INFO: Try 'open website example.com'.")

        elif "display what I said" in command_text or "show last command" in command_text:
            self.display_text_in_browser(self.last_recognized_command.upper())

        elif "close browser" in command_text:
            self.close_browser()

        elif "exit" in command_text or "quit" in command_text or "close game" in command_text:
            self._add_status_message("ACTION: Exiting application. Goodbye!")
            self.running = False # This will stop the main Pygame loop
        else:
            self._add_status_message(f"INFO: Command '{command_text}' not recognized.")
            self._add_status_message("INFO: Try 'Open Google in Chrome' or 'Display what I said'.")

    def handle_messages_from_thread(self):
        """Processes messages from the voice listener thread."""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            if message.startswith("RECOGNIZED:"):
                command_text = message[len("RECOGNIZED:"):].strip()
                self._add_status_message(f"YOU SAID: {command_text.upper()}") # Display recognized text in upper for emphasis
                self.execute_command(command_text)
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
                # Example: Add keyboard events for immediate exit for development
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: # Press ESC to quickly quit
                        self.running = False

            # Process messages from the voice listener thread
            self.handle_messages_from_thread()

            # --- Drawing ---
            self.screen.fill(DARK_GRAY) # Darker background

            # Title
            self.draw_text(self.screen, "Voice-Controlled Browser Launcher (Selenium)", self.font_large, GREEN, SCREEN_WIDTH // 2, 30, "center")

            # Last Recognized Command
            self.draw_text(self.screen, "Last Command:", self.font_medium, WHITE, 50, 100)
            self.draw_text(self.screen, self.last_recognized_command.upper(), self.font_large, BLUE, 50, 140)

            # Instructions Area
            self.draw_text(self.screen, "Available Commands:", self.font_medium, WHITE, 50, 220)
            instruction_start_y = 250
            instruction_spacing = 25
            self.draw_text(self.screen, "- 'Open Google [in Chrome/Firefox/Edge/default]'", self.font_small, LIGHT_GRAY, 50, instruction_start_y)
            self.draw_text(self.screen, "- 'Open YouTube [in ...]' ", self.font_small, LIGHT_GRAY, 50, instruction_start_y + instruction_spacing)
            self.draw_text(self.screen, "- 'Open Wikipedia [in ...]' ", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 2))
            self.draw_text(self.screen, "- 'Open My GitHub [in ...]' (customize in code)", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 3))
            self.draw_text(self.screen, "- 'Open Website [URL] [in ...]' (e.g., 'open website stackoverflow.com')", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 4))
            self.draw_text(self.screen, "- 'Display What I Said' or 'Show Last Command'", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 5))
            self.draw_text(self.screen, "- 'Close Browser' ", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 6))
            self.draw_text(self.screen, "- 'Exit' or 'Quit' or 'Close Game' to stop", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 7))


            # Status Messages Log
            self.draw_text(self.screen, "Status Log:", self.font_medium, WHITE, 50, 420)
            y_offset = 450
            for msg in reversed(self.status_messages): # Display newest messages at the top of the log
                color = LIGHT_GRAY
                if msg.startswith("ERROR:"):
                    color = RED
                elif msg.startswith("ACTION:"):
                    color = BLUE
                elif msg.startswith("YOU SAID:"):
                    color = GREEN
                elif msg.startswith("FATAL_ERROR:"):
                    color = RED
                elif msg.startswith("WARNING:"):
                    color = (255, 165, 0) # Orange
                self.draw_text(self.screen, msg, self.font_tiny, color, 50, y_offset)
                y_offset += 15 # Tighter line spacing for log

            pygame.display.flip()
            self.clock.tick(FPS)

        # --- Cleanup ---
        self.voice_listener_thread.stop() # Tell the thread to stop its loop
        self.voice_listener_thread.join() # Wait for the thread to finish
        self.close_browser() # Close the Selenium browser instance when Pygame exits
        pygame.quit()
        print("Application closed.")

if __name__ == "__main__":
    game = PygameVoiceBrowser()
    game.run()