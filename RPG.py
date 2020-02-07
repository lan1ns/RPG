import pygame
import os
import time


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows):
        super().__init__(all_sprites)
        self.sheet = sheet
        self.frames = []
        self.cut_sheet(self.sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]

    def cut_sheet(self, sheet, columns, rows):
        one_frame = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (one_frame.w * i, one_frame.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, one_frame.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]

    def change_image(self, sheet, cols, rows):
        self.frames = list()
        self.cut_sheet(sheet, cols, rows)


class Weapon:
    def __init__(self, name, damage, range):
        self.name, self.damage, self.range = name, damage, range

    def hit(self, target):
        if isinstance(target, BaseEnemy):
            print('Врагу нанесен урон оружием {} в размере {}'.format(self.name, self.damage))
        target.get_damage(self.damage)

    def return_range(self):
        return self.range

    def return_damage(self):
        return self.damage


class BaseCharacter(AnimatedSprite):
    def __init__(self, pos_x, pos_y, hp, sheet, columns, rows):
        super().__init__(sheet, columns, rows)
        self.x, self.y, self.hp = pos_x, pos_y, hp

    def move(self, x, y):
        self.x = x
        self.y = y
        self.rect = x, y

    def is_alive(self):
        if self.hp > 0:
            return True
        else:
            return False

    def get_damage(self, ammount):
        self.hp -= ammount

    def get_coords(self):
        return [self.x, self.y]

    def return_hp(self):
        return self.hp


class BaseEnemy(BaseCharacter):
    def __init__(self, pos_x, pos_y, weapon, hp, sheet, columns, rows):
        self.x, self.y, self.weapon, self.hp = pos_x, pos_y, weapon, hp
        self.attacking, self.allow_to_attack, self.new_call_to_atack = False, True, False
        self.l_mult_x, self.l_mult_y = 1, 1
        self.first_attack = True
        self.hit_count = 0
        super().__init__(pos_x, pos_y, hp, sheet, columns, rows)

    def hit(self, target):
        if isinstance(target, MainHero) and self.allow_to_attack:
            self.weapon.hit(self, target)
        else:
            print('Могу ударить только Главного героя')

    def return_mult(self):
        dw_x, dw_y = map(int, dwarf.get_coords())
        x, y = map(int, self.get_coords())
        if dw_x > x:
            if dw_y > y:
                return 1, 1
            elif dw_y < y:
                return 1, -1
        elif dw_y > y:
            return -1, 1
        elif dw_y < y:
            return -1, -1

    def hit_count_increase(self):
        self.hit_count = (self.hit_count + 1) % 5
        return self.hit_count

    def after_attack(self):
        if not self.new_call_to_atack:
            self.new_call_to_atack = True
            self.time_after_attack = time.time()
            self.allow_to_attack = False
        if time.time() - self.time_after_attack > 1.1:
            self.new_call_to_atack = False
            self.allow_to_attack = True
        self.attacking = False

    def check_direction(self):
        try:
            m_x, m_y = self.return_mult()
        except TypeError:
            m_x, m_y = self.l_mult_x, self.l_mult_y
        self.changed = False
        if self.l_mult_x != m_x:
            self.changed = True
            self.l_mult_x = m_x
            self.l_mult_y = m_y
            if m_x == 1:
                return '+x'
            else:
                return '-x'
        if self.l_mult_y != m_y and not self.changed:
            self.l_mult_x = m_x
            self.l_mult_y = m_y
            if m_y == 1:
                return '+y'
            else:
                return '-y'
        if self.l_mult_x == 1:
            return '+x'
        else:
            return '-x'


class Skeleton(BaseEnemy):
    def __init__(self, pos_x, pos_y, hp, sheet, columns, rows):
        self.x, self.y, self.hp = pos_x, pos_y, hp
        self.l_mult_x, self.l_mult_y = 1, 1
        self.weapon = Weapon('Взрыв', 30, 30)
        self.exploding, self.dead = False, False
        self.dead_count = 0
        super().__init__(pos_x, pos_y, self.weapon, hp, sheet, columns, rows)

    def move(self, x, y):
        if not self.exploding:
            self.change_image(load_image('demon_skeleton{}.png'.format(self.check_direction()), -1),
                              3, 1)
            self.x, self.y = x, y
            self.rect = x, y

    def before_hit(self):
        self.exploding = True
        self.attacking = True
        self.death_time = time.time()

    def return_size(self):
        return 48, 64

    def hit(self, target):
        if isinstance(target, MainHero):
            self.hp = 0
            self.on_death()
            self.weapon.hit(target)

    def on_death(self):
        self.change_image(load_image('explosion.png', -1), 1, 1)


