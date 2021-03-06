import pygame
import os
import random
import csv
import button

pygame.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Earnesto\'s Crusade')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#define game variables
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 22
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
char_select = 0


#define player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


#load images
#button images
start_img = pygame.image.load('img/buttons/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/buttons/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/buttons/restart_btn.png').convert_alpha()

#background
pine1_img = pygame.image.load('img/background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/background/sky_cloud.png').convert_alpha()

#money img
money_img = pygame.image.load('img/icons/currency.png').convert_alpha()
money_img = pygame.transform.rotate(money_img, -90)

#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'img/tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)

#bullets
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
#grenade
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
#pick up boxes
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
money_box_img = pygame.image.load('img/icons/currency_box.png').convert_alpha()

item_boxes = {
	'Health'	: health_box_img,
	'Ammo'		: ammo_box_img,
	'Grenade'	: grenade_box_img,
  'Money'   : money_box_img
}
#other
choose_img = pygame.image.load('img/buttons/select_btn.png').convert_alpha()
soldier_idle0_img = pygame.image.load('img/player/soldier/idle/0.png').convert_alpha()
elite_idle0_img = pygame.image.load('img/player/elite/idle/0.png').convert_alpha()


#define colours
BG = (100, 101, 220)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

#define font
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y, size):
	img = font.render(text * size, True, text_col)
	screen.blit(img, (x, y))


def draw_bg():
	screen.fill(BG)
	width = sky_img.get_width()
	for x in range(5):
		screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
		screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
		screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
		screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))


#function to reset level
def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	#create empty tile list
	data = []
	for row in range(ROWS):
		r = [-1] * COLS
		data.append(r)

	return data

###################################################################
###################################################################

class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)

		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.currency = 0

		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1

		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
    
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()

		#ai specific variables
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0
		self.coin_dropped = False

    #ANIMATION#
		#load all images for the players
		animation_types = ['idle', 'run', 'jump', 'death']

		for animation in animation_types:
			#reset temporary list of images
			temp_list = []

			#count number of files in the folder
			num_of_frames = len(os.listdir(f'img/{self.char_type}/soldier/{animation}'))

			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/soldier/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()


	def update(self):
		self.update_animation()
		self.check_alive()

		#update cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1


	def move(self, moving_left, moving_right):
		#reset movement variables
		screen_scroll = 0
		dx = 0
		dy = 0

		#assign movement variables if moving left or right
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1

		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1


		#jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True


		#apply gravity
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy += self.vel_y


		#check for collision
		for tile in world.obstacle_list:
			#check collision in the x direction
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0

				#if the ai has hit a wall then make it turn around
				if self.char_type == 'enemy':
					self.direction *= -1
					self.move_counter = 0

			#check for collision in y
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#check if below the ground, i.e. jumping
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top

				#check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom


		#check for collision with water
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health -= 100

		#check for collision with exit
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		#check if fallen off the map
		if self.rect.bottom > SCREEN_HEIGHT:
			self.health = 0

		#check if going off the edges of the screen
		if self.char_type == 'player':
			if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
				dx = 0


		#update rectangle position
		self.rect.x += dx
		self.rect.y += dy


		#update scroll based on player position
		if self.char_type == 'player':
			if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
				or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
				self.rect.x -= dx
				screen_scroll = -dx

		return screen_scroll, level_complete, player.currency



	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)

			#reduce ammo
			self.ammo -= 1


	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and random.randint(1, 200) == 1:
				self.update_action(0)#0: idle
				self.idling = True
				self.idling_counter = 50

			#check if the ai in near the player
			if self.vision.colliderect(player.rect):
				#stop running and face the player
				self.update_action(0)#0: idle
				#shoot
				self.shoot()
      
      #when they can't see the player
			else:
				if self.idling == False:
					if self.direction == 1:
						ai_moving_right = True

					else:
						ai_moving_right = False

					ai_moving_left = not ai_moving_right
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)#1: run
					self.move_counter += 1
					#update ai vision as the enemy moves
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter *= -1

				else:
					self.idling_counter -= 1
					if self.idling_counter <= 0:
						self.idling = False

		#scroll
		self.rect.x += screen_scroll


	def update_animation(self):
		#update animation
		ANIMATION_COOLDOWN = 100

		#update image depending on current frame
		self.image = self.animation_list[self.action][self.frame_index]

		#check if enough time has passed since the last update
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1

		#if the animation has run out the reset back to the start
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1

			else:
				self.frame_index = 0



	def update_action(self, new_action):
		#check if the new action is different to the previous one
		if new_action != self.action:
			self.action = new_action
			#update the animation settings
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()



	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)
			if self.char_type == 'enemy' and self.coin_dropped == False:
				#add a coin to coin group 
				coin = Money(money_img, self.rect.x, self.rect.y)
				coin_group.add(coin)
				self.coin_dropped = True


	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])

		#iterate through each value in level data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)

					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)

					elif tile >= 9 and tile <= 10:
						water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
						water_group.add(water)

					elif tile >= 11 and tile <= 14:
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)

					elif tile == 15:#create player
						player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5)
						health_bar = HealthBar(10, 10, player.health, player.health)

					elif tile == 16:#create enemies
						enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20, 0)
						enemy_group.add(enemy)

					elif tile == 17:#create ammo box
						item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)

					elif tile == 18:#create grenade box
						item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)

					elif tile == 19:#create health box
						item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)

					elif tile == 20:#create exit
						exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
						exit_group.add(exit)
          
					elif tile == 21:#create coin box
						item_box = ItemBox('Money', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
						

		return player, health_bar


	def draw(self):
		for tile in self.obstacle_list: #iterate through obstacles in world and update their images and rect x based on scroll
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])

