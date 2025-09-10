import random

import pygame, sys
from pytmx.util_pygame import load_pygame
from random import randint, choice
from pygame.math import Vector2
from os import walk

# 基本数值设置（做好字典方便调用）-------------------------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 64
# 覆盖层位置
OVERLAY_POSITIONS = {
    'tool': (40, SCREEN_HEIGHT - 15),
    'seed': (80, SCREEN_HEIGHT - 15),
    'achievement_btn': (SCREEN_WIDTH - 40, 40)}
# 工具使用方向的向量
PLAYER_TOOL_OFFSET = {
    'left': Vector2(-50, 40),
    'right': Vector2(50, 40),
    'up': Vector2(0, -10),
    'down': Vector2(0, 50)}
# 图层顺序
LAYERS = {
    'ground': 0,
    'soil': 1,
    'soil water': 2,
    'house bottom': 3,
    'ground plant': 4,
    'main': 5,
    'house top': 6,
    'fruit': 7, }
# 作物生长速度
GROW_SPEED = {
    'corn': 1,
    'tomato': 0.7}
# 商店价格
SALE_PRICES = {
    'wood': 4,
    'apple': 2,
    'corn': 10,
    'tomato': 20}
PURCHASE_PRICES = {
    'corn': 4,
    'tomato': 5}


# 覆盖层(静止部分）的显示------------------------------------------------------
class Overlay:
    def __init__(self, player, get_day_func):
        self.display_surface = pygame.display.get_surface()
        self.player = player
        self.get_day = get_day_func  # 新增获取天数的方法
        overlay_path = '../graphics/overlay/'
        self.tools_surf = {tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in
                           player.tools}
        self.seeds_surf = {seed: pygame.image.load(f'{overlay_path}{seed}.png').convert_alpha() for seed in
                           player.seeds}
        self.achievement_btn_surf = pygame.image.load(f'{overlay_path}achievement_btn.png').convert_alpha()
        self.day_font = pygame.font.Font('../font/ChangBanDianSong-12.ttf', 28)  # 新增字体

    def display(self):
        # 显示天数
        day = self.get_day()
        day_surf = self.day_font.render(f'第 {day} 天', True, (38, 101, 189))
        self.display_surface.blit(day_surf, (20, 20))

        # 工具
        tool_surf = self.tools_surf[self.player.selected_tool]
        tool_rect = tool_surf.get_rect(midbottom=OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surf, tool_rect)
        # 种子
        seed_surf = self.seeds_surf[self.player.selected_seed]
        seed_rect = seed_surf.get_rect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seed_surf, seed_rect)
        # 成就按钮
        achievement_btn_rect = self.achievement_btn_surf.get_rect(center=OVERLAY_POSITIONS['achievement_btn'])
        self.display_surface.blit(self.achievement_btn_surf, achievement_btn_rect)


# 从文件夹读出图像，存入二维列表（字典）-------------------------------------------------------
# 导入文件夹，返回文件夹下的文件图像列表
def import_folder(path):
    surface_list = []
    for _, __, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()  # convert_alpha支持透明度处理
            surface_list.append(image_surf)
    return surface_list


# 导入文件夹，返回文件夹下的文件图像字典（文件夹名：文件图像）
def import_folder_dict(path):
    surface_dict = {}
    for _, __, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_dict[image.split('.')[0]] = image_surf
    return surface_dict


# 计时器（动作激活时间长短）-----------------------------------------------------------
class Timer:
    def __init__(self, duration, func=None):
        self.duration = duration
        self.func = func
        self.start_time = 0
        self.active = False

    def activate(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()

    def deactivate(self):
        self.active = False
        self.start_time = 0

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time >= self.duration:
            if self.func and self.start_time != 0:
                self.func()
            self.deactivate()


# 黑夜来临----------------------------------------------------
class Transition:
    def __init__(self, reset, player):
        # 基本导入
        self.display_surface = pygame.display.get_surface()
        self.reset = reset
        self.player = player
        # 屏幕、颜色、速度初始化
        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.color = 255
        self.speed = -2

    # 播放
    def play(self):
        self.color += self.speed
        if self.color <= 0:
            self.speed *= -1
            self.color = 0
            self.reset()
        if self.color > 255:
            self.color = 255
            self.player.sleep = False
            self.speed = -2
        self.image.fill((self.color, self.color, self.color))
        self.display_surface.blit(self.image, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


# 精灵类--------------------------------------------------------------
class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS['main']):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.2, -self.rect.height * 0.75)