class Boss(BaseEnemy):
    def __init__(self, pos_x, pos_y, hp, sheet, columns, rows):
        self.x, self.y, self.hp = pos_x, pos_y, hp
        self.dead = False
        super().__init__(pos_x, pos_y, self.weapon, hp, sheet, columns, rows)

    def return_size(self):
        return 320, 320


class Imp(Boss):
    def __init__(self, pos_x, pos_y, hp, sheet, columns, rows):
        self.x, self.y, self.hp = pos_x, pos_y, hp
        self.weapon = Weapon('Вилы', 50, 50)
        self.l_mult_x, self.l_mult_y = 1, 1
        self.changed = False
        super().__init__(pos_x, pos_y, hp, sheet, columns, rows)

    def hit(self, target):
        if isinstance(target, MainHero) and (self.allow_to_attack or self.first_attack):
            self.first_attack = False
            self.heal(int(self.weapon.return_damage() * 0.5))
            self.weapon.hit(target)

    def heal(self, ammount):
        if (self.hp + ammount) <= 300:
            self.hp += ammount
        else:
            self.hp = 300

    def move(self, x, y):
        self.change_image(
            load_image('walk_pitchfork_shield{}.png'.format(self.check_direction()), -1),
            4, 1)
        self.x, self.y = x, y
        self.rect = x, y

    def before_hit(self):
        if not self.attacking:
            self.change_image(
                load_image('attack_pitchfork_shield{}.png'.format(self.check_direction()), -1), 4,
                1)
        self.attacking = True


class MainHero(BaseCharacter):
    def __init__(self, pos_x, pos_y, name, hp, sheet, columns, rows):
        self.x, self.y, self.name, self.hp = pos_x, pos_y, name, hp
        self.weapon_rmb = Weapon('Топор', 30, 100)
        self.weapon_f = Weapon('Топор', 80, 50)
        self.heal_count = 3
        self.dead = False
        super().__init__(pos_x, pos_y, hp, sheet, columns, rows)

    def rmb_hit(self, target):
        self.weapon_rmb.hit(target)

    def f_hit(self, target):
        self.weapon_f.hit(target)

    def heal(self, ammount):
        if self.heal_count > 0:
            if (self.hp + ammount) <= 200:
                self.hp += ammount
            else:
                self.hp = 200
            print('Полечился, теперь здоровья', self.hp, 'осталось', self.heal_count, 'банок')
            self.heal_count -= 1
        else:
            print('Больше нет банок со здоровьем')

    def on_move(self, x):
        if self.x > x:
            self.change_image(load_image('dwarf_sprite_walk-x.png', -1), 8, 1)
        else:
            self.change_image(load_image('dwarf_sprite_walk+x.png', -1), 8, 1)


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


def check_intersection(el, rect):
    ax1, ay1, ax2, ay2 = el[0], el[1], el[2], el[3]
    ax2 = ax1 + ax2
    ay2 = ay1 + ay2

    bx1, by1, bx2, by2 = rect[0], rect[1], rect[2], rect[3]
    bx2 = bx1 + bx2
    by2 = by1 + by2

    s1 = (ax1 >= bx1 and ax1 <= bx2) or (ax2 >= bx1 and ax2 <= bx2)
    s2 = (ay1 >= by1 and ay1 <= by2) or (ay2 >= by1 and ay2 <= by2)
    s3 = (bx1 >= ax1 and bx1 <= ax2) or (bx2 >= ax1 and bx2 <= ax2)
    s4 = (by1 >= ay1 and by1 <= ay2) or (by2 >= ay1 and by2 <= ay2)

    return ((s1 and s2) or (s3 and s4)) or ((s1 and s4) or (s3 and s2))


def draw_text(screen, intro_text, color):
    screen.fill((0, 0, 0))
    font = pygame.font.Font(None, 30)
    y = 10
    for line in intro_text:
        string_rendered = font.render(line, 1, color)
        y += 40
        screen.blit(string_rendered, (10, y))


def terminate():
    pygame.quit()
    exit()


