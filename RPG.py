import pygame
import os


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


class Weapon:
    def __init__(self, name, damage, range):
        self.name, self.damage, self.range = name, damage, range

    def hit(self, actor, target):
        if abs(actor.x - target.x) <= self.range and abs(actor.y - actor.y) <= self.range:
            print('Врагу нанесен урон оружием', self.name, 'в размере', self.damage)
            target.get_damage(self.damage)
        else:
            print('Враг слишком далеко')

    def __str__(self):
        return self.name


class BaseCharacter:
    def __init__(self, pos_x, pos_y, hp):
        self.x, self.y, self.hp = pos_x, pos_y, hp

    def move(self, x, y):
        self.x = x
        self.y = y

    def is_alive(self):
        if self.hp > 0:
            return True
        else:
            return False

    def get_damage(self, ammount):
        self.hp -= ammount

    def get_coords(self):
        return self.x, self.y


class BaseEnemy(BaseCharacter):
    def __init__(self, pos_x, pos_y, weapon, hp):
        self.x, self.y, self.weapon, self.hp = pos_x, pos_y, weapon, hp
        super().__init__(pos_x, pos_y, hp)

    def __str__(self):
        print('Враг на позиции', (self.x, self.y), 'с оружием', self.weapon)

    def hit(self, target):
        if isinstance(target, MainHero):
            self.weapon.hit(self, target)
        else:
            print('Могу ударить только Главного героя')


class MainHero(BaseCharacter):
    def __init__(self, pos_x, pos_y, name, hp):
        self.x, self.y, self.name, self.hp = pos_x, pos_y, name, hp
        self.weapon = Weapon('Дубинка', 34, 50)
        self.flag = True
        super().__init__(pos_x, pos_y, hp)

    def hit(self, target):
        if isinstance(target, BaseEnemy):
            self.weapon.hit(self, target)
        else:
            print('Могу ударить только Врага')

    def heal(self, ammount):
        if (self.hp + ammount) <= 200:
            self.hp += ammount
        else:
            self.hp = 200
        print('Полечился, теперь здоровья', self.hp)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen.fill((0, 0, 0))
pygame.display.flip()

all_sprites = pygame.sprite.Group()
dwarf = AnimatedSprite(load_image('dwarf_sprite_walk.png', -1), 8, 1, 64, 64)
x, y = 0, 0
dwarf.rect = x, y
all_sprites.add(dwarf)

v = 300
clock = pygame.time.Clock()
current_slide = 0
running = True
moving_x, moving_y = False, False
mult_x, mult_y = 0, 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.scancode == 1:
            running = False
        if pygame.key.get_pressed()[pygame.K_d]:
            moving_x = True
            mult_x = 1
        elif pygame.key.get_pressed()[pygame.K_a]:
            moving_x = True
            mult_x = -1
        else:
            moving_x = False
        if pygame.key.get_pressed()[pygame.K_w]:
            moving_y = True
            mult_y = -1
        elif pygame.key.get_pressed()[pygame.K_s]:
            moving_y = True
            mult_y = 1
        else:
            moving_y = False

    mv = clock.tick() * v / 1000
    screen.fill((0, 0, 0))
    if moving_x:
        x += mv * mult_x
        dwarf.rect = (x, y)
    if moving_y:
        y += mv * mult_y
        dwarf.rect = (x, y)
    all_sprites.draw(screen)
    if current_slide == 19:
        dwarf.update()
        current_slide = 0
    else:
        current_slide += 1
    pygame.display.flip()

pygame.quit()