class Interaction(Generic):
    def __init__(self, pos, size, groups, name):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.name = name


class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)


class Particle(Generic):
    def __init__(self, pos, surf, groups, z, duration=200):
        super().__init__(pos, surf, groups, z)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        # white surface
        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0, 0, 0))
        self.image = new_surf

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time > self.duration:
            self.kill()


# 玩家设置-------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, interaction, soil_layer, toggle_shop):
        super().__init__(group)

        self.import_assets()
        self.status = 'down_idle'
        self.frame_index = 0

        # 动画导入
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.z = LAYERS['main']

        # 移动方向，当前位置、速度
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200

        # 交互
        self.hitbox = self.rect.copy().inflate((-126, -70))
        self.collision_sprites = collision_sprites

        # 时间间隔
        self.timers = {
            'tool use': Timer(350, self.use_tool),
            'tool switch': Timer(200),
            'seed use': Timer(350, self.use_seed),
            'seed switch': Timer(200),
        }

        # 工具列表
        self.tools = ['hoe', 'water']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]

        # 种子列表
        self.seeds = ['corn', 'tomato']
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]

        # 玩家初始背包
        self.item_inventory = {
            'apple': 20,
            'corn': 20,
            'tomato': 20
        }
        self.seed_inventory = {
            'corn': 5,
            'tomato': 5
        }
        self.money = 200

        # 交互初始化（睡觉、土地、商店）
        self.interaction = interaction
        self.sleep = False
        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop

        # 音频导入
        self.watering = pygame.mixer.Sound('../audio/water.mp3')
        self.watering.set_volume(0.2)

    def use_tool(self):
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)

        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_pos)
            self.watering.play()

    # 获取工具使用目标位置
    def get_target_pos(self):
        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

    # 种地动作
    def use_seed(self):
        if self.seed_inventory[self.selected_seed] > 0:
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed)
            self.seed_inventory[self.selected_seed] -= 1

    def import_assets(self):
        self.animations = {'up': [], 'down': [], 'left': [], 'right': [],
                           'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
                           'right_hoe': [], 'left_hoe': [], 'up_hoe': [], 'down_hoe': [],
                           'right_water': [], 'left_water': [], 'up_water': [], 'down_water': []}

        for animation in self.animations.keys():
            full_path = '../graphics/character/' + animation
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]

    # 键盘输入
    def input(self):
        keys = pygame.key.get_pressed()
        if not self.timers['tool use'].active and not self.sleep:
            # 移动 获得方向向量（y分量）
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0
            # x分量
            if keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            elif keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            else:
                self.direction.x = 0
            # 工具使用
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0
            # 切换工具
            if keys[pygame.K_q] and not self.timers['tool switch'].active:
                self.timers['tool switch'].activate()
                self.tool_index += 1
                self.tool_index = self.tool_index if self.tool_index < len(self.tools) else 0
                self.selected_tool = self.tools[self.tool_index]
            # 种子使用
            if keys[pygame.K_LCTRL]:
                self.timers['seed use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0

            # 切换种子
            if keys[pygame.K_e] and not self.timers['seed switch'].active:
                self.timers['seed switch'].activate()
                self.seed_index += 1
                self.seed_index = self.seed_index if self.seed_index < len(self.seeds) else 0
                self.selected_seed = self.seeds[self.seed_index]
            # 交互（商店、睡觉）
            if keys[pygame.K_RETURN]:
                collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction, False)
                if collided_interaction_sprite:
                    if collided_interaction_sprite[0].name == 'Trader':
                        self.toggle_shop()
                    else:
                        self.status = 'left_idle'
                        self.sleep = True

    # 获取玩家状态
    def get_status(self):
        # 闲置
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'
        # 工具使用
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    # 更新计时器
    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    # 碰撞盒检测
    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0:  # moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0:  # moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        if self.direction.y > 0:  # moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0:  # moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    def move(self, dt):
        # 向量归一化
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()
        # 水平方向移动
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')
        # 垂直方向移动
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)  # 四舍五入
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def update(self, dt):
        self.input()
        self.get_status()
        self.update_timers()
        self.get_target_pos()
        self.move(dt)
        self.animate(dt)


