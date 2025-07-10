"""
Type to Voice Game
------------------
A fun and simple Pygame-based game: type any word and hear it spoken aloud!

Copyright (c) 2025 Your Name
License: MIT
"""

import pygame
import pyttsx3
import threading
import time
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BLUE = (0, 100, 255)
GREEN = (0, 255, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
DARK_GRAY = (30, 30, 30)

class SimpleVoiceEngine:
    """Handles text-to-speech using pyttsx3."""
    def __init__(self):
        self.engine = pyttsx3.init()
        self.setup_voice()
        
    def setup_voice(self):
        """Setup clear voice for speaking (force female voice if available)."""
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.5)
        voices = self.engine.getProperty('voices')
        # Try to select a female voice (by name or id)
        female_voice = None
        for v in voices:
            if 'female' in v.name.lower() or 'female' in v.id.lower() or 'zira' in v.name.lower() or 'zira' in v.id.lower():
                female_voice = v
                break
        if female_voice:
            self.engine.setProperty('voice', female_voice.id)
        elif voices:
            self.engine.setProperty('voice', voices[0].id)
    
    def speak_word(self, word):
        """Speak the exact word with voice."""
        def speak():
            try:
                self.engine.say(word)
                self.engine.runAndWait()
            except Exception:
                pass
        thread = threading.Thread(target=speak, daemon=True)
        thread.start()

