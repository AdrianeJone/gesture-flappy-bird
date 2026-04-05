import pygame
import random
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

pygame.init()
screen = pygame.display.set_mode((400, 600))
pygame.display.set_caption("Gesture Flappy Bird") # Title of the game window
clock = pygame.time.Clock()

# MediaPipe Setup
base_options = mp_python.BaseOptions(model_asset_path='hand_landmarker.task')
options = mp_vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
hand_detector = mp_vision.HandLandmarker.create_from_options(options)
cap = cv2.VideoCapture(1)  # Switch camera if needed

# 2. Game Variables

# Load Game Object Assets
bg_image = pygame.image.load('background.png').convert()
base_image = pygame.image.load('base.png').convert()
bottom_pipe_image = pygame.image.load('pipe.png').convert_alpha()
top_pipe_image = pygame.transform.flip(bottom_pipe_image, False, True)
bird_down = pygame.image.load('bird_down_flap.png').convert_alpha()
bird_mid  = pygame.image.load('bird_mid_flap.png').convert_alpha()
bird_up   = pygame.image.load('bird_up_flap.png').convert_alpha()

# Bird Animation list
bird_frames = [bird_down, bird_mid, bird_up]
bird_index = 0  # Starts at 0 (bird_down)
bird_image = bird_frames[bird_index]

# Bird flap timer event (every 150 milliseconds)
BIRD_FLAP = pygame.USEREVENT + 1
pygame.time.set_timer(BIRD_FLAP, 150)

# Load Sound effects assets
wing_sound = pygame.mixer.Sound('wing.wav')
point_sound = pygame.mixer.Sound('point.wav')
hit_sound = pygame.mixer.Sound('hit.wav')
swoosh_sound = pygame.mixer.Sound('swoosh.wav')

# Bird variables
bird_x = 50                        # It stays on the left side of the screen
bird_y = 300                       # Starts in the middle of the screen
bird_velocity_y = 0                # How fast it is currently falling/rising
gravity = 0.5                      # How strong gravity pulls it down every frame
jump_strength = -8                 # How much velocity is applied when the bird jumps

# Pipe variables
pipe_x = 400                       
pipe_width = 70
pipe_velocity = -4
pipe_gap = 160
pipe_top_height = 250 

# Game state
score = 0
game_active = True
hand_was_open = False
running = True  

# Font
font = pygame.font.SysFont("Courier New", 28, bold=True) 

# 3. Game Loop
     
while running:
    # A. Vision Logic
    hand_is_open = False
    success, frame = cap.read()
    if success:
        frame = cv2.flip(frame, 1)  # Mirror the frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = hand_detector.detect(mp_image)
        
        if results.hand_landmarks:
            hand_landmarks = results.hand_landmarks[0]
            index_up  = hand_landmarks[8].y  < hand_landmarks[6].y
            middle_up = hand_landmarks[12].y < hand_landmarks[10].y
            ring_up   = hand_landmarks[16].y < hand_landmarks[14].y
            
            # Hand is only "Open" if all three are up!
            if index_up and middle_up and ring_up:
                hand_is_open = True
            else:
                hand_is_open = False
                
            h, w, _ = frame.shape
            fingertip_ids = [4, 8, 12, 16, 20]
            
            for tip_id in fingertip_ids:
                tip = hand_landmarks[tip_id]
                cx, cy = int(hand_landmarks[tip_id].x * w), int(hand_landmarks[tip_id].y * h)
                cv2.circle(frame, (cx, cy), 8, (255, 0, 255), cv2.FILLED)
                
                if tip_id == 8:
                    cv2.circle(frame, (cx, cy), 10, (0, 255, 255), 2)
            
        cv2.imshow("Webcam Feed", frame)
        cv2.waitKey(1)
        
    # B. Event handling (Inputs)                              
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Flap animation logic    
        if event.type == BIRD_FLAP:
            bird_index += 1
            if bird_index > 2:
                bird_index = 0
            bird_image = bird_frames[bird_index]
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game_active:         # If spacebar is pressed
            bird_velocity_y = jump_strength                                      # Make the bird jump by setting its velocity upwards
        
    # C. Physics and Logic
    
    if game_active:
        # Hand Flap Logic (State Management)
        if hand_is_open:
            if not hand_was_open:
                bird_velocity_y = jump_strength
                wing_sound.play()
                hand_was_open = True
        else:
            hand_was_open = False
            
        # Bird Physics        
        bird_velocity_y += gravity                                              # Apply gravity to the bird's velocity
        bird_y += bird_velocity_y                                               # Move the bird based on its velocity
        if bird_y >= 550:                                                          
            game_active = False
            hit_sound.play() 
            
        # Pipe Movement and Resetting    
        pipe_x += pipe_velocity
        if pipe_x < -pipe_width:                                                   # If the pipe goes off the left side of the screen
            pipe_x = 400                                                           # Reset it to the right side
            pipe_top_height = random.randint(100, 350)                             # Randomize the height of the top pipe
            score += 1
            point_sound.play()
    
        # Collision Detection
        bird_rect = pygame.Rect(bird_x - 20, int(bird_y) - 20, 40, 40)
        pipe_top_rect = pygame.Rect(pipe_x, 0, pipe_width, pipe_top_height)
        pipe_bottom_rect = pygame.Rect(pipe_x, pipe_top_height + pipe_gap, pipe_width, 600)
        
        if bird_rect.colliderect(pipe_top_rect) or bird_rect.colliderect(pipe_bottom_rect): 
            game_active = False
            hit_sound.play()                                                      
    
    else:
        # Game Over Logic
        # If hand is open, reset game state
        if hand_is_open:
            game_active = True
            swoosh_sound.play() 
            score = 0
            bird_y = 300
            bird_velocity_y = 0
            pipe_x = 400
            
    # D. Drawing
    # 1. Draw Background
    screen.blit(bg_image, (0, 0))
    
    # 2. Draw Pipes
    screen.blit(top_pipe_image, (pipe_x, pipe_top_height - top_pipe_image.get_height()))
    screen.blit(bottom_pipe_image, (pipe_x, pipe_top_height + pipe_gap))
    
    # 3. Draw base
    screen.blit(base_image, (0, 550))
    
    # 4. Draw Bird 
    screen.blit(bird_image, (bird_x - 20, int(bird_y) - 20))

    # 5. UI Text
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (20, 20))

    if not game_active:
        over_text = font.render("Game Over", True, (200, 0, 0))
        retry_text = font.render("Open hand to restart", True, (255, 255, 255))
        screen.blit(over_text, (80, 260))
        screen.blit(retry_text, (50, 300))
        
    pygame.display.update()
    clock.tick(60)

# 4. Quit and Cleanup
cap.release()
cv2.destroyAllWindows()    
pygame.quit()