def start_screen_activate():
    start_screen = pygame.display.set_mode((700, 500))
    start_screen.fill((0, 0, 0))

    play = pygame.sprite.Sprite()
    play.image = load_image('button_play.png', -1)
    play.rect = 200, 0

    rules = pygame.sprite.Sprite()
    rules.image = load_image('button_rules.png', -1)
    rules.rect = 200, 200

    start_screen_sprites = pygame.sprite.Group()
    start_screen_sprites.add(play, rules)

    start_screen_running = True
    while start_screen_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.scancode == 1):
                terminate()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 200 < event.pos[0] < 500 and 50 < event.pos[1] < 150:
                    game()

                if 200 < event.pos[0] < 500 and 250 < event.pos[1] < 350:
                    rules_screen = pygame.display.set_mode((720, 750))
                    rules_screen.fill((0, 0, 0))

                    rules_running = True
                    while rules_running:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT or (
                                    event.type == pygame.KEYDOWN and event.scancode == 1):
                                rules_running = False

                        rules_screen.fill((0, 0, 0))
                        draw_text(rules_screen, ['Правила игры:', '', 'Чтобы выйти нажмите Esc', '',
                                                 'В игре 4 волны, на первых появляются скелеты',
                                                 'На финальной волне появляется босс.', '',
                                                 'Скелеты идут к тебе и, когда подойдут,'
                                                 'взорувутся,'
                                                 'Нанося 30 урона,', 'если вы стоите рядом с ними',
                                                 '',
                                                 'Босс атакует вас раз в секунду и наносит 50'
                                                 'урона,',
                                                 'при этом лечась на 25.', '',
                                                 'Главный герой имеет 2 атаки на ПКМ и F, также он'
                                                 ' имеет 3 банки',
                                                 'здоровья, которые восстанавливают'
                                                 ' 75 здоровья.(всего 200)',
                                                 'атака на F наносит 80 урона, на ПКМ наносит'
                                                 ' 30 ед '
                                                 'урона, но', 'по области вокруг вас и быстрее'],
                                  pygame.Color('green'))
                        pygame.display.flip()

        start_screen.fill((0, 0, 0))
        start_screen_sprites.draw(start_screen)
        pygame.display.flip()