class TypeToVoiceGame:
    """Main game class for Type to Voice Game."""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Type to Voice Game")
        self.clock = pygame.time.Clock()
        self.voice_engine = SimpleVoiceEngine()
        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.input_font = pygame.font.Font(None, 36)
        self.instruction_font = pygame.font.Font(None, 24)
        self.result_font = pygame.font.Font(None, 32)
        # Game state
        self.user_input = ""
        self.last_spoken = ""
        self.is_speaking = False
        self.face_color = WHITE
        # Input box
        self.input_box = pygame.Rect(SCREEN_WIDTH//2 - 200, 350, 400, 50)
        self.input_active = True
        
    def type_to_voice(self, text):
        """Convert typed text to voice."""
        if text.strip():
            self.voice_engine.speak_word(text.strip())
            self.last_spoken = text.strip()
            self.is_speaking = True
            text_lower = text.lower().strip()
            if text_lower in ["hi", "hello", "hey"]:
                self.face_color = GREEN
            elif text_lower in ["happy", "smile", "good"]:
                self.face_color = YELLOW
            elif text_lower in ["sad", "cry", "bad"]:
                self.face_color = BLUE
            elif text_lower in ["angry", "mad"]:
                self.face_color = RED
            elif text_lower in ["love", "heart"]:
                self.face_color = PINK
            else:
                self.face_color = CYAN
            estimated_time = len(text) * 0.1 + 1
            threading.Timer(estimated_time, self.stop_speaking).start()
    
    def stop_speaking(self):
        """Reset speaking status."""
        self.is_speaking = False
        self.face_color = WHITE
    
    def draw_face(self):
        """Draw a Doraemon-inspired face."""
        center = (SCREEN_WIDTH // 2, 150)
        face_radius = 60
        face_color = BLUE  # Doraemon's blue
        mouth_area_color = WHITE
        nose_color = RED
        bell_color = YELLOW
        bell_line_color = BLACK
        # Pulsing animation when speaking
        radius = face_radius
        if self.is_speaking:
            pulse = math.sin(time.time() * 8) * 8
            radius += int(pulse)
        # Draw blue face
        pygame.draw.circle(self.screen, face_color, center, radius)
        pygame.draw.circle(self.screen, BLACK, center, radius, 3)
        # Draw white mouth area (lower half)
        pygame.draw.ellipse(self.screen, mouth_area_color, (center[0] - radius + 8, center[1] - 5, (radius-8)*2, radius*1.2))
        pygame.draw.ellipse(self.screen, BLACK, (center[0] - radius + 8, center[1] - 5, (radius-8)*2, radius*1.2), 2)
        # Draw eyes
        left_eye = (center[0] - 18, center[1] - 18)
        right_eye = (center[0] + 18, center[1] - 18)
        pygame.draw.ellipse(self.screen, WHITE, (left_eye[0] - 10, left_eye[1] - 12, 20, 24))
        pygame.draw.ellipse(self.screen, WHITE, (right_eye[0] - 10, right_eye[1] - 12, 20, 24))
        pygame.draw.ellipse(self.screen, BLACK, (left_eye[0] - 10, left_eye[1] - 12, 20, 24), 2)
        pygame.draw.ellipse(self.screen, BLACK, (right_eye[0] - 10, right_eye[1] - 12, 20, 24), 2)
        # Pupils
        pygame.draw.circle(self.screen, BLACK, (left_eye[0], left_eye[1] - 2), 4)
        pygame.draw.circle(self.screen, BLACK, (right_eye[0], right_eye[1] - 2), 4)
        # Red nose
        pygame.draw.circle(self.screen, nose_color, (center[0], center[1] - 2), 8)
        pygame.draw.circle(self.screen, BLACK, (center[0], center[1] - 2), 8, 2)
        # Whiskers (3 each side)
        for i in range(-1, 2):
            pygame.draw.line(self.screen, BLACK, (center[0] - 10, center[1] + 10 + i*10), (center[0] - 40, center[1] + 5 + i*12), 2)
            pygame.draw.line(self.screen, BLACK, (center[0] + 10, center[1] + 10 + i*10), (center[0] + 40, center[1] + 5 + i*12), 2)
        # Mouth (arc)
        pygame.draw.arc(self.screen, BLACK, (center[0] - 25, center[1] + 5, 50, 30), math.radians(20), math.radians(160), 2)
        # Bell (below face)
        bell_center = (center[0], center[1] + radius + 18)
        pygame.draw.circle(self.screen, bell_color, bell_center, 13)
        pygame.draw.circle(self.screen, bell_line_color, bell_center, 13, 2)
        pygame.draw.line(self.screen, bell_line_color, (bell_center[0] - 10, bell_center[1]), (bell_center[0] + 10, bell_center[1]), 2)
        pygame.draw.circle(self.screen, bell_line_color, (bell_center[0], bell_center[1] + 6), 3)
        pygame.draw.line(self.screen, bell_line_color, (bell_center[0], bell_center[1] + 3), (bell_center[0], bell_center[1] + 10), 2)
    
    def draw_ui(self):
        """Draw the user interface."""
        title_text = self.title_font.render("Type to Voice Game", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title_text, title_rect)
        instructions = [
            "Type any word and press Enter to hear it spoken!",
            "Try: hi, hello, happy, sad, love, thank you, etc."
        ]
        for i, instruction in enumerate(instructions):
            text = self.instruction_font.render(instruction, True, LIGHT_GRAY)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 30))
            self.screen.blit(text, text_rect)
        label_text = self.instruction_font.render("Type here:", True, WHITE)
        self.screen.blit(label_text, (self.input_box.x, self.input_box.y - 30))
        pygame.draw.rect(self.screen, WHITE, self.input_box)
        pygame.draw.rect(self.screen, GREEN if self.input_active else GRAY, self.input_box, 3)
        input_surface = self.input_font.render(self.user_input, True, BLACK)
        self.screen.blit(input_surface, (self.input_box.x + 10, self.input_box.y + 10))
        if self.input_active and int(time.time() * 2) % 2:
            cursor_x = self.input_box.x + 10 + input_surface.get_width()
            pygame.draw.line(self.screen, BLACK, 
                           (cursor_x, self.input_box.y + 10), 
                           (cursor_x, self.input_box.y + 40), 2)
        if self.is_speaking:
            status = f"🔊 Speaking: '{self.last_spoken}'"
            color = GREEN
        else:
            status = "🎤 Ready - Type something!"
            color = GRAY
        status_surface = self.result_font.render(status, True, color)
        status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(status_surface, status_rect)
        examples_text = self.instruction_font.render(
            "Examples: hi → speaks 'hi', hello → speaks 'hello', happy → speaks 'happy'", 
            True, LIGHT_GRAY)
        examples_rect = examples_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
        self.screen.blit(examples_text, examples_rect)
        instruction_text = self.instruction_font.render(
            "Press Enter to speak | Press Escape to clear", 
            True, DARK_GRAY)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(instruction_text, instruction_rect)
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.user_input.strip():
                        self.type_to_voice(self.user_input)
                        self.user_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.user_input = self.user_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.user_input = ""
                else:
                    if event.unicode.isprintable() and len(self.user_input) < 50:
                        self.user_input += event.unicode
        return True
    
    def run(self):
        """Main game loop."""
        running = True
        while running:
            running = self.handle_events()
            self.screen.fill(BLACK)
            self.draw_face()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    try:
        game = TypeToVoiceGame()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have pyttsx3 installed: pip install pyttsx3")
