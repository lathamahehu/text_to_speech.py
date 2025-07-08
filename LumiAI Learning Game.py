import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🤖 LumiAI Learning Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
SILVER = (192, 192, 192)
PINK = (255, 192, 203)

# Fonts
title_font = pygame.font.Font(None, 48)
big_font = pygame.font.Font(None, 36)
normal_font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 20)

class LumiAI:
    def __init__(self):
        # Lumi's AI brain - these are the rules it follows
        self.rules = {
            'red_ball': 'pick_up_red',
            'blue_ball': 'pick_up_blue',
            'shiny_object': 'ignore_object'
        }
        self.score = 0
        self.rounds_played = 0
        self.last_decision = ""
        self.learning_message = ""
        
        # Visual properties
        self.x = 150
        self.y = 300
        self.size = 60
        self.thinking = False
        self.emotion = "neutral"  # happy, sad, thinking, neutral

    def make_decision(self, scenario_condition):
        """Lumi makes a decision based on its current rules"""
        self.thinking = True
        
        # Check if Lumi has a rule for this situation
        for condition, action in self.rules.items():
            if condition in scenario_condition:
                print(f"🤖 Lumi's brain says: For '{condition}' → do '{action}'")
                self.last_decision = action
                return action
        
        # If no rule exists, make a random guess
        print("🤔 Lumi doesn't know this situation, making a guess...")
        self.last_decision = random.choice(['pick_up_red', 'pick_up_blue', 'ignore_object'])
        return self.last_decision

    def learn_from_feedback(self, scenario_condition, feedback, correct_action=None):
        """Lumi learns from player feedback"""
        self.thinking = False
        
        if feedback == 'correct':
            self.score += 1
            self.emotion = "happy"
            self.learning_message = "Great! I was right! 😊"
            print("✅ Lumi: I got it right!")
            
        elif feedback == 'incorrect' and correct_action:
            self.emotion = "sad"
            self.learning_message = f"Oops! I should '{correct_action}' for '{scenario_condition}'"
            
            # Update or add new rule
            rule_updated = False
            for condition, action in self.rules.items():
                if condition in scenario_condition and action == self.last_decision:
                    print(f"🧠 Updating rule: '{condition}' → '{correct_action}'")
                    self.rules[condition] = correct_action
                    rule_updated = True
                    break
            
            if not rule_updated:
                print(f"🧠 Adding new rule: '{scenario_condition}' → '{correct_action}'")
                self.rules[scenario_condition] = correct_action
        
        self.rounds_played += 1

    def draw(self, screen):
        """Draw Lumi on the screen"""
        # Lumi's body (circle)
        if self.emotion == "happy":
            body_color = GREEN
        elif self.emotion == "sad":
            body_color = RED
        elif self.thinking:
            body_color = YELLOW
        else:
            body_color = BLUE
        
        pygame.draw.circle(screen, body_color, (self.x, self.y), self.size)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), self.size, 3)
        
        # Lumi's eyes
        eye_size = 8
        if self.thinking:
            # Thinking eyes (spirals)
            pygame.draw.circle(screen, BLACK, (self.x - 20, self.y - 15), eye_size)
            pygame.draw.circle(screen, BLACK, (self.x + 20, self.y - 15), eye_size)
        else:
            # Normal eyes
            pygame.draw.circle(screen, BLACK, (self.x - 20, self.y - 15), eye_size)
            pygame.draw.circle(screen, BLACK, (self.x + 20, self.y - 15), eye_size)
        
        # Lumi's mouth
        if self.emotion == "happy":
            # Smile
            pygame.draw.arc(screen, BLACK, (self.x - 20, self.y + 5, 40, 25), 0, 3.14, 3)
        elif self.emotion == "sad":
            # Frown
            pygame.draw.arc(screen, BLACK, (self.x - 20, self.y + 15, 40, 25), 3.14, 6.28, 3)
        else:
            # Neutral mouth
            pygame.draw.line(screen, BLACK, (self.x - 15, self.y + 15), (self.x + 15, self.y + 15), 3)
        
        # Lumi's name tag
        name_text = small_font.render("LUMI", True, WHITE)
        name_rect = name_text.get_rect(center=(self.x, self.y + self.size + 15))
        screen.blit(name_text, name_rect)

