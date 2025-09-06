import pygame,sys
from pygame.math import Vector2
from os import walk, path
from pytmx.util_pygame import load_pygame
from random import randint,choice

#基本数值设置（做好字典方便调用）-------------------------------------------
# 屏幕
SCREEN_WIDTH=1280
SCREEN_HEIGHT=720
TILE_SIZE=64

# 覆盖层位置
OVERLAY_POSITIONS = {
	'tool' : (40, SCREEN_HEIGHT - 15), 
	'seed': (70, SCREEN_HEIGHT - 5),
    'inventory': (640, SCREEN_HEIGHT - 15)
}
#工具使用方向的向量
PLAYER_TOOL_OFFSET = {
	'left': Vector2(-50,40),
	'right': Vector2(50,40),
	'up': Vector2(0,-10),
	'down': Vector2(0,50)
}
#图层顺序
LAYERS = {
	'water': 0,
	'ground': 1,
	'soil': 2,
	'soil water': 3,
	'rain floor': 4,
	'house bottom': 5,
	'ground plant': 6,
	'main': 7,
	'house top': 8,
	'fruit': 9,
	'rain drops': 10
}
#作物生长速度
GROW_SPEED = {
	'corn': 1,
	'tomato': 0.7
}
#商店价格
SALE_PRICES = {
	'wood': 4,
	'apple': 2,
	'corn': 10,
	'tomato': 20
}
PURCHASE_PRICES = {
	'corn': 4,
	'tomato': 5
}

#覆盖层的显示------------------------------------------------------
class Overlay:
	def __init__(self,player):
		self.display_surface = pygame.display.get_surface()
		self.player = player

		overlay_path = '../graphics/overlay/'
		self.tools_surf = {tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in player.tools}
		self.seeds_surf = {seed: pygame.image.load(f'{overlay_path}{seed}.png').convert_alpha() for seed in player.seeds}

	def display(self):

		# tool
		tool_surf = self.tools_surf[self.player.selected_tool]
		tool_rect = tool_surf.get_rect(midbottom = OVERLAY_POSITIONS['tool'])
		self.display_surface.blit(tool_surf,tool_rect)

		# seeds
		seed_surf = self.seeds_surf[self.player.selected_seed]
		seed_rect = seed_surf.get_rect(midbottom = OVERLAY_POSITIONS['seed'])
		self.display_surface.blit(seed_surf,seed_rect)


#大概是图像处理----------------------------------------------------
class Transition:




#读地图文件返回二维数组用于定位（support）？-------------------------------------------------------
def import_folder(path):
	
def import_folder_dict(path):

'''

#时间系统-----------------------------------------------------------
class Timer:


#各类sprites（小）-----------------------------------------------------
class Generic(pygame.sprite.Sprite):
	
class Interaction(Generic):
	
class Water(Generic):

class WildFlower(Generic):
	
class Particle(Generic):
	
class Tree(Generic):  #不砍树可以不加

#商店功能-------------------------------------------------------






#玩家------------------------------------------------------------
class Player(pygame.sprite.Sprite):




#耕种系统（soil）----------------------------------------------
class SoilTile(pygame.sprite.Sprite):
	
class WaterTile(pygame.sprite.Sprite):
	
class Plant(pygame.sprite.Sprite):
	
class SoilLayer:
	

#商店交易-----------------------------------------------------
class Menu:
	

#天气系统（时间足够再做）----------------------------------------
class Sky:
	
class Rain:
	
'''




#功能集合----------------------------------------------------
class Level:
	#初始化
	def __init__(self):
		self.display_surface = pygame.display.get_surface()

		self.all_sprites = CameraGroup()
		self.collision_sprites = pygame.sprite.Group()
		self.interaction_sprites = pygame.sprite.Group()


		self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
		self.setup()
		self.overlay = Overlay(self.player)
		self.transition = Transition(self.reset, self.player)

		# 商店
		self.menu = Menu(self.player, self.toggle_shop)
		self.shop_active = False

		# 音乐
		self.success = pygame.mixer.Sound('../audio/success.wav')
		self.success.set_volume(0.3)
		self.music = pygame.mixer.Sound('../audio/music.mp3')
		self.music.play(loops = -1)


		

    #开始
	def setup(self):
		#创建地图
		for row_index, row in enumerate(WORLD_MAP):
			for col_index, col in enumerate(row):
				x = col_index * TILE_SIZE
				y = row_index * TILE_SIZE
				if col == '0':
					Tile((x,y), [self.all_sprites, self.collision_sprites], 'invisible')
				if col == '1':
					Player((x,y), [self.all_sprites])



'''	
    #玩家
	def player_add(self,item):

    #商店
	def toggle_shop(self):
		
    #作物生长刷新机制？
	def reset(self):
		
    #作物收获机制：
	def plant_collision(self):
'''
    #游戏运行
	def run(self,dt):
	# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)
		
		# updates
		if self.shop_active:
			self.menu.update()
		else:
			self.all_sprites.update(dt)
			self.plant_collision()
'''
		# weather
		self.overlay.display()
		if self.raining and not self.shop_active:
			self.rain.update()
		self.sky.display(dt)

		# transition overlay
		if self.player.sleep:
			self.transition.play()

'''

#相机功能：玩家显示在画面中心-----------------------------------------
class CameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.offset = pygame.math.Vector2()

	def custom_draw(self, player):
		self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
		self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

        for layer in LAYERS.values():
			for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
				if sprite.z == layer:
					offset_rect = sprite.rect.copy()
					offset_rect.center -= self.offset
					self.display_surface.blit(sprite.image, offset_rect)


#游戏主体--------------------------------------------------------
class Game:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
		pygame.display.set_caption('小猫岛')
		self.clock = pygame.time.Clock()
		self.level = Level()

	def run(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()

			dt = self.clock.tick() / 1000
			self.level.run(dt)
			pygame.display.update()


#运行-----------------------------------------------------------------
if __name__ == '__main__':
	game = Game()
	game.run()