##################################################################
##################################################################

class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)

		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

##################################################################
##################################################################

class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)

		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

##################################################################
##################################################################

class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)

		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

##################################################################
##################################################################

class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)

		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		#scroll
		self.rect.x += screen_scroll

		#check if the player has picked up the box
		if pygame.sprite.collide_rect(self, player):

			#check what kind of box it was
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health

			elif self.item_type == 'Ammo':
				player.ammo += 15

			elif self.item_type == 'Grenade':
				player.grenades += 3
      
			elif self.item_type == 'Money':
				player.currency += 25

			#delete the item box
			self.kill()


##################################################################
##################################################################

class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		#update with new health
		self.health = health

		#calculate health ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

##################################################################

class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)

		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction


	def update(self):
		#move bullet
		self.rect.x += (self.direction * self.speed) + screen_scroll

		#check if bullet has gone off screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()


    #COLLISION#
		#check for collision with level
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#check collision with characters
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()

		for enemy in enemy_group: #check if coll with enemys
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()

##################################################################
##################################################################

class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
    
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction


	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y


		#check for collision with level
		for tile in world.obstacle_list:
			#check coll with walls
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed

			#check for coll in y
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0

				#check if below the ground, i.e. thrown up
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top

				#check if above the ground, i.e. falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom	


		#update grenade position
		self.rect.x += dx + screen_scroll
		self.rect.y += dy

		#countdown timer
		self.timer -= 1


		if self.timer <= 0:
			self.kill()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)

			#do damage to anyone that is nearby
      #PLAYER#{
      #layer 1
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health -= 25
      #layer 2
			if abs(self.rect.centerx - player.rect.centerx) < int(TILE_SIZE * 0.8) and \
				abs(self.rect.centery - player.rect.centery) < int(TILE_SIZE* 0.8):
				player.health -= 50
      #layer 3
			if abs(self.rect.centerx - player.rect.centerx) < int(TILE_SIZE * 0.65)and \
				abs(self.rect.centery - player.rect.centery) < int(TILE_SIZE * 0.65):
				player.health -= 100
      #}

      #ENEMY#{
      #layer 1
			for enemy in enemy_group: #iterate through enemys to see if any are hit
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE:
					enemy.health -= 25

        #layer 2
				if abs(self.rect.centerx - enemy.rect.centerx) < int(TILE_SIZE * 0.8 ) and \
					abs(self.rect.centery - enemy.rect.centery) < int(TILE_SIZE * 0.8):
					enemy.health -= 50

        #layer 3
				if abs(self.rect.centerx - enemy.rect.centerx) < int(TILE_SIZE * 0.65) and \
					abs(self.rect.centery - enemy.rect.centery) < int(TILE_SIZE * 0.65):
					enemy.health -=  100
          #}

##################################################################
##################################################################

class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = [] #blank list for animation frames

		for num in range(1, 6):
			img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)

		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0


	def update(self):
		#scroll
		self.rect.x += screen_scroll

		EXPLOSION_SPEED = 4
		#update explosion amimation
		self.counter += 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			#if the animation is complete then delete the explosion
			if self.frame_index >= len(self.images):
				self.kill()

			else:
				self.image = self.images[self.frame_index]

##################################################################
##################################################################
class Money(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)

		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		self.rect.x += screen_scroll
		for coin in coin_group:
			if pygame.sprite.spritecollide(player, coin_group, False):
				player.currency += 1
				self.kill()
				money.clear()