class GameObject:
    """Objects that Lumi can interact with"""
    def __init__(self, obj_type, color, shape):
        self.type = obj_type
        self.color = color
        self.shape = shape
        self.x = 500
        self.y = 300
        self.size = 40

    def draw(self, screen):
        """Draw the object"""
        if self.shape == "ball":
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.size)
            pygame.draw.circle(screen, BLACK, (self.x, self.y), self.size, 3)
        elif self.shape == "square":
            pygame.draw.rect(screen, self.color, (self.x - self.size, self.y - self.size, 
                                                self.size * 2, self.size * 2))
            pygame.draw.rect(screen, BLACK, (self.x - self.size, self.y - self.size, 
                                           self.size * 2, self.size * 2), 3)
        elif self.shape == "gem":
            # Draw a diamond shape
            points = [(self.x, self.y - self.size), 
                     (self.x + self.size, self.y),
                     (self.x, self.y + self.size), 
                     (self.x - self.size, self.y)]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, BLACK, points, 3)
        elif self.shape == "coin":
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.size)
            pygame.draw.circle(screen, BLACK, (self.x, self.y), self.size, 3)
            # Add shine effect
            pygame.draw.circle(screen, WHITE, (self.x - 10, self.y - 10), 8)

class GameState:
    def __init__(self):
        self.current_round = 1
        self.max_rounds = 7
        self.current_scenario = None
        self.current_object = None
        self.waiting_for_feedback = False
        self.game_over = False
        self.feedback_buttons = []
        self.scenarios = [
            {
                'description': "Lumi sees a bright red ball",
                'condition': 'red_ball',
                'correct_action': 'pick_up_red',
                'object': GameObject('red_ball', RED, 'ball')
            },
            {
                'description': "Lumi sees a small blue ball", 
                'condition': 'blue_ball',
                'correct_action': 'pick_up_blue',
                'object': GameObject('blue_ball', BLUE, 'ball')
            },
            {
                'description': "Lumi sees a shimmering silver coin",
                'condition': 'shiny_object', 
                'correct_action': 'ignore_object',
                'object': GameObject('shiny_object', SILVER, 'coin')
            },
            {
                'description': "Lumi sees a red square block",
                'condition': 'red_square',
                'correct_action': 'ignore_object', 
                'object': GameObject('red_square', RED, 'square')
            },
            {
                'description': "Lumi sees a tiny blue gem",
                'condition': 'blue_gem',
                'correct_action': 'pick_up_blue',
                'object': GameObject('blue_gem', BLUE, 'gem')
            },
            {
                'description': "Lumi sees a large green sphere", 
                'condition': 'green_sphere',
                'correct_action': 'ignore_object',
                'object': GameObject('green_sphere', GREEN, 'ball')
            }
        ]
        random.shuffle(self.scenarios)

