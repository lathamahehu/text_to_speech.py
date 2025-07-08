import pygame
import speech_recognition as sr
import webbrowser
import threading
import time
import queue # For communication between threads
import os # For browser path handling

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
DARK_GRAY = (50, 50, 50) # For background elements

# Optional: Register specific browser paths if webbrowser.get() doesn't find them automatically.
# Uncomment and modify these lines with your actual browser executable paths.
# Example for Chrome on Windows:
# CHROME_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
# Example for Firefox on Windows:
# FIREFOX_PATH = 'C:/Program Files/Mozilla Firefox/firefox.exe %s'
# Example for Edge on Windows (often works without explicit registration):
# EDGE_PATH = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe %s'

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
                # Increased duration for potentially better calibration
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.is_calibrated = True
            self.message_queue.put("STATUS: Calibration complete. Ready for commands!")
            self.message_queue.put("COMMAND: Say 'Open Google in Chrome', 'Open YouTube in Firefox', etc.")

            while self.running:
                self.message_queue.put("STATUS: Listening for command...")
                try:
                    with self.microphone as source:
                        # Listen with timeout and phrase limit
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
        pygame.display.set_caption("Voice-Controlled Browser Launcher")
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)


        self.status_messages = []
        self.last_recognized_command = "None"
        self.message_queue = queue.Queue() # Queue for thread communication

        # Register custom browser paths if needed
        # Uncomment and configure these for your specific browser installations
        # try:
        #     webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(CHROME_PATH))
        #     self._add_status_message("INFO: Chrome registered successfully.")
        # except webbrowser.Error:
        #     self._add_status_message("WARNING: Could not register Chrome. Check path or it may not be installed.")
        #
        # try:
        #     webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(FIREFOX_PATH))
        #     self._add_status_message("INFO: Firefox registered successfully.")
        # except webbrowser.Error:
        #     self._add_status_message("WARNING: Could not register Firefox. Check path or it may not be installed.")
        #
        # try:
        #     webbrowser.register('edge', None, webbrowser.BackgroundBrowser(EDGE_PATH))
        #     self._add_status_message("INFO: Edge registered successfully.")
        # except webbrowser.Error:
        #     self._add_status_message("WARNING: Could not register Edge. Check path or it may not be installed.")


        self.voice_listener_thread = VoiceListener(self.message_queue)
        self.voice_listener_thread.start() # Start the voice listener thread

    def _add_status_message(self, message):
        """Adds a message to the status display, keeping only the last few."""
        self.status_messages.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        if len(self.status_messages) > 15: # Keep last 15 messages for more history
            self.status_messages = self.status_messages[-15:]

    def open_url_in_browser(self, url, browser_name=None):
        """Helper function to open a URL in a specific browser or the default."""
        try:
            if browser_name:
                self._add_status_message(f"ACTION: Opening {url} in {browser_name}...")
                browser_controller = webbrowser.get(browser_name)
                browser_controller.open_new_tab(url)
            else:
                self._add_status_message(f"ACTION: Opening {url} in default browser...")
                webbrowser.open_new_tab(url)
            return True
        except webbrowser.Error as e:
            self._add_status_message(f"ERROR: Could not open browser '{browser_name or 'default'}': {e}")
            self._add_status_message("INFO: Make sure browser is installed and its path is correctly configured or registered.")
            return False

    def execute_command(self, command_text):
        """Executes actions based on the recognized command text."""
        if command_text is None:
            return

        self.last_recognized_command = command_text

        target_browser = None
        # Check for browser specifiers first and remove them from the command
        if "in chrome" in command_text:
            target_browser = 'chrome'
            command_text = command_text.replace("in chrome", "").strip()
        elif "in firefox" in command_text:
            target_browser = 'firefox'
            command_text = command_text.replace("in firefox", "").strip()
        elif "in edge" in command_text:
            target_browser = 'microsoft-edge' # This is the internal type name for Edge
            command_text = command_text.replace("in edge", "").strip()
        elif "in default" in command_text: # Allow explicitly asking for default browser
            target_browser = None
            command_text = command_text.replace("in default", "").strip()

        # Now, check for the main command
        if "open google" in command_text:
            self.open_url_in_browser("https://www.google.com", target_browser)
        elif "open youtube" in command_text:
            # Note: The 'https://www.youtube.com' URL is not a standard way to open YouTube.
            # Using the direct YouTube URL is more reliable.
            self.open_url_in_browser("https://www.youtube.com", target_browser)
        elif "open wikipedia" in command_text:
            self.open_url_in_browser("https://www.wikipedia.org", target_browser)
        elif "open my github" in command_text: # Example of a personal command
            self.open_url_in_browser("https://github.com/your-username", target_browser) # <<< REMEMBER TO CHANGE THIS TO YOUR GITHUB USERNAME!
        elif "open website" in command_text:
            # Improved logic for "open website [URL]"
            parts = command_text.split("open website")
            if len(parts) > 1 and parts[1].strip():
                raw_url_part = parts[1].strip()
                # Basic attempt to extract a URL-like string
                # This could be made much more robust with regex
                url_to_open = raw_url_part.split(" ")[0] # Take the first word after "open website"

                if not url_to_open.startswith(("http://", "https://")):
                    url_to_open = "https://" + url_to_open # Default to HTTPS if no schema
                self.open_url_in_browser(url_to_open, target_browser)
            else:
                self._add_status_message("ERROR: No specific URL provided with 'open website'.")
                self._add_status_message("INFO: Try 'open website example.com'.")

        elif "exit" in command_text or "quit" in command_text or "close game" in command_text:
            self._add_status_message("ACTION: Exiting application. Goodbye!")
            self.running = False # This will stop the main Pygame loop
        else:
            self._add_status_message(f"INFO: Command '{command_text}' not recognized.")
            self._add_status_message("INFO: Try 'open Google in Chrome' or 'exit'.")

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
                # if event.type == pygame.KEYDOWN:
                #     if event.key == pygame.K_ESCAPE:
                #         self.running = False

            # Process messages from the voice listener thread
            self.handle_messages_from_thread()

            # --- Drawing ---
            self.screen.fill(DARK_GRAY) # Darker background

            # Title
            self.draw_text(self.screen, "Voice-Controlled Browser Launcher", self.font_large, GREEN, SCREEN_WIDTH // 2, 30, "center")

            # Last Recognized Command
            self.draw_text(self.screen, "Last Command:", self.font_medium, WHITE, 50, 100)
            # Display command in a prominent way
            self.draw_text(self.screen, self.last_recognized_command.upper(), self.font_large, BLUE, 50, 140)

            # Instructions Area
            self.draw_text(self.screen, "Available Commands:", self.font_medium, WHITE, 50, 220)
            instruction_start_y = 250
            instruction_spacing = 25
            self.draw_text(self.screen, "- 'Open Google [in Chrome/Firefox/Edge/default]'", self.font_small, LIGHT_GRAY, 50, instruction_start_y)
            self.draw_text(self.screen, "- 'Open YouTube [in ...]' (opens youtube.com)", self.font_small, LIGHT_GRAY, 50, instruction_start_y + instruction_spacing)
            self.draw_text(self.screen, "- 'Open Wikipedia [in ...]' ", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 2))
            self.draw_text(self.screen, "- 'Open My GitHub [in ...]' (customize in code)", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 3))
            self.draw_text(self.screen, "- 'Open Website [URL] [in ...]' (e.g., 'open website stackoverflow.com')", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 4))
            self.draw_text(self.screen, "- 'Exit' or 'Quit' or 'Close Game' to stop", self.font_small, LIGHT_GRAY, 50, instruction_start_y + (instruction_spacing * 5))


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
        pygame.quit()
        print("Application closed.")

if __name__ == "__main__":
    game = PygameVoiceBrowser()
    game.run()