##################################################################
class AnimatedPreview(pygame.sprite.Sprite):
	def __init__(self, x, y, char_type, scale):
		pygame.sprite.Sprite.__init__(self)

		self.frame_index = 0
		self.char_type = char_type
		self.idle_animation_list = []
		self.update_counter = 0

		#load images
		if char_type == 'soldier':
			num_of_frames = len(os.listdir(f'img/player/{self.char_type}/idle'))
			temp_list = []
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/player/{self.char_type}/idle/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.idle_animation_list.append(temp_list)
			
		elif char_type == 'elite':
			num_of_frames = len(os.listdir(f'img/player/{self.char_type}/idle'))
			temp_list = []
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/player/{self.char_type}/idle/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.idle_animation_list.append(temp_list)

		self.image = self.idle_animation_list[0][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

    #add basic animation: iterate through the idle list and make self.image = self.idle_animation_list[0]the first temp list at[self.frame_index]
		def update(self):
			self.animation_cooldown = 4

			if self.update_counter >= self.animation_cooldown:
				self.update_counter = 0
				self.frame_index += 1
				if self.frame_index >= len(os.listdir(f'img/player/{self.char_type}/idle')):
					self.frame_index = 0

			else:
				self.animation_counter += 1
				self.frame_index += 1

			self.image = self.idle_animation_list[0][self.frame_index]


#<END CLASSES>#

#create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#char select buttons
elite_button = button.Button(SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT // 2 + 150, choose_img, 1)
soldier_button = button.Button(SCREEN_WIDTH // 2 - 375, SCREEN_HEIGHT // 2 + 150, choose_img, 1)

#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()

explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()

water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()

#money list saves through levels
money = []

#define previews
soldier_preview = AnimatedPreview(SCREEN_WIDTH // 2 - 300, SCREEN_WIDTH - 650, 'soldier', 8)
elite_preview = AnimatedPreview(SCREEN_WIDTH // 2 + 150, SCREEN_WIDTH - 630, 'elite', 7)
#preview group
preview_group = pygame.sprite.Group()

#starting world instance data
#create empty tile list
world_data = []
for row in range(ROWS):
	r = [-1] * COLS
	world_data.append(r)

#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)

world = World()
player, health_bar = world.process_data(world_data)


###GAME LOOP###
run = True
while run:

	clock.tick(FPS)


	#draw menu
	screen.fill(BG)
	#add buttons
	if start_button.draw(screen):
		start_game = True

	if exit_button.draw(screen):
		run = False

	if start_game:
		screen.fill(BG)
    #draw selection buttons: two at this point: soldier + elite
    #add animated previews of the character types above their buttons
		preview_group.add(soldier_preview)
		preview_group.add(elite_preview)

		preview_group.update()
		preview_group.draw(screen)
    
		draw_text("Soldier", font, BLACK, SCREEN_WIDTH // 2 - 300, SCREEN_WIDTH // 2 + 50, 3)
		if soldier_button.draw(screen):
			char_select = 1

		draw_text("Elite", font, BLACK, SCREEN_WIDTH // 2 + 170, SCREEN_WIDTH // 2 + 50, 3)
		if elite_button.draw(screen):
			char_select = 2
		
		if char_select == 1:
			pass
			#default is soldier
		elif char_select == 2:
			#player has chosen elite
			pass


#start the game
	if start_game == True and char_select != 0:
			#update background
			draw_bg()
			#draw world map
			world.draw()

			#show player health
			health_bar.draw(player.health)

			#show ammo
			draw_text('AMMO: ', font, WHITE, 10, 35, 1)
			for x in range(player.ammo):
				screen.blit(bullet_img, (90 + (x * 10), 40))

			#show grenades
			draw_text('GRENADES: ', font, WHITE, 10, 60, 1)
			for x in range(player.grenades):
				screen.blit(grenade_img, (135 + (x * 15), 60))
    
			#show currency
			draw_text(f'MONEY: {player.currency}', font, WHITE, 10, 85, 1)
			if player.currency <=  99:
				screen.blit(money_img, (123, 83))
			elif player.currency >= 100:
				for i in range(2):
					screen.blit(money_img,(135+(7*i), 83))


			#draw player and update based on user input
			player.update()
			player.draw()

			for enemy in enemy_group:#iterate though enemys and update them, draw them, and add ai
				enemy.ai()
				enemy.update()
				enemy.draw()

			#update and draw groups
			bullet_group.update()
			grenade_group.update()
			explosion_group.update()
			item_box_group.update()

			decoration_group.update()
			water_group.update()
			exit_group.update()
			coin_group.update()


			bullet_group.draw(screen)
			grenade_group.draw(screen)
			explosion_group.draw(screen)
			item_box_group.draw(screen)

			decoration_group.draw(screen)
			water_group.draw(screen)
			exit_group.draw(screen)
			coin_group.draw(screen)

			#update player actions
			if player.alive:
				#shoot bullets
				if shoot:
					player.shoot()

				#throw grenades
				elif grenade and grenade_thrown == False and player.grenades > 0:
					grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
				 			player.rect.top, player.direction)
					grenade_group.add(grenade)
					#reduce grenades
					player.grenades -= 1
					grenade_thrown = True


				if player.in_air:
					player.update_action(2)#2: jump

				elif moving_left or moving_right:
					player.update_action(1)#1: run

				else:
					player.update_action(0)#0: idle

				screen_scroll, level_complete, player.currency = player.move(moving_left, moving_right)
				bg_scroll -= screen_scroll


				#check if player has completed the level
				if level_complete:
					level += 1
					bg_scroll = 0
					world_data = reset_level()
					money.append(player.currency)

					if level <= MAX_LEVELS:#stops from loading in nonexistent levels
						#load in level data and create world
						with open(f'level{level}_data.csv', newline='') as csvfile:
							reader = csv.reader(csvfile, delimiter=',')
							for x, row in enumerate(reader):
								for y, tile in enumerate(row):
									world_data[x][y] = int(tile)

						world = World()
						player, health_bar = world.process_data(world_data)
          	#making the payer's money able to survive lvl changes
						player.currency = money[0]
    
    	#if player is dead or in any other state
			else:
				screen_scroll = 0
        #clear coins from screen when you die
				coin_group.empty()

				if restart_button.draw(screen):
					bg_scroll = 0
					world_data = reset_level()

					#load in level data and create world
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')#delimiter is what the program takes as the boundrary of one piece of data from the next
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)

					world = World() #reset world with new data
					player, health_bar = world.process_data(world_data)




  	###################
  	###EVENT HANDLER###
  	###################

	for event in pygame.event.get():
		#quit game
		if event.type == pygame.QUIT:
				run = False

			#keyboard presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
					moving_left = True

			if event.key == pygame.K_d:
					moving_right = True

			if event.key == pygame.K_SPACE:
					shoot = True

			if event.key == pygame.K_q:
					grenade = True

			if event.key == pygame.K_w and player.alive:
					player.jump = True

			if event.key == pygame.K_ESCAPE:
					run = False


			#keyboard button released
    #this makes it so you may do these actions over many presses
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False

			if event.key == pygame.K_d:
				moving_right = False

			if event.key == pygame.K_SPACE:
				shoot = False

			if event.key == pygame.K_q:
				grenade = False
				grenade_thrown = False


	pygame.display.update()

pygame.quit()

#REMINDERS:
#add a shop + upgrades (BIG CHANGES!)

#IN PROGRESS:
#add a health bar for enemies using a group
#add two more fully animated classes: wizard and archer (plus easter egg halo elite w energy sword)

#DONE:
#add currency
#add a way to drop currency from killed enemies
#add grenade layers

#IMPORTANT!!!!
#look at how the buttons were imported. See if i can make every single class the same as that for easier access and less of an annoyingly long block of code
#problems that have arisen:
#classes reference returned or global vars inside and cannot be modified easily
#circular import breaks pygame

#find sprite sheets for archer and wizard

#ELITE:#
#need animations:#
#standby w energy sword, 
#standby w plasma rifle, 
#death, 
#jump, 
#energy sword lunge (add a method in elite class for this action), 
#plasma rifle shoot animation
#plasma rifle overheat animation
#plasma rifle vent animation

#need sounds:#
#energy sword buzz for standby
#energy sword zap for overheat
#energy sword zap for attack
#plasma rifle firing 
#plasma rifle overheat noise
#plasma rifle vent noise

#need features:#
#way to switch weapons (no animation needed)
#cannot pick up weapons or ammo. does not use grenades, and instead has a special weapon called a brute shot that fires 1-6 rounds before having to pick up more ammo
#use the existing ammo crates for brute shot ammo
#does not need ammo,but weapons overheat and have a cooldown period if used too much

#ideas for overheat: 
#PLASMA RIFLE: as long as the firing key is being pressed, a counter increases. when that counter hits a certain point, the action of the plasma rifle is changed to overheat. the player has the option at any point to vent it, triggering a new animation and cooling the weapon down.
#ENERGY SWORD: energy sword will work differently, because it doesn't shoot. Whenever it hits an enemy, a counter is increased, by increments of 25%. when it hits that 100%, overheat is triggered and the weapon must cool down to 0% again to be used. the energy sword cannot be vented,just cooled down.
#maybe have a bar below health that shows how hot the weapon is. use something like the health bar class, but with different colors.