# 耕种系统----------------------------------------------
class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']


class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil water']


class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)

        # setup
        self.plant_type = plant_type
        self.frames = import_folder(f'../graphics/fruit/{plant_type}')
        self.soil = soil
        self.check_watered = check_watered
        self.alive = True

        # plant growing
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        # sprite setup
        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom=soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))


class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):

        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # graphics
        self.soil_surfs = import_folder_dict('../graphics/soil/')
        self.water_surfs = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

        # sounds
        self.hoe_sound = pygame.mixer.Sound('../audio/hoe.wav')
        self.hoe_sound.set_volume(0.1)

        self.plant_sound = pygame.mixer.Sound('../audio/plant.wav')
        self.plant_sound.set_volume(0.2)

    def create_soil_grid(self):
        ground = pygame.image.load('../graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                self.hoe_sound.play()

                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')

                pos = soil_sprite.rect.topleft
                surf = choice(self.water_surfs)
                WaterTile(pos, surf, [self.all_sprites, self.water_sprites])

    def remove_water(self):
        # destroy all water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # clean up the grid
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered

    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                self.plant_sound.play()

                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE

                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite,
                          self.check_watered)

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:

                    # tile options
                    t = 'X' in self.grid[index_row - 1][index_col]
                    b = 'X' in self.grid[index_row + 1][index_col]
                    r = 'X' in row[index_col + 1]
                    l = 'X' in row[index_col - 1]

                    tile_type = 'o'

                    # all sides
                    if all((t, r, b, l)): tile_type = 'x'

                    # horizontal tiles only
                    if l and not any((t, r, b)): tile_type = 'r'
                    if r and not any((t, l, b)): tile_type = 'l'
                    if r and l and not any((t, b)): tile_type = 'lr'

                    # vertical only
                    if t and not any((r, l, b)): tile_type = 'b'
                    if b and not any((r, l, t)): tile_type = 't'
                    if b and t and not any((r, l)): tile_type = 'tb'

                    # corners
                    if l and b and not any((t, r)): tile_type = 'tr'
                    if r and b and not any((t, l)): tile_type = 'tl'
                    if l and t and not any((b, r)): tile_type = 'br'
                    if r and t and not any((b, l)): tile_type = 'bl'

                    # T shapes
                    if all((t, b, r)) and not l: tile_type = 'tbr'
                    if all((t, b, l)) and not r: tile_type = 'tbl'
                    if all((l, r, t)) and not b: tile_type = 'lrb'
                    if all((l, r, b)) and not t: tile_type = 'lrt'

                    SoilTile(
                        pos=(index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites])


