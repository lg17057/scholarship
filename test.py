import pygame
import random

# Initialize Pygame
pygame.init()

# Set up the game window
width, height = 800, 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pong")

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Define game variables
ball_pos = [width // 2, height // 2]
ball_radius = 10
ball_velocity = [0, random.choice([-2, 2])]
paddle_width, paddle_height = 10, 60
player_pos = (height - paddle_height) // 2
opponent_pos = (height - paddle_height) // 2
paddle_velocity = 5
score = [0, 0]

# Update the game state
def update():
    # Update ball position
    ball_pos[0] += ball_velocity[0]
    ball_pos[1] += ball_velocity[1]

    # Collision detection with paddles
    if ball_pos[1] <= player_pos + paddle_height and player_pos <= ball_pos[1] + ball_radius:
        ball_velocity[0] = -ball_velocity[0]
    if ball_pos[1] >= opponent_pos - ball_radius and opponent_pos <= ball_pos[1] + ball_radius:
        ball_velocity[0] = -ball_velocity[0]

    # Collision detection with walls
    if ball_pos[1] <= 0 or ball_pos[1] >= height - ball_radius:
        ball_velocity[1] = -ball_velocity[1]

    # Update paddle positions
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] and player_pos > 0:
        player_pos -= paddle_velocity
    if keys[pygame.K_DOWN] and player_pos < height - paddle_height:
        player_pos += paddle_velocity

    # Update opponent paddle position
    if opponent_pos + paddle_height // 2 < ball_pos[1] and opponent_pos < height - paddle_height:
        opponent_pos += paddle_velocity
    if opponent_pos + paddle_height // 2 > ball_pos[1] and opponent_pos > 0:
        opponent_pos -= paddle_velocity

    # Scoring
    if ball_pos[0] <= 0:
        score[1] += 1
        reset()
    if ball_pos[0] >= width - ball_radius:
        score[0] += 1
        reset()

# Reset the ball position
def reset():
    ball_pos[0] = width // 2
    ball_pos[1] = height // 2
    ball_velocity[0] = 0
    ball_velocity[1] = random.choice([-2, 2])

# Game loop
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update game state
    update()

    # Clear the screen
    screen.fill(BLACK)

    # Draw the ball
    pygame.draw.circle(screen, WHITE, ball_pos, ball_radius)

    # Draw the paddles
    pygame.draw.rect(screen, WHITE, (0, player_pos, paddle_width, paddle_height))
    pygame.draw.rect(screen, WHITE, (width - paddle_width, opponent_pos, paddle_width, paddle_height))

    # Draw the center line
    pygame.draw.line(screen, WHITE, (width // 2, 0), (width // 2, height), 1)

    # Display the score
    font = pygame.font.Font(None, 36)
    text = font.render(str(score[0]) + " : " + str(score[1]), 1, WHITE)
    screen.blit(text, (width // 2 - text.get_width() // 2, 10))

    # Update the display
    pygame.display.flip()

    # Set the frames per second
    clock.tick(60)

# Quit the game
pygame.quit()