def game():
    screen = pygame.display.set_mode((1920, 1080),
                                     pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    screen.fill((0, 0, 0))
    pygame.display.flip()
    global all_sprites, dwarf
    all_sprites = pygame.sprite.Group()

    for x in range(0, 1920, 43):
        for y in range(200, 600, 43):
            tile = pygame.sprite.Sprite()
            tile.image = load_image('tile.png')
            tile.rect = x, y
            all_sprites.add(tile)

    dwarf = MainHero(600, 300, 'dwarf', 200, load_image('dwarf_sprite_idle+x.png', -1), 5, 1)
    dwarf.rect = dwarf.get_coords()
    dwarf_x, dwarf_y = dwarf.get_coords()
    characters = [dwarf]

    f_ability = pygame.sprite.Sprite()
    f_ability.image = load_image('hammer-drop.png')
    f_ability.rect = 1536, 952

    h_ability = pygame.sprite.Sprite()
    h_ability.image = load_image('health-potion.png')
    h_ability.rect = 1664, 952

    rmb_ability = pygame.sprite.Sprite()
    rmb_ability.image = load_image('wide-arrow-dunk.png')
    rmb_ability.rect = 1792, 952

    enemies = []
    all_sprites.add(dwarf, f_ability, h_ability, rmb_ability)

    clock = pygame.time.Clock()
    current_slide, needed_slides = 0, 20
    running = True
    moving_x, moving_y = False, False
    mult_x, mult_y = 1, 1
    after_moving = False
    rmb_attacking, f_attacking = False, False
    boss_fight = False
    level = 0
    allow_to_spawn = [True, True, True, True]
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.scancode == 1:
                terminate()

            if pygame.key.get_pressed()[pygame.K_d]:
                rmb_attacking, rmb_count = False, 0
                f_attacking, f_count = False, 0
                needed_slides = 20
                dwarf.on_move(dwarf_x + 1)
                moving_x = True
                mult_x = 1
            elif pygame.key.get_pressed()[pygame.K_a]:
                rmb_attacking, rmb_count = False, 0
                f_attacking, f_count = False, 0
                needed_slides = 20
                dwarf.on_move(dwarf_x - 1)
                moving_x = True
                mult_x = -1
            else:
                moving_x = False
            if pygame.key.get_pressed()[pygame.K_w]:
                rmb_attacking, rmb_count = False, 0
                f_attacking, f_count = False, 0
                needed_slides = 20
                moving_y = True
                mult_y = -1
            elif pygame.key.get_pressed()[pygame.K_s]:
                rmb_attacking, rmb_count = False, 0
                f_attacking, f_count = False, 0
                needed_slides = 20
                moving_y = True
                mult_y = 1
            else:
                moving_y = False

            if event.type == pygame.KEYDOWN and event.unicode == 'f':
                current_slide, needed_slides = 0, 10
                f_attacking, f_count = True, 0
                rmb_attacking, rmb_count = False, 0
                if mult_x == 1:
                    dwarf.change_image(load_image('dwarf_sprite_f_attack+x.png', -1), 7, 1)
                else:
                    dwarf.change_image(load_image('dwarf_sprite_f_attack-x.png', -1), 7, 1)

            if event.type == pygame.KEYDOWN and event.unicode == 'h':
                dwarf.heal(75)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                current_slide, needed_slides = 0, 5
                rmb_attacking, rmb_count = True, 0
                f_attacking, f_count = False, 0
                if mult_x == 1:
                    dwarf.change_image(load_image('dwarf_sprite_rmb_attack+x.png', -1), 2, 1)
                else:
                    dwarf.change_image(load_image('dwarf_sprite_rmb_attack-x.png', -1), 2, 1)

        mv = clock.tick() / 1000
        screen.fill((0, 0, 0))

        if not dwarf.is_alive():
            if not dwarf.dead:
                dwarf.dead = True
                death_time = time.time()
                for el in all_sprites:
                    all_sprites.remove(el)
                death_screen = pygame.sprite.Sprite()
                death_screen.image = load_image('hero_died.png')
                death_screen.rect = 0, 0
                all_sprites.add(death_screen)
            all_sprites.draw(screen)
            pygame.display.flip()
            if time.time() - death_time > 3:
                start_screen_activate()
            continue

        if moving_x:
            if level != 4:
                if dwarf_x + int(mv * 300 * mult_x) > 1920:
                    level += 1
                    dwarf_x = 0
                    dwarf.move(dwarf_x, dwarf_y)
                if 0 < dwarf_x + int(mv * 300 * mult_x):
                    dwarf_x += int(mv * 300 * mult_x)
                    dwarf.move(dwarf_x, dwarf_y)
            else:
                if 0 < dwarf_x + int(mv * 300 * mult_x) < 1760:
                    dwarf_x += int(mv * 300 * mult_x)
                    dwarf.move(dwarf_x, dwarf_y)
            after_moving = True
        if moving_y:
            if 200 < dwarf_y + int(mv * 250 * mult_y) < 440:
                dwarf_y += int(mv * 250 * mult_y)
                dwarf.move(dwarf_x, dwarf_y)
            after_moving = True
        if not moving_x and not moving_y and after_moving:
            after_moving = False
            if mult_x == 1:
                dwarf.change_image(load_image('dwarf_sprite_idle+x.png', -1), 5, 1)
            if mult_x == -1:
                dwarf.change_image(load_image('dwarf_sprite_idle-x.png', -1), 5, 1)

        for enemy in enemies:
            x, y = enemy.get_coords()
            enemy_size = enemy.return_size()
            enemy_weapon_range = enemy.weapon.return_range()
            if not check_intersection((dwarf_x, dwarf_y, 160, 160), (
                    x, y, enemy_size[0] + enemy_weapon_range, enemy_size[1] + enemy_weapon_range)):
                if isinstance(enemy, Skeleton) and enemy.attacking:
                    if int(time.time() - enemy.death_time) > 1:
                        enemy.dead = True
                enemy.hit_count = 0
                if dwarf_x >= x:
                    if dwarf_y > y:
                        m_x, m_y = 1, 1
                    else:
                        m_x, m_y = 1, -1
                elif dwarf_y > y:
                    m_x, m_y = -1, 1
                else:
                    m_x, m_y = -1, -1
                x1, y1 = x + mv * 100 * m_x, y + mv * 100 * m_y
                enemy.move(x1, y1)
            else:
                enemy.before_hit()

        if current_slide == needed_slides:
            for char in characters:
                char.update()
                if not char.is_alive():
                    if isinstance(char, Skeleton) and not char.dead_count:
                        char.dead_count = 1
                    else:
                        characters.remove(char)
                        enemies.remove(char)
                        all_sprites.remove(char)
                if isinstance(char, Boss):
                    boss_fight = True
                if isinstance(char, BaseEnemy) and char.attacking:
                    x, y = char.get_coords()
                    enemy_size = char.return_size()
                    if isinstance(char, Skeleton) and char.dead:
                        if check_intersection((dwarf_x, dwarf_y, 175, 175),
                                              (x, y, enemy_size[0], enemy_size[1])):
                            char.hit(dwarf)
                            continue
                        else:
                            char.on_death()
                            char.hp = 0
                            continue
                    if char.hit_count == 4:
                        char.hit_count_increase()
                        char.after_attack()
                        if check_intersection((dwarf_x, dwarf_y, 160, 160),
                                              (x, y, enemy_size[0] + char.weapon.return_range(),
                                               enemy_size[1] + char.weapon.return_range())):
                            char.hit(dwarf)
                    else:
                        char.hit_count_increase()
            current_slide = 0
            if rmb_attacking:
                if rmb_count == 3:
                    needed_slides = 20
                    rmb_attacking = False
                    for enemy in enemies:
                        x, y = enemy.get_coords()
                        enemy_size = enemy.return_size()
                        if check_intersection((dwarf_x, dwarf_y, 185, 185),
                                              (x, y, enemy_size[0], enemy_size[1])):
                            dwarf.rmb_hit(enemy)
                    if mult_x == 1:
                        dwarf.change_image(load_image('dwarf_sprite_idle+x.png', -1), 5, 1)
                    if mult_x == -1:
                        dwarf.change_image(load_image('dwarf_sprite_idle-x.png', -1), 5, 1)
                else:
                    rmb_count += 1
            if f_attacking:
                if f_count == 6:
                    needed_slides = 20
                    f_attacking = False
                    for enemy in enemies:
                        x, y = enemy.get_coords()
                        enemy_size = enemy.return_size()
                        if check_intersection((dwarf_x, dwarf_y, 175, 175),
                                              (x, y, enemy_size[0], enemy_size[1])):
                            dwarf.f_hit(enemy)
                    if mult_x == 1:
                        dwarf.change_image(load_image('dwarf_sprite_idle+x.png', -1), 5, 1)
                    if mult_x == -1:
                        dwarf.change_image(load_image('dwarf_sprite_idle-x.png', -1), 5, 1)
                else:
                    f_count += 1
        else:
            current_slide += 1

        all_sprites.draw(screen)

        if boss_fight:
            if imp.is_alive():
                length = 600 * (imp.return_hp() / 300)
                pygame.draw.rect(screen, pygame.Color('white'), (545, 0, 610, 40), 5)
                pygame.draw.rect(screen, pygame.Color('red'), (550, 5, length, 30))
        if dwarf in all_sprites:
            length = 600 * (dwarf.return_hp() / 200)
            pygame.draw.rect(screen, pygame.Color('white'), (545, 1011, 610, 40), 5)
            pygame.draw.rect(screen, pygame.Color('red'), (550, 1016, length, 30))

        pygame.display.flip()

        if level > 0 and allow_to_spawn[level - 1]:
            if level == 4:
                imp = Imp(1700, 300, 300, load_image('walk_pitchfork_shield+y.png', -1), 4, 1)
                imp.rect = imp.get_coords()
                enemies.append(imp)
                characters.append(imp)
                all_sprites.add(imp)
                allow_to_spawn[level - 1] = False
                continue
            allow_to_spawn[level - 1] = False
            y = 200
            for _ in range(level * 2):
                sk = (Skeleton(1700, y, 30, load_image('demon_skeleton+y.png', -1), 3, 1))
                enemies.append(sk)
                all_sprites.add(sk)
                characters.append(sk)
                y += 50

        if level == 4:
            if not imp.is_alive() and not imp.dead:
                if dwarf.is_alive():
                    for el in all_sprites:
                        all_sprites.remove(el)
                    win = pygame.sprite.Sprite()
                    win.image = load_image('win.png', -1)
                    win.rect = 0, 0
                    all_sprites.add(win)
                imp.dead = True


pygame.init()
start_screen_activate()