# 天空--------------------------------------------------------------
class Sky:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.full_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.start_color = [255, 255, 255]
        self.end_color = (38, 101, 189)

    def display(self, dt):
        for index, value in enumerate(self.end_color):
            if self.start_color[index] > value:
                self.start_color[index] -= 2 * dt

        self.full_surf.fill(self.start_color)
        self.display_surface.blit(self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


# 商店交易-----------------------------------------------------
class Menu:
    def __init__(self, player, toggle_menu):
        self.player = player
        self.toggle_menu = toggle_menu
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('../font/ChangBanDianSong-12.ttf', 30)
        # 选择区块样式
        self.width = 400
        self.space = 10
        self.padding = 8
        # 条目设置
        self.options = list(self.player.item_inventory.keys()) + list(self.player.seed_inventory.keys())
        self.sell_border = len(self.player.item_inventory) - 1
        self.setup()
        # 选择器
        self.index = 0
        self.timer = Timer(200)

    def display_money(self):
        text_surf = self.font.render(f'${self.player.money}', False, 'Black')
        text_rect = text_surf.get_rect(midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20))

        pygame.draw.rect(self.display_surface, 'White', text_rect.inflate(10, 10), 0,
                         4)  # 绘制选择框，文字区域扩大10后的区域，0：填充实心，圆角半径4
        self.display_surface.blit(text_surf, text_rect)

    def setup(self):
        # 计算菜单总高度
        self.text_surfs = []
        self.total_height = 0

        for item in self.options:
            if item == 'corn':
                item = '玉米'
            elif item == 'tomato':
                item = '西红柿'
            elif item == 'apple':
                item = '苹果'
            text_surf = self.font.render(item, False, 'Black')
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)
        self.total_height += (len(self.text_surfs) - 1) * self.space
        self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
        self.main_rect = pygame.Rect(SCREEN_WIDTH / 2 - self.width / 2, self.menu_top, self.width, self.total_height)
        # 购买、出售文字
        self.buy_text = self.font.render('购买', False, 'Blue')
        self.sell_text = self.font.render('出售', False, 'Green')

    # 键盘控制选择、买卖、退出
    def input(self):
        keys = pygame.key.get_pressed()
        self.timer.update()
        if keys[pygame.K_ESCAPE]:
            self.toggle_menu()
        if not self.timer.active:
            if keys[pygame.K_UP]:
                self.index -= 1
                self.timer.activate()
            if keys[pygame.K_DOWN]:
                self.index += 1
                self.timer.activate()
            if keys[pygame.K_SPACE]:
                self.timer.activate()
                # 获取当前物品
                current_item = self.options[self.index]
                # 卖
                if self.index <= self.sell_border:
                    if self.player.item_inventory[current_item] > 0:
                        self.player.item_inventory[current_item] -= 1
                        self.player.money += SALE_PRICES[current_item]
                # 买
                else:
                    seed_price = PURCHASE_PRICES[current_item]
                    if self.player.money >= seed_price:
                        self.player.seed_inventory[current_item] += 1
                        self.player.money -= PURCHASE_PRICES[current_item]
        # 选择器循环
        if self.index < 0:
            self.index = len(self.options) - 1
        if self.index > len(self.options) - 1:
            self.index = 0

    def show_entry(self, text_surf, amount, top, selected):
        # 背景
        bg_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surf.get_height() + (self.padding * 2))
        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)
        # 文本
        text_rect = text_surf.get_rect(midleft=(self.main_rect.left + 20, bg_rect.centery))
        self.display_surface.blit(text_surf, text_rect)
        # 数目
        amount_surf = self.font.render(str(amount), False, 'Black')
        amount_rect = amount_surf.get_rect(midright=(self.main_rect.right - 20, bg_rect.centery))
        self.display_surface.blit(amount_surf, amount_rect)
        # 选择框
        if selected:
            pygame.draw.rect(self.display_surface, 'black', bg_rect, 4, 4)
            if self.index <= self.sell_border:  # sell
                pos_rect = self.sell_text.get_rect(midleft=(self.main_rect.left + 150, bg_rect.centery))
                self.display_surface.blit(self.sell_text, pos_rect)
            else:  # buy
                pos_rect = self.buy_text.get_rect(midleft=(self.main_rect.left + 150, bg_rect.centery))
                self.display_surface.blit(self.buy_text, pos_rect)

    def update(self):
        self.input()
        self.display_money()
        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (text_surf.get_height() + (self.padding * 2) + self.space)
            amount_list = list(self.player.item_inventory.values()) + list(self.player.seed_inventory.values())
            amount = amount_list[text_index]
            self.show_entry(text_surf, amount, top, self.index == text_index)