class Button:
    def __init__(self, x, y, width, height, text, color, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.clicked = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        text_surface = normal_font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def draw_lumi_brain(screen, lumi):
    """Draw Lumi's AI brain (rules) on screen"""
    brain_rect = pygame.Rect(50, 450, 400, 200)
    pygame.draw.rect(screen, WHITE, brain_rect)
    pygame.draw.rect(screen, BLACK, brain_rect, 3)
    
    # Title
    title = normal_font.render("🧠 Lumi's AI Brain (Rules)", True, PURPLE)
    screen.blit(title, (brain_rect.x + 10, brain_rect.y + 10))
    
    # Rules
    y_offset = 45
    for condition, action in lumi.rules.items():
        rule_text = small_font.render(f"If '{condition}' → do '{action}'", True, BLACK)
        screen.blit(rule_text, (brain_rect.x + 15, brain_rect.y + y_offset))
        y_offset += 25
        if y_offset > 160:  # Don't overflow the box
            break

def draw_score(screen, lumi, game_state):
    """Draw score and round info"""
    score_rect = pygame.Rect(500, 450, 200, 100)
    pygame.draw.rect(screen, LIGHT_GRAY, score_rect)
    pygame.draw.rect(screen, BLACK, score_rect, 2)
    
    round_text = normal_font.render(f"Round: {game_state.current_round}/{game_state.max_rounds}", True, BLACK)
    screen.blit(round_text, (score_rect.x + 10, score_rect.y + 10))
    
    score_text = normal_font.render(f"Score: {lumi.score}/{lumi.rounds_played}", True, BLACK)
    screen.blit(score_text, (score_rect.x + 10, score_rect.y + 40))
    
    if lumi.rounds_played > 0:
        accuracy = (lumi.score / lumi.rounds_played) * 100
        acc_text = small_font.render(f"Accuracy: {accuracy:.1f}%", True, BLACK)
        screen.blit(acc_text, (score_rect.x + 10, score_rect.y + 70))

def draw_instructions(screen):
    """Draw game instructions"""
    inst_rect = pygame.Rect(720, 450, 250, 200)
    pygame.draw.rect(screen, PINK, inst_rect)
    pygame.draw.rect(screen, BLACK, inst_rect, 2)
    
    title = normal_font.render("How to Play:", True, PURPLE)
    screen.blit(title, (inst_rect.x + 10, inst_rect.y + 10))
    
    instructions = [
        "1. Watch Lumi see objects",
        "2. Lumi decides what to do",
        "3. Tell Lumi if correct/wrong",
        "4. Lumi learns new rules!",
        "",
        "Click buttons to give feedback",
        "Watch Lumi's brain grow!"
    ]
    
    y_offset = 40
    for instruction in instructions:
        if instruction:  # Skip empty lines
            inst_text = small_font.render(instruction, True, BLACK)
            screen.blit(inst_text, (inst_rect.x + 10, inst_rect.y + y_offset))
        y_offset += 20

def main():
    """Main game function"""
    clock = pygame.time.Clock()
    lumi = LumiAI()
    game_state = GameState()
    
    # Create feedback buttons
    correct_button = Button(300, 400, 120, 40, "✅ Correct", GREEN)
    wrong_button = Button(450, 400, 120, 40, "❌ Wrong", RED)
    next_button = Button(600, 400, 120, 40, "Next Round", YELLOW)
    
    # Action choice buttons (for when Lumi is wrong)
    action_buttons = [
        Button(250, 380, 150, 30, "pick_up_red", RED, WHITE),
        Button(420, 380, 150, 30, "pick_up_blue", BLUE, WHITE),
        Button(590, 380, 150, 30, "ignore_object", GRAY, WHITE)
    ]
    
    show_action_buttons = False
    selected_action = None
    
    running = True
    
    # Start first round
    if game_state.scenarios:
        game_state.current_scenario = game_state.scenarios.pop(0)
        game_state.current_object = game_state.current_scenario['object']
        lumi_decision = lumi.make_decision(game_state.current_scenario['condition'])
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if game_state.waiting_for_feedback:
                    # Check feedback buttons
                    if correct_button.is_clicked(mouse_pos):
                        lumi.learn_from_feedback(game_state.current_scenario['condition'], 'correct')
                        game_state.waiting_for_feedback = False
                    
                    elif wrong_button.is_clicked(mouse_pos):
                        show_action_buttons = True
                    
                    # Check action buttons (when Lumi was wrong)
                    if show_action_buttons:
                        for i, button in enumerate(action_buttons):
                            if button.is_clicked(mouse_pos):
                                actions = ['pick_up_red', 'pick_up_blue', 'ignore_object']
                                selected_action = actions[i]
                                lumi.learn_from_feedback(
                                    game_state.current_scenario['condition'], 
                                    'incorrect', 
                                    selected_action
                                )
                                show_action_buttons = False
                                game_state.waiting_for_feedback = False
                
                elif next_button.is_clicked(mouse_pos) and not game_state.waiting_for_feedback:
                    # Start next round
                    if game_state.current_round < game_state.max_rounds and game_state.scenarios:
                        game_state.current_round += 1
                        game_state.current_scenario = game_state.scenarios.pop(0)
                        game_state.current_object = game_state.current_scenario['object']
                        lumi_decision = lumi.make_decision(game_state.current_scenario['condition'])
                        game_state.waiting_for_feedback = True
                        lumi.emotion = "neutral"
                        lumi.learning_message = ""
                    else:
                        game_state.game_over = True
        
        # Clear screen
        screen.fill(WHITE)
        
        # Draw title
        title = title_font.render("🤖 LumiAI Learning Game", True, PURPLE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title, title_rect)
        
        subtitle = normal_font.render("Help Lumi learn to make smart decisions!", True, BLACK)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(subtitle, subtitle_rect)
        
        if not game_state.game_over:
            # Draw current scenario
            if game_state.current_scenario:
                scenario_text = big_font.render(game_state.current_scenario['description'], True, BLACK)
                scenario_rect = scenario_text.get_rect(center=(SCREEN_WIDTH // 2, 130))
                screen.blit(scenario_text, scenario_rect)
                
                # Draw Lumi's decision
                decision_text = normal_font.render(f"Lumi decides: {lumi.last_decision}", True, PURPLE)
                decision_rect = decision_text.get_rect(center=(SCREEN_WIDTH // 2, 170))
                screen.blit(decision_text, decision_rect)
                
                # Draw learning message
                if lumi.learning_message:
                    msg_text = normal_font.render(lumi.learning_message, True, ORANGE)
                    msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
                    screen.blit(msg_text, msg_rect)
            
            # Draw Lumi and object
            lumi.draw(screen)
            if game_state.current_object:
                game_state.current_object.draw(screen)
            
            # Draw feedback buttons
            if game_state.waiting_for_feedback:
                correct_button.draw(screen)
                wrong_button.draw(screen)
                
                feedback_text = normal_font.render("Was Lumi's decision correct?", True, BLACK)
                feedback_rect = feedback_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
                screen.blit(feedback_text, feedback_rect)
                
                # Draw action choice buttons if needed
                if show_action_buttons:
                    choice_text = small_font.render("What should Lumi have done?", True, BLACK)
                    choice_rect = choice_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
                    screen.blit(choice_text, choice_rect)
                    
                    for button in action_buttons:
                        button.draw(screen)
            else:
                next_button.draw(screen)
        
        else:
            # Game over screen
            game_over_text = big_font.render("🎉 Game Complete!", True, GREEN)
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            screen.blit(game_over_text, game_over_rect)
            
            final_score = big_font.render(f"Final Score: {lumi.score}/{lumi.rounds_played}", True, PURPLE)
            score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, 250))
            screen.blit(final_score, score_rect)
            
            if lumi.rounds_played > 0:
                accuracy = (lumi.score / lumi.rounds_played) * 100
                acc_text = normal_font.render(f"Lumi's Learning Accuracy: {accuracy:.1f}%", True, BLACK)
                acc_rect = acc_text.get_rect(center=(SCREEN_WIDTH // 2, 290))
                screen.blit(acc_text, acc_rect)
            
            congrats_text = normal_font.render("You taught Lumi how to think like AI!", True, ORANGE)
            congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, 330))
            screen.blit(congrats_text, congrats_rect)
        
        # Always draw these UI elements
        draw_lumi_brain(screen, lumi)
        draw_score(screen, lumi, game_state)
        draw_instructions(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("🤖 Starting LumiAI Learning Game!")
    print("Help Lumi learn to make smart decisions by giving feedback!")
    main()