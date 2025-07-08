import pygame
import speech_recognition as sr
import threading
import time
import random
from collections import deque

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Color palette for text effects
COLORS = [BLUE, GREEN, RED, YELLOW, PURPLE, ORANGE, CYAN]

class SpeechToTextGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Speech-to-Text Game")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Game state
        self.running = True
        self.listening = False
        self.current_text = ""
        self.text_history = deque(maxlen=10)  # Keep last 10 speech inputs
        self.is_speaking = False
        
        # Visual effects
        self.particles = []
        self.text_color = random.choice(COLORS)
        self.background_color = BLACK
        self.pulse_alpha = 0
        self.pulse_direction = 1
        
        # Start listening thread
        self.listening_thread = threading.Thread(target=self.listen_continuously, daemon=True)
        self.listening_thread.start()
        
        # Calibrate microphone
        self.calibrate_microphone()
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Microphone calibrated!")
    
    def listen_continuously(self):
        """Continuously listen for speech in a separate thread"""
        while self.running:
            try:
                with self.microphone as source:
                    # Listen for audio with a timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Set speaking flag
                self.is_speaking = True
                
                # Recognize speech
                try:
                    text = self.recognizer.recognize_google(audio)
                    self.current_text = text
                    self.text_history.append(text)
                    self.text_color = random.choice(COLORS)
                    self.create_particles()
                    print(f"Recognized: {text}")
                except sr.UnknownValueError:
                    pass  # Speech not recognized
                except sr.RequestError as e:
                    print(f"Error with speech recognition: {e}")
                
                self.is_speaking = False
                
            except sr.WaitTimeoutError:
                # No speech detected
                self.is_speaking = False
                pass
            except Exception as e:
                print(f"Error in listening: {e}")
                time.sleep(0.1)
    
    def create_particles(self):
        """Create particle effects when speech is detected"""
        for _ in range(20):
            particle = {
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'color': random.choice(COLORS),
                'size': random.randint(2, 8),
                'life': 60  # frames
            }
            self.particles.append(particle)
    
    def update_particles(self):
        """Update particle positions and remove dead particles"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['size'] = max(1, particle['size'] - 0.1)
            
            if particle['life'] <= 0 or particle['size'] <= 1:
                self.particles.remove(particle)
    
    def draw_particles(self):
        """Draw all particles"""
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / 60))
            color = (*particle['color'], alpha)
            
            # Create a surface with alpha
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, particle['color'], 
                             (particle['size'], particle['size']), particle['size'])
            
            self.screen.blit(particle_surface, (particle['x'] - particle['size'], particle['y'] - particle['size']))
    
    def draw_text_with_effect(self, text, font, color, x, y, effect="normal"):
        """Draw text with various effects"""
        if effect == "shadow":
            # Draw shadow first
            shadow_surface = font.render(text, True, (50, 50, 50))
            self.screen.blit(shadow_surface, (x + 3, y + 3))
        
        # Draw main text
        text_surface = font.render(text, True, color)
        
        if effect == "glow":
            # Create glow effect
            glow_surface = pygame.Surface((text_surface.get_width() + 10, text_surface.get_height() + 10), pygame.SRCALPHA)
            for i in range(5):
                glow_color = (*color, 50 - i * 10)
                glow_text = font.render(text, True, glow_color)
                glow_surface.blit(glow_text, (5 - i, 5 - i))
            self.screen.blit(glow_surface, (x - 5, y - 5))
        
        self.screen.blit(text_surface, (x, y))
        return text_surface.get_rect(topleft=(x, y))
    
    def draw_microphone_indicator(self):
        """Draw microphone status indicator"""
        # Microphone icon position
        mic_x = SCREEN_WIDTH - 100
        mic_y = 50
        
        # Draw microphone background
        mic_color = GREEN if self.is_speaking else WHITE
        pygame.draw.circle(self.screen, mic_color, (mic_x, mic_y), 25)
        pygame.draw.circle(self.screen, BLACK, (mic_x, mic_y), 25, 3)
        
        # Draw microphone icon
        pygame.draw.rect(self.screen, BLACK, (mic_x - 8, mic_y - 15, 16, 20))
        pygame.draw.rect(self.screen, mic_color, (mic_x - 6, mic_y - 13, 12, 16))
        pygame.draw.rect(self.screen, BLACK, (mic_x - 2, mic_y + 8, 4, 8))
        pygame.draw.rect(self.screen, BLACK, (mic_x - 8, mic_y + 15, 16, 3))
        
        # Status text
        status_text = "LISTENING" if self.is_speaking else "READY"
        status_color = GREEN if self.is_speaking else WHITE
        self.draw_text_with_effect(status_text, self.font_small, status_color, 
                                 mic_x - 30, mic_y + 40, "shadow")
    
    def draw_waveform(self):
        """Draw animated waveform when speaking"""
        if self.is_speaking:
            wave_y = SCREEN_HEIGHT - 100
            wave_height = 50
            
            for i in range(0, SCREEN_WIDTH, 10):
                height = random.randint(10, wave_height) if self.is_speaking else 2
                color = random.choice(COLORS)
                pygame.draw.rect(self.screen, color, 
                               (i, wave_y - height//2, 8, height))
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        # Clear current text
                        self.current_text = ""
                    elif event.key == pygame.K_c:
                        # Clear history
                        self.text_history.clear()
                        self.current_text = ""
            
            # Update pulse effect
            self.pulse_alpha += self.pulse_direction * 3
            if self.pulse_alpha >= 255:
                self.pulse_alpha = 255
                self.pulse_direction = -1
            elif self.pulse_alpha <= 0:
                self.pulse_alpha = 0
                self.pulse_direction = 1
            
            # Update particles
            self.update_particles()
            
            # Clear screen
            self.screen.fill(self.background_color)
            
            # Draw particles
            self.draw_particles()
            
            # Draw title
            title_text = "🎤 Speech-to-Text Game 🎤"
            self.draw_text_with_effect(title_text, self.font_large, WHITE, 
                                     SCREEN_WIDTH//2 - 200, 20, "glow")
            
            # Draw current speech text
            if self.current_text:
                text_y = SCREEN_HEIGHT//2 - 50
                self.draw_text_with_effect(f"You said: \"{self.current_text}\"", 
                                         self.font_medium, self.text_color, 
                                         50, text_y, "shadow")
            
            # Draw speech history
            if self.text_history:
                history_y = SCREEN_HEIGHT//2 + 50
                self.draw_text_with_effect("Recent Speech:", self.font_medium, WHITE, 
                                         50, history_y, "shadow")
                
                for i, text in enumerate(list(self.text_history)[-5:]):  # Show last 5
                    color = COLORS[i % len(COLORS)]
                    self.draw_text_with_effect(f"• {text}", self.font_small, color, 
                                             70, history_y + 40 + i * 30, "shadow")
            
            # Draw microphone indicator
            self.draw_microphone_indicator()
            
            # Draw waveform
            self.draw_waveform()
            
            # Draw instructions
            instructions = [
                "Speak into your microphone to see text appear!",
                "Press SPACE to clear current text",
                "Press C to clear history",
                "Press ESC to quit"
            ]
            
            for i, instruction in enumerate(instructions):
                self.draw_text_with_effect(instruction, self.font_small, WHITE, 
                                         50, SCREEN_HEIGHT - 150 + i * 25, "shadow")
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    try:
        game = SpeechToTextGame()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"Error running game: {e}")
        print("Make sure you have a microphone connected and working!")