# 成就系统----------------------------------------------------
class AchievementSystem:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('../font/ChangBanDianSong-12.ttf', 28)
        self.achievements = []
        self.harvest_count = 0
        self.visible = False
        self.button_rect = pygame.Rect(SCREEN_WIDTH - 120, 20, 100, 40)  # 右上角按钮
        # 弹窗
        self.popup_text = None
        self.popup_start_time = 0
        self.popup_duration = 2000  # 弹窗显示2秒

    def add_harvest(self):
        self.harvest_count += 1
        # 收获1次成就
        if self.harvest_count == 1 and "萌芽！" not in self.achievements:
            self.achievements.append("萌芽！")
            self.popup_text = "成就达成：萌芽！"
            self.popup_start_time = pygame.time.get_ticks()
        # 收获20次成就
        if self.harvest_count == 20 and "收获小能手！" not in self.achievements:
            self.achievements.append("收获小能手！")
            self.popup_text = "成就达成：收获小能手！"
            self.popup_start_time = pygame.time.get_ticks()
        # 收获50次成就
        if self.harvest_count == 50 and "大丰收！" not in self.achievements:
            self.achievements.append("大丰收！")
            self.popup_text = "成就达成：大丰收！"
            self.popup_start_time = pygame.time.get_ticks()

    def draw_button(self):
        pygame.draw.rect(self.display_surface, (200, 220, 255), self.button_rect, border_radius=8)
        text = self.font.render("成就", True, (0, 0, 0))
        text_rect = text.get_rect(center=self.button_rect.center)
        self.display_surface.blit(text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                self.visible = not self.visible

    def display(self):
        # 弹窗显示
        if self.popup_text:
            now = pygame.time.get_ticks()
            if now - self.popup_start_time < self.popup_duration:
                popup_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, 40, 360, 60)
                pygame.draw.rect(self.display_surface, (255, 255, 200), popup_rect, border_radius=12)
                popup_font = pygame.font.Font('../font/ChangBanDianSong-12.ttf', 32)
                popup_surf = popup_font.render(self.popup_text, True, (255, 128, 0))
                popup_text_rect = popup_surf.get_rect(center=popup_rect.center)
                self.display_surface.blit(popup_surf, popup_text_rect)
            else:
                self.popup_text = None  # 超时后清除弹窗

        if self.visible:
            bg_rect = pygame.Rect(SCREEN_WIDTH / 2 - 200, SCREEN_HEIGHT / 2 - 150, 400, 300)
            pygame.draw.rect(self.display_surface, (255, 255, 255), bg_rect, border_radius=12)
            title = self.font.render("成就记录", True, (38, 101, 189))
            self.display_surface.blit(title, (bg_rect.x + 120, bg_rect.y + 20))
            for idx, ach in enumerate(self.achievements):
                ach_text = self.font.render(ach, True, (0, 128, 0))
                self.display_surface.blit(ach_text, (bg_rect.x + 40, bg_rect.y + 80 + idx * 40))
            if not self.achievements:
                no_text = self.font.render("暂无成就", True, (128, 128, 128))
                self.display_surface.blit(no_text, (bg_rect.x + 120, bg_rect.y + 120))


