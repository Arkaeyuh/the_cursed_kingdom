from config.settings import SCREEN_WIDTH,SCREEN_HEIGHT
import pygame
import os
from entities import Boss

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go one folder up (out of ProjectRoot)
PARENT_DIR = os.path.dirname(BASE_DIR)

# Now construct the path to the assets/images folder
ASSETS_DIR = os.path.join(PARENT_DIR, 'assets')


class Room:
    def __init__(self, room_id, background_image_path=f'/world/test.png', is_boss_room=False) -> None:

        self.room_id = room_id  # Unique identifier for the room
        self.is_boss_room = is_boss_room  # Whether this room contains the boss
        self.enemies = pygame.sprite.Group()  # Group for enemies in the room
        self.doors = []  # List of doors leading to other rooms
        self.powerups = pygame.sprite.Group()  # Group for powerups or items
        self.background_image = pygame.image.load(ASSETS_DIR + background_image_path).convert()
        self.background_image = pygame.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.power_sound = pygame.mixer.Sound('assets/audio/powerup.mp3')
        self.power_sound.set_volume(0.35)


    def add_enemy(self, enemy) -> None:
        self.enemies.add(enemy)

    def add_door(self, door) -> None:
        self.doors.append(door)

    def add_powerup(self, powerup) -> None:
        self.powerups.add(powerup)

    def draw(self, screen) -> None:
        """Draw the room layout, enemies, and items."""

        screen.blit(self.background_image, (0, 0))

        for door in self.doors:
            door.draw(screen)
        
        # Draw all enemies including the boss
        self.enemies.draw(screen)

        # Now loop through enemies and specifically call the draw() method for the Boss
        for enemy in self.enemies:
            if isinstance(enemy, Boss):
                enemy.draw(screen)  # Call the Boss's custom draw method
        
        self.powerups.draw(screen)

    def update(self, delta_time, player) -> None:
        """Update all room objects (enemies, items)."""

        self.enemies.update(delta_time, player)
        self.powerups.update(delta_time)

        for spell in player.spells:
            enemies_hit = pygame.sprite.spritecollide(spell, self.enemies, False)

            if enemies_hit:

                for enemy in enemies_hit:

                    enemy.take_damage(25)  # Adjust damage value as needed

                spell.kill()  # Remove the spell after collision

        for powerup in pygame.sprite.spritecollide(player, self.powerups, True):  # True removes the powerup
            self.power_sound.play()
            powerup.apply(player)  # Apply the effect of the powerup


class Door:
    def __init__(self, x, y, width, height, leads_to) -> None:
        self.rect = pygame.Rect(x, y, width, height)  # Door's position and size
        self.leads_to = leads_to  # The ID of the room this door leads to

    def draw(self, screen) -> None:
        """Draw the door."""
        # pygame.draw.rect(screen, (255, 255, 0), self.rect)  # Yellow door, use this to see where the doors are when we place them and then we choose not to draw

    def check_collision(self, player) -> bool:
        """Check if the player collides with the door."""

        return self.rect.colliderect(player.rect)

class RoomManager:
    def __init__(self) -> None:
        self.current_room = None  # Start in the first room
        self.rooms = {}  # Dictionary of rooms by room_id
        self.transition_cooldown = 0
        self.boss_music_playing = False  # Flag to check if boss music is already playing

    def add_room(self, room):
        self.rooms[room.room_id] = room
        print(f"Room {room.room_id} added")
        print(self.rooms)

    def change_room(self, room_id, player=None, entering_door=None) -> None:
        """Transition to a different room."""

        if room_id in self.rooms:
            print(f"Changing to room: {room_id}")  # Debug message
            self.current_room = self.rooms[room_id]
            if self.current_room.is_boss_room and not self.boss_music_playing:
                pygame.mixer.music.stop()
                pygame.mixer.music.load('assets/audio/boss_music.mp3')
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)  # Loop the music
                self.boss_music_playing = True  # Set the flag

            # Reset flag if leaving boss room
            if not self.current_room.is_boss_room and self.boss_music_playing:
                pygame.mixer.music.stop()
                self.boss_music_playing = False  # Reset the flag


            # Find the door in the new room that leads back to the current room
            for door in self.current_room.doors:

                if door.leads_to == entering_door and player != None:
                    # Place the player outside the door based on door position

                    if door.rect.x == 0:  # Left side of the room
                        player.rect.x = door.rect.x + door.rect.width + 10

                    elif door.rect.right == SCREEN_WIDTH:  # Right side of the room
                        player.rect.x = door.rect.x - player.rect.width - 10

                    elif door.rect.y == 0:  # Top side of the room
                        player.rect.y = door.rect.y + door.rect.height + 10

                    elif door.rect.bottom == SCREEN_HEIGHT:  # Bottom side of the room
                        player.rect.y = door.rect.y - player.rect.height - 10

                    self.transition_cooldown = 1.0  # Set cooldown for 1 second
                    break


        else:
            print(f"Room {room_id} not found!")  # Handle missing room

    def update(self, player, delta_time) -> None:
        """Update the current room and check for transitions."""

        if self.current_room:
            self.current_room.update(delta_time, player)

            # Reduce cooldown over time
            if self.transition_cooldown > 0:
                self.transition_cooldown -= delta_time

            # Only check for door collisions if cooldown is over and boss is defeated (if it's a boss room)
            if self.transition_cooldown <= 0:
                if not self.current_room.is_boss_room or self.is_boss_defeated():
                    # Only allow door transitions if not in a boss room or the boss is defeated
                    for door in self.current_room.doors:
                        if door.check_collision(player):
                            self.change_room(door.leads_to, player, self.current_room.room_id)

    def draw(self, screen) -> None:
        """Draw the current room."""

        if self.current_room:
            self.current_room.draw(screen)

    def is_boss_defeated(self) -> bool:
        """Check if all enemies in the boss room are defeated, particularly the boss."""

        if self.current_room.is_boss_room:
            # Check if any boss enemies are still alive
            for enemy in self.current_room.enemies:
                if isinstance(enemy, Boss):
                    if enemy.alive():
                        return False
        return True
