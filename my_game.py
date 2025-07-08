import pygame
import sys

# --- Configuration Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "My Awesome Pygame Adventure"

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# --- 1. Game Entry Point / Main Application ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_state = None
        self.change_state(MainMenuState(self)) # Start with the Main Menu

        print("Game initialized successfully.")

    def change_state(self, new_state):
        if self.current_state:
            self.current_state.exit() # Clean up current state if it exists
        self.current_state = new_state
        self.current_state.enter() # Initialize new state
        print(f"Changed to state: {type(new_state).__name__}")

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.current_state.handle_event(event) # Delegate event to current state

            # Update
            self.current_state.update(dt)

            # Draw
            self.screen.fill(BLACK) # Clear screen
            self.current_state.draw(self.screen) # Draw current state
            pygame.display.flip() # Update the full display Surface to the screen

        pygame.quit()
        sys.exit()

# --- 2. Game States ---
class GameState:
    """Base class for all game states."""
    def __init__(self, game):
        self.game = game

    def enter(self):
        """Called when entering this state."""
        pass

    def exit(self):
        """Called when exiting this state."""
        pass

    def handle_event(self, event):
        """Handles Pygame events for this state."""
        pass

    def update(self, dt):
        """Updates the state logic (dt is delta time in seconds)."""
        pass

    def draw(self, screen):
        """Draws the state's elements to the screen."""
        pass

class MainMenuState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        print("MainMenuState created.")

    def enter(self):
        print("Entering MainMenuState.")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Simple button detection (replace with proper UI system in a real game)
            start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 50)
            if start_button_rect.collidepoint(mouse_pos):
                self.game.change_state(GameplayState(self.game))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN: # Press Enter to start
                self.game.change_state(GameplayState(self.game))
            elif event.key == pygame.K_ESCAPE: # Press Esc to quit
                self.game.running = False

    def update(self, dt):
        # Menu animations or transitions could go here
        pass

    def draw(self, screen):
        title_surf = self.font.render(TITLE, True, WHITE)
        start_surf = self.small_font.render("Press ENTER or Click to Start", True, GREEN)
        
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        start_rect = start_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        screen.blit(title_surf, title_rect)
        screen.blit(start_surf, start_rect)
        
        # Draw a placeholder button area
        pygame.draw.rect(screen, BLUE, start_rect.inflate(20, 10), 2) # Border

class GameplayState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.debug_font = pygame.font.Font(None, 24)
        print("GameplayState created.")

    def enter(self):
        print("Entering GameplayState.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # Press Esc to pause/return to menu
                self.game.change_state(PauseState(self.game))
            # Player input handled by InputManager or directly in Player class
            # For simplicity, we'll handle directly here for now
            # In a larger game, you'd have an InputManager dispatching
            if event.key == pygame.K_SPACE:
                print("Player fired!") # Example action

    def update(self, dt):
        # Get pressed keys for continuous movement
        keys = pygame.key.get_pressed()
        InputManager.handle_player_movement_keys(self.player, keys, dt)

        self.player.update(dt)
        # Update enemies, world, physics, etc.
        pass

    def draw(self, screen):
        self.player.draw(screen)
        
        # Display FPS for debugging
        fps_text = self.debug_font.render(f"FPS: {int(self.game.clock.get_fps())}", True, WHITE)
        screen.blit(fps_text, (10, 10))

class PauseState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        print("PauseState created.")

    def enter(self):
        print("Entering PauseState.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_p: # Resume with Esc or P
                self.game.change_state(GameplayState(self.game)) # Go back to gameplay
            elif event.key == pygame.K_m: # Return to main menu
                self.game.change_state(MainMenuState(self.game))
            elif event.key == pygame.K_q: # Quit game
                self.game.running = False

    def update(self, dt):
        pass # Nothing updates when paused

    def draw(self, screen):
        # Draw a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150)) # Black with 150 alpha
        screen.blit(overlay, (0, 0))

        pause_surf = self.font.render("PAUSED", True, WHITE)
        resume_surf = self.small_font.render("Press ESC/P to Resume", True, GREEN)
        menu_surf = self.small_font.render("Press M for Main Menu", True, GREEN)
        quit_surf = self.small_font.render("Press Q to Quit", True, RED)

        pause_rect = pause_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        resume_rect = resume_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        menu_rect = menu_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        quit_rect = quit_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))

        screen.blit(pause_surf, pause_rect)
        screen.blit(resume_surf, resume_rect)
        screen.blit(menu_surf, menu_rect)
        screen.blit(quit_surf, quit_rect)


# --- 3. Input Handling ---
class InputManager:
    @staticmethod
    def handle_player_movement_keys(player, keys_pressed, dt):
        dx = 0
        dy = 0
        speed = player.speed * dt # Apply delta time for frame-rate independence

        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            dx -= speed
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            dx += speed
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            dy -= speed
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            dy += speed
            
        player.move(dx, dy)

    # You could add methods for other types of input
    # @staticmethod
    # def handle_mouse_click(event):
    #     if event.type == pygame.MOUSEBUTTONDOWN:
    #         print(f"Mouse clicked at {event.pos}")


# --- 4. A Simple Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 200 # pixels per second
        print("Player created.")

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

        # Keep player within screen bounds
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)

    def update(self, dt):
        # Player-specific logic that runs every frame
        # e.g., animation updates, health regeneration, collision checks (if not managed globally)
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# --- Game Initialization and Run ---
if __name__ == "__main__":
    game = Game()
    game.run()