# 功能集合----------------------------------------------------
class Level:
    # 初始化
    def __init__(self):
        self.display_surface = pygame.display.get_surface()

        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()

        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
        self.day_count = 1  # 天数变量
        self.setup()
        self.overlay = Overlay(self.player, self.get_day)  # 传入获取天数方法
        self.transition = Transition(self.reset, self.player)
        # 商店
        self.menu = Menu(self.player, self.toggle_shop)
        self.shop_active = False
        # 天空
        self.sky = Sky()
        # 音乐
        self.success = pygame.mixer.Sound('../audio/success.wav')
        self.success.set_volume(0.3)
        self.music = pygame.mixer.Sound('../audio/music.mp3')
        self.music.play(loops=-1)
        self.achievement_system = AchievementSystem()  # 新增成就系统
        # 小游戏相关变量
        self.mini_game_active = False
        self.mini_game_start_time = 0
        self.mini_game_score = 0
        self.mini_game_round = 0
        self.mini_game_icon_pos = None
        self.mini_game_icon_surf = None
        self.mini_game_icon_rect = None
        self.mini_game_result = None
        self.mini_game_icon_visible = False
        self.mini_game_icon_flash_time = 0
        self.mini_game_selected_plant = None

    # 初步设置处理tmx文件
    def setup(self):
        # 导入
        tmx_data = load_pygame('../data/map.tmx')
        # house
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])
        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites)
        # Fence
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])
        # wildflowers
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])
        # collion tiles
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)
        # tmx中的对象层
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(
                    pos=(obj.x, obj.y),
                    group=self.all_sprites,
                    collision_sprites=self.collision_sprites,
                    interaction=self.interaction_sprites,
                    soil_layer=self.soil_layer,
                    toggle_shop=self.toggle_shop)
            if obj.name == 'Bed':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)
            if obj.name == 'Trader':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)

        Generic(
            pos=(0, 0),
            surf=pygame.image.load('../graphics/world/ground.png').convert_alpha(),
            groups=self.all_sprites,
            z=LAYERS['ground'])

    # 玩家物品添加
    def player_add(self, item):
        self.player.item_inventory[item] += 1
        self.success.play()

    # 商店
    def toggle_shop(self):
        self.shop_active = not self.shop_active

    # 重置机制
    def reset(self):
        # plants
        self.soil_layer.update_plants()
        # soil
        self.soil_layer.remove_water()
        # sky
        self.sky.start_color = [255, 255, 255]
        self.day_count += 1  # 天数增加

    def get_day(self):
        return self.day_count

    # 作物收获机制：
    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    self.player_add(plant.plant_type)
                    plant.kill()
                    Particle(plant.rect.topleft, plant.image, self.all_sprites, z=LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')
                    self.achievement_system.add_harvest()  # 收获计数

    # 游戏运行
    def run(self, dt):
        # 游戏暂停逻辑：小游戏期间只显示小游戏界面
        if self.mini_game_active:
            self.display_surface.fill('black')
            self.mini_game_update()
            return

        # 界面绘制
        self.display_surface.fill('black')
        self.all_sprites.custom_draw(self.player)
        # 商店和主页面区别更新
        if self.shop_active:
            self.menu.update()
        else:
            self.all_sprites.update(dt)
            self.plant_collision()
        # 天空
        self.overlay.display()
        self.sky.display(dt)
        # 成就页面
        self.achievement_system.display()
        # 睡觉黑夜转换
        if self.player.sleep:
            self.transition.play()
            #小游戏
            if not self.mini_game_active and not self.mini_game_result:
                self.mini_game_kill_plant()
            # 小游戏结束后才进入新一天
            if self.mini_game_result and not self.mini_game_active:
                self.player.sleep = False
                self.mini_game_result = None
                self.reset()

    # 小游戏入口：启动小游戏
    def mini_game_kill_plant(self):
        alive_plants = [plant for plant in self.soil_layer.plant_sprites.sprites() if plant.alive]
        if not alive_plants:
            return
        self.mini_game_active = True
        self.mini_game_start_time = pygame.time.get_ticks()
        self.mini_game_score = 0
        self.mini_game_round = 0
        self.mini_game_result = None
        self.mini_game_selected_plant = choice(alive_plants)
        self.mini_game_icon_visible = False
        self.mini_game_icon_flash_time = 0
        self.mini_game_icon_surf = pygame.image.load(f'../graphics/fruit/{self.mini_game_selected_plant.plant_type}/0.png').convert_alpha()
        self.mini_game_icon_rect = None
        # 暂停背景音乐
        self.music.stop()
    # 小游戏主循环和绘制
    def mini_game_update(self):
        now = pygame.time.get_ticks()
        elapsed = (now - self.mini_game_start_time) / 1000
        # 游戏结束
        if elapsed > 30 or self.mini_game_round >= 20:
            self.mini_game_active = False
            # 胜利条件
            if self.mini_game_score >= 10:
                self.mini_game_result = 'win'
            else:
                self.mini_game_result = 'lose'
            # 处理结果
            if self.mini_game_result == 'lose':
                # 杀死植物
                self.mini_game_selected_plant.alive = False
                self.mini_game_selected_plant.kill()
                self.soil_layer.grid[self.mini_game_selected_plant.rect.centery // TILE_SIZE][self.mini_game_selected_plant.rect.centerx // TILE_SIZE].remove('P')
            # 恢复背景音乐
            self.music.play(loops=-1)
            return

        # 绘制小游戏界面
        mini_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300)
        pygame.draw.rect(self.display_surface, (255, 255, 220), mini_rect, border_radius=16)
        font = pygame.font.Font('../font/ChangBanDianSong-12.ttf', 32)
        title = font.render('女巫想杀死你的植物！点击作物救回！', True, 'red')
        self.display_surface.blit(title, (SCREEN_WIDTH/4 , 20))
        score_text = font.render(f'分数: {self.mini_game_score}/20', True, (0, 128, 0))
        self.display_surface.blit(score_text, (mini_rect.x + 180, mini_rect.y + 70))
        time_left = max(0, 30 - int(elapsed))
        time_text = font.render(f'剩余时间: {time_left}s', True, (128, 0, 0))
        self.display_surface.blit(time_text, (mini_rect.x + 160, mini_rect.y + 120))
        # 闪现逻辑，每次闪现持续0.7秒，间隔0.3秒
        if not self.mini_game_icon_visible:
            if self.mini_game_round < 20:
                # 生成小游戏框内随机位置
                icon_w, icon_h = self.mini_game_icon_surf.get_size()
                x = random.randint(mini_rect.left + 40, mini_rect.right - 40 - icon_w)
                y = random.randint(mini_rect.top + 60, mini_rect.bottom - 40 - icon_h)
                self.mini_game_icon_rect = self.mini_game_icon_surf.get_rect(topleft=(x, y))
                self.mini_game_icon_visible = True
                self.mini_game_icon_flash_time = now
        else:
            # 图标显示0.9秒
            if now - self.mini_game_icon_flash_time > 900:
                self.mini_game_icon_visible = False
                self.mini_game_round += 1
        # 显示图标
        if self.mini_game_icon_visible and self.mini_game_icon_rect:
            self.display_surface.blit(self.mini_game_icon_surf, self.mini_game_icon_rect)
        # 游戏结束提示
        if not self.mini_game_active and self.mini_game_result:
            result_text = '胜利！植物安全' if self.mini_game_result == 'win' else '失败，植物被杀死！'
            result_surf = font.render(result_text, True, (255, 0, 0) if self.mini_game_result == 'lose' else (0, 128, 0))
            self.display_surface.blit(result_surf, (mini_rect.x + 140, mini_rect.y + 200))


# 相机功能：玩家显示在画面中心-----------------------------------------
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        for layer in LAYERS.values():
            for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)

# 游戏主体--------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('小猫岛')
        self.clock = pygame.time.Clock()
        self.level = Level()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.level.achievement_system.handle_event(event)  # 处理成就按钮点击
            # 小游戏点击判定
                if self.level.mini_game_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.level.mini_game_icon_visible and self.level.mini_game_icon_rect and self.level.mini_game_icon_rect.collidepoint(event.pos):
                        self.level.mini_game_score += 1
                        self.level.mini_game_icon_visible = False
                        self.level.mini_game_round += 1
            dt = self.clock.tick() / 1000
            self.level.run(dt)
            pygame.display.update()
# 运行-----------------------------------------------------------------
if __name__ == '__main__':
    game = Game()
    game.run()

