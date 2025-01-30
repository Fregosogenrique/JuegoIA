import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
GRID_WIDTH = 40
GRID_HEIGHT = 30
SQUARE_SIZE = 20
SCREEN_WIDTH = GRID_WIDTH * SQUARE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * SQUARE_SIZE

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Avatar positions
player_pos = [1, 1]
house_pos = [5, 5]

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Grid Game")

def draw_grid():
   """Draws the grid on the screen."""
   for x in range(0, SCREEN_WIDTH, SQUARE_SIZE):
       for y in range(0, SCREEN_HEIGHT, SQUARE_SIZE):
           rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
           pygame.draw.rect(screen, WHITE, rect, 1)

def draw_avatars():
   """Draws the player and house avatars on the grid."""
   player_rect = pygame.Rect(player_pos[0] * SQUARE_SIZE, player_pos[1] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
   house_rect = pygame.Rect(house_pos[0] * SQUARE_SIZE, house_pos[1] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
   pygame.draw.rect(screen, GREEN, player_rect)
   pygame.draw.rect(screen, RED, house_rect)

def move_player(dx, dy):
   """Moves the player avatar by the specified delta."""
   new_x = player_pos[0] + dx
   new_y = player_pos[1] + dy
   if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
       if [new_x, new_y] != house_pos:  # Ensure player does not move to house position
           player_pos[0] = new_x
           player_pos[1] = new_y

def handle_events():
   #Deteccion de eventos de teclado
   for event in pygame.event.get():
       if event.type == pygame.QUIT:
           pygame.quit()
           sys.exit()
       elif event.type == pygame.KEYDOWN:
           if event.key == pygame.K_UP:
               move_player(0, -1)
           elif event.key == pygame.K_DOWN:
               move_player(0, 1)
           elif event.key == pygame.K_LEFT:
               move_player(-1, 0)
           elif event.key == pygame.K_RIGHT:
               move_player(1, 0)

# Main game loop
while True:
   screen.fill((0, 0, 0))  # Clear the screen
   draw_grid()  # Draw the grid
   draw_avatars()  # Draw the avatars
   handle_events()  # Handle user input
   pygame.display.flip()  # Update the display
   pygame.time.delay(100)  # Delay to control frame rate
## Código en Python para el juego de cuadrícula