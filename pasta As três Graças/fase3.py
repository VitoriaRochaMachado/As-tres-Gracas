# fase3.py (refatorado com suporte a sprite idle/walk do jogador + música de fundo da fase 3)
import pygame
import sys
import math, random
import os

# ----- CONFIG -----
WIDTH, HEIGHT = 1024, 640
FPS = 60

# cores
BLACK = (0,0,0)
WHITE = (240,240,240)
GERLUCE_COLOR = (200,60,80)
GUARD_COLOR = (30,30,100)
STATUE_COLOR = (210,180,60)
ALARM_COLOR = (220,20,20)
BG_COLOR = (20,20,25)
WALL_COLOR = (25,25,25)
HINT_COLOR = (180,180,255)
DOOR_COLOR = (100,40,20)
MAT_COLOR = (130,30,80)

# Gameplay params
PLAYER_SPEED = 200
GUARD_SPEED = 90
FOV_ANGLE = 60
FOV_DISTANCE = 220
STEAL_TIME = 2.0

# ----- SONS / ASSETS -----
def _load_sounds(base_dir=None):
    alarm_sound = None
    game_over_sound = None
    victory_sound = None
    try:
        if base_dir:
            alarm_path = os.path.join(base_dir, "assets", "alarme.mp3")
            go_path = os.path.join(base_dir, "assets", "game_over_som.mp3")
            vi_path = os.path.join(base_dir, "assets", "vitoria_som.mp3")
        else:
            alarm_path = "assets/alarme.mp3"
            go_path = "assets/game_over_som.mp3"
            vi_path = "assets/vitoria_som.mp3"
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass
        if pygame.mixer.get_init() is not None:
            try:
                if os.path.exists(alarm_path):
                    alarm_sound = pygame.mixer.Sound(alarm_path)
                    alarm_sound.set_volume(0.6)
            except Exception:
                alarm_sound = None
            try:
                # Carrega som de game over (efeito curto)
                if os.path.exists(go_path):
                    game_over_sound = pygame.mixer.Sound(go_path)
                    game_over_sound.set_volume(0.75)
            except Exception:
                game_over_sound = None
            try:
                # Carrega som de vitória (novo, opcional)
                if os.path.exists(vi_path):
                    victory_sound = pygame.mixer.Sound(vi_path)
                    victory_sound.set_volume(0.85)
            except Exception:
                victory_sound = None
    except Exception:
        alarm_sound = None
        game_over_sound = None
        victory_sound = None
    return alarm_sound, game_over_sound, victory_sound

def _load_images(base_dir=None):
    GAME_OVER_BG = None
    VICTORY_BG = None
    PRESA_VIDEO_BG = None
    try:
        if base_dir:
            go_path = os.path.join(base_dir, "assets", "game_over.png")
            vi_path = os.path.join(base_dir, "assets", "vitoria.png")
            pv_path = os.path.join(base_dir, "assets", "Presa_video.png")
        else:
            go_path = "assets/game_over.png"
            vi_path = "assets/vitoria.png"
            pv_path = "assets/Presa_video.png"

        # carregar game over (se existir)
        try:
            if os.path.exists(go_path):
                GAME_OVER_BG = pygame.image.load(go_path).convert()
                GAME_OVER_BG = pygame.transform.scale(GAME_OVER_BG, (WIDTH, HEIGHT))
        except Exception:
            GAME_OVER_BG = None

        # carregar victory (opcional)
        try:
            if os.path.exists(vi_path):
                VICTORY_BG = pygame.image.load(vi_path).convert()
                VICTORY_BG = pygame.transform.scale(VICTORY_BG, (WIDTH, HEIGHT))
        except Exception:
            VICTORY_BG = None

        # carregar presa_video (opcional)
        try:
            if os.path.exists(pv_path):
                PRESA_VIDEO_BG = pygame.image.load(pv_path).convert()
                PRESA_VIDEO_BG = pygame.transform.scale(PRESA_VIDEO_BG, (WIDTH, HEIGHT))
        except Exception:
            PRESA_VIDEO_BG = None

    except Exception:
        GAME_OVER_BG = None
        VICTORY_BG = None
        PRESA_VIDEO_BG = None

    return GAME_OVER_BG, VICTORY_BG, PRESA_VIDEO_BG

def _trim_sprite(surf):
    try:
        mask = pygame.mask.from_surface(surf)
        rects = mask.get_bounding_rects()
        if not rects:
            return surf
        r = rects[0].copy()
        for rr in rects[1:]:
            r.union_ip(rr)
        return surf.subsurface(r).copy()
    except Exception:
        return surf

# ----- ENTITIES -----
class Player:
    def __init__(self, x,y):
        self.rect = pygame.Rect(x, y, 64, 96)
        self.hitbox = self.rect.inflate(-30, -40)
        self.hitbox.midbottom = self.rect.midbottom

        self.speed = PLAYER_SPEED
        self.stealing = False
        self.steal_timer = 0.0
        self.has_statue = False
        self.mask = False

        # --- sprite support 
        self.images_ok = False
        self.idle_image = None
        self.walk_images = []
        self.idle_dir = {}
        self.walk_dir = {}
        self.base_w = 1
        self.base_h = 1
        self.facing = "down"
        self._prev_facing = self.facing
        self.frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.12
        self.moving = False
        self.facing_left = False
        # ----------------------------------------

    def update(self, dt, walls):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1
        if dx != 0 or dy != 0:
            l = math.hypot(dx,dy)
            if l != 0:
                dx /= l; dy /= l

        if dx < 0:
            self.facing_left = True
        elif dx > 0:
            self.facing_left = False

        if dx != 0 or dy != 0:
            if abs(dx) > abs(dy):
                if dx < 0:
                    self.facing = "left"
                elif dx > 0:
                    self.facing = "right"
            else:
                if dy < 0:
                    self.facing = "up"
                elif dy > 0:
                    self.facing = "down"

        # atualiza flag de movimento (usada para animação)
        self.moving = (dx != 0 or dy != 0)

        self.hitbox.x += dx * self.speed * dt
        self._collide(walls, dx, 0)
        self.hitbox.y += dy * self.speed * dt
        self._collide(walls, 0, dy)
        self.rect.midbottom = self.hitbox.midbottom

    def _collide(self, walls, dx, dy):
        for w in walls:
            if self.hitbox.colliderect(w):
                if dx > 0: self.hitbox.right = w.left
                if dx < 0: self.hitbox.left = w.right
                if dy > 0: self.hitbox.bottom = w.top
                if dy < 0: self.hitbox.top = w.bottom

    def draw(self, surf):
        # Se houver sprites, desenha sprite escalado; senão, retângulo (fallback)
        if self.images_ok and (self.idle_image is not None):
            if self.moving:
                frames = self.walk_dir.get(self.facing)
                if frames:
                    sprite = frames[self.frame % len(frames)]
                elif len(self.walk_images) >= 1:
                    sprite = self.walk_images[self.frame]
                else:
                    sprite = self.idle_image
            else:
                sprite = self.idle_dir.get(self.facing, self.idle_image)

            w, h = sprite.get_size()
            scale = min(self.rect.width / self.base_w, self.rect.height / self.base_h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

            try:
                sprite_scaled = pygame.transform.smoothscale(sprite, new_size)
            except Exception:
                sprite_scaled = pygame.transform.scale(sprite, new_size)

            # <<< ADIÇÃO MÍNIMA: flip horizontal quando estiver virado à esquerda >>>
            if self.facing_left and (self.facing not in self.walk_dir) and (self.facing not in self.idle_dir):
                sprite_scaled = pygame.transform.flip(sprite_scaled, True, False)
            # <<< fim da adição >>>

            x = self.rect.centerx - sprite_scaled.get_width() // 2
            y = self.rect.centery - sprite_scaled.get_height() // 2
            surf.blit(sprite_scaled, (x, y))
        else:
            pygame.draw.rect(surf, GERLUCE_COLOR, self.rect)
            if self.mask:
                pygame.draw.rect(surf, (255,255,255), self.rect.inflate(-8,-14), 2)

class Guard:
    def __init__(self, path_points, speed=GUARD_SPEED, pause=0.6):
        self.path = path_points[:]
        self.i = 0
        self.pos = pygame.Vector2(self.path[0])
        self.speed = speed
        self.pause = pause
        self.pause_timer = 0
        self.direction = pygame.Vector2(1,0)
        self.rect = pygame.Rect(self.pos.x-14, self.pos.y-14, 28,28)
        self.alerted = False

    def update(self, dt):
        if self.alerted: return
        target = pygame.Vector2(self.path[(self.i+1)%len(self.path)])
        vec = target - self.pos
        dist = vec.length()
        if dist < 2:
            self.pause_timer += dt
            if self.pause_timer >= self.pause:
                self.pause_timer = 0
                self.i = (self.i + 1) % len(self.path)
        else:
            self.direction = vec.normalize()
            self.pos += self.direction * self.speed * dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))

    def chase(self, player, dt):
        vec = pygame.Vector2(player.rect.center) - self.pos
        if vec.length() > 4:
            self.direction = vec.normalize()
            self.pos += self.direction * (self.speed*1.2) * dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))

    def draw(self, surf):
        pygame.draw.rect(surf, GUARD_COLOR, self.rect)
        start = pygame.Vector2(self.rect.center)
        dir_angle = math.degrees(math.atan2(self.direction.y, self.direction.x))
        left_angle = math.radians(dir_angle - FOV_ANGLE/2)
        right_angle = math.radians(dir_angle + FOV_ANGLE/2)
        p1 = start + pygame.Vector2(math.cos(left_angle), math.sin(left_angle)) * FOV_DISTANCE
        p2 = start + pygame.Vector2(math.cos(right_angle), math.sin(right_angle)) * FOV_DISTANCE
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (50,50,150,30), [start, p1, p2])
        surf.blit(s, (0,0))

    def can_see_player(self, player, walls):
        start = pygame.Vector2(self.rect.center)
        target = pygame.Vector2(player.rect.center)
        vec = target - start
        dist = vec.length()
        if dist > FOV_DISTANCE: return False
        if vec.length() == 0: return True
        dir_angle = math.degrees(math.atan2(self.direction.y, self.direction.x))
        to_player_angle = math.degrees(math.atan2(vec.y, vec.x))
        diff = (to_player_angle - dir_angle + 180) % 360 - 180
        if abs(diff) > FOV_ANGLE/2: return False
        steps = int(dist//8)
        for i in range(1, steps+1):
            p = start + vec*(i/steps)
            r = pygame.Rect(p.x-2,p.y-2,4,4)
            for w in walls:
                if r.colliderect(w): return False
        return True

class Statue:
    def __init__(self, x,y):
        self.rect = pygame.Rect(x,y,34,34)
        self.stolen = False
    def draw(self, surf):
        if not self.stolen:
            pygame.draw.rect(surf, STATUE_COLOR, self.rect)
            pygame.draw.rect(surf, (255,255,255), self.rect.inflate(-10,-10), 2)

# ----- LEVEL SETUP -----
def build_walls(door_closed=True, door_rect=None):
    walls = []
    walls.append(pygame.Rect(0,0,WIDTH,16))
    walls.append(pygame.Rect(0,0,16,HEIGHT))
    walls.append(pygame.Rect(0,HEIGHT-16,WIDTH,16))
    walls.append(pygame.Rect(WIDTH-16,0,16,HEIGHT))

    mansion_x, mansion_y, mansion_w, mansion_h = 200, 120, 600, 200
    top_wall = pygame.Rect(mansion_x, mansion_y, mansion_w, 16)
    left_wall = pygame.Rect(mansion_x, mansion_y, 16, mansion_h)
    right_wall = pygame.Rect(mansion_x+mansion_w-16, mansion_y, 16, mansion_h)
    
    if door_rect is None:
        bottom_wall = pygame.Rect(mansion_x, mansion_y + mansion_h - 16, mansion_w, 16)
        walls += [top_wall, left_wall, bottom_wall, right_wall]
    else:
        door_x, door_w = door_rect.x, door_rect.width
        bottom_y = mansion_y + mansion_h - 16
        if door_x > mansion_x:
            walls.append(pygame.Rect(mansion_x, bottom_y, door_x - mansion_x, 16))
        right_start, end_x = door_x + door_w, mansion_x + mansion_w
        if right_start < end_x:
            walls.append(pygame.Rect(right_start, bottom_y, end_x - right_start, 16))
        walls += [top_wall, left_wall, right_wall]
        if door_closed: walls.append(door_rect)
    
    walls += [pygame.Rect(340,180,120,20), pygame.Rect(520,220,160,20), pygame.Rect(420,360,80,120)]
    return walls

def draw_text(s, txt, x,y, color=WHITE, font=None):
    if font is None:
        font = pygame.font.SysFont("consolas", 20)
    surf = font.render(txt, True, color)
    s.blit(surf, (x,y))

# ----- TELAS DE FIM (reutilizáveis) -----
def show_end_screen_local(screen, clock, font, title, msg, color, bg_image=None, game_over_sound=None):
    """
    Exibe a tela final. Se bg_image for fornecida, usa-a como fundo.
    Retorna True se o jogador pedir para reiniciar (R).
    """
    # tenta tocar som de fim (se fornecido)
    try:
        if game_over_sound:
            game_over_sound.play()
    except Exception:
        pass

    if bg_image:
        screen.blit(bg_image, (0, 0))
    else:
        screen.fill((15, 15, 20))

    t = font.render(title, True, color)
    t2 = font.render(msg, True, WHITE)
    t3 = font.render("Pressione R para Reiniciar ou ESC para Sair", True, HINT_COLOR)

    screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 80))
    screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2 - 30))
    screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT - 90))

    pygame.display.flip()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: return True
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
        clock.tick(15)

# ----- RUN API -----
def run(screen, clock, font, base_dir=None):
    # carregar sons e imagens (uma vez)
    alarm_sound, game_over_sound, victory_sound = _load_sounds(base_dir)
    GAME_OVER_BG, VICTORY_BG, PRESA_VIDEO_BG = _load_images(base_dir)

    # --- MÚSICA DE FUNDO DA FASE 3 (ADIÇÃO MÍNIMA) ---
    try:
        if base_dir:
            fase3_music_path = os.path.join(base_dir, "assets", "fase3_som.mp3")
        else:
            fase3_music_path = "assets/fase3_som.mp3"

        # garante que o mixer esteja inicializado (o _load_sounds já tentará, mas checamos novamente com try)
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        if os.path.exists(fase3_music_path) and pygame.mixer.get_init() is not None:
            try:
                pygame.mixer.music.load(fase3_music_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)  # loop infinito
            except Exception:
                pass
    except Exception:
        pass
    # ----------------------------------------------

    # --- PISO + OVERLAY + TIMER BOX ---
    floor_tile = None
    try:
        if base_dir:
            floor_path = os.path.join(base_dir, "assets", "piso_madeira.png")
        else:
            floor_path = os.path.join("assets", "piso_madeira.png")
        floor_img = pygame.image.load(floor_path).convert()
        floor_tile = pygame.transform.smoothscale(floor_img, (74, 74))
    except Exception:
        floor_tile = None

    floor_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    floor_overlay.fill((0, 0, 0, 100))

    try:
        if base_dir:
            timer_path = os.path.join(base_dir, "assets", "timer_box.png")
        else:
            timer_path = os.path.join("assets", "timer_box.png")
        timer_box_img = pygame.image.load(timer_path).convert_alpha()
    except Exception:
        timer_box_img = None

    # --- CARREGA SPRITES DO JOGADOR (MÍNIMA ALTERAÇÃO) ---
    player_idle = None
    player_walk = []
    images_ok = False
    player_idle_dir = {}
    player_walk_dir = {}
    base_w = 1
    base_h = 1
    try:
        if base_dir:
            player_dir = os.path.join(base_dir, "assets", "player")
        else:
            player_dir = os.path.join("assets", "player")

        idle_path = os.path.join(player_dir, "idle.png")
        if os.path.exists(idle_path):
            player_idle = pygame.image.load(idle_path).convert_alpha()

        idle_files = {
            "down": "idledown.png",
            "up": "idleup.png",
            "left": "idleleft.png",
            "right": "idleright.png",
        }
        for d, fn in idle_files.items():
            p = os.path.join(player_dir, fn)
            if os.path.exists(p):
                player_idle_dir[d] = pygame.image.load(p).convert_alpha()

        for d in ["down","up","left","right"]:
            frames = []
            for i in range(3):
                p = os.path.join(player_dir, f"walk_{i}{d}.png")
                if os.path.exists(p):
                    frames.append(pygame.image.load(p).convert_alpha())
            if frames:
                player_walk_dir[d] = frames

        if player_idle is None:
            player_idle = player_idle_dir.get("down", None)

        # tenta carregar até 8 frames de walk (para ser tolerante)
        for i in range(8):
            p = os.path.join(player_dir, f"walk_{i}.png")
            if os.path.exists(p):
                player_walk.append(pygame.image.load(p).convert_alpha())

        if player_idle is not None:
            if len(player_walk) >= 1 or len(player_walk_dir) >= 1:
                images_ok = True
            else:
                player_walk = [player_idle]
                images_ok = True

        if player_idle is not None:
            player_idle = _trim_sprite(player_idle)

        for k in list(player_idle_dir.keys()):
            player_idle_dir[k] = _trim_sprite(player_idle_dir[k])

        for k in list(player_walk_dir.keys()):
            player_walk_dir[k] = [_trim_sprite(s) for s in player_walk_dir[k]]

        player_walk = [_trim_sprite(s) for s in player_walk]

        all_sprites = []
        if player_idle is not None:
            all_sprites.append(player_idle)
        all_sprites += list(player_idle_dir.values())
        for frames in player_walk_dir.values():
            all_sprites += list(frames)
        all_sprites += player_walk

        if all_sprites:
            base_w = max(s.get_width() for s in all_sprites)
            base_h = max(s.get_height() for s in all_sprites)

    except Exception:
        images_ok = False
    # --------------------------------------------------------------------

    # inicialização local de entidades / estado
    door_w, door_h = 120, 16
    door_x, door_y = 200 + (600 - door_w) // 2, 120 + 200 - 16
    door_rect = pygame.Rect(door_x, door_y, door_w, door_h)
    door_closed, door_open_progress = True, 0.0
    DOOR_OPEN_TIME = 0.4

    walls = build_walls(door_closed=True, door_rect=door_rect)
    player = Player(100, HEIGHT//2)
    # injeta atributos de sprite no jogador (mínima alteração)
    player.images_ok = images_ok
    player.idle_image = player_idle
    player.walk_images = player_walk
    player.idle_dir = player_idle_dir
    player.walk_dir = player_walk_dir
    player.base_w = base_w
    player.base_h = base_h
    player.frame = 0
    player.anim_timer = 0.0
    player.anim_speed = 0.12
    player._prev_facing = player.facing

    statue = Statue(600, 250)
    guards = [
        Guard([(500,60),(780,60),(780,300),(500,300)]),
        Guard([(260,200),(420,200),(420,320),(260,320)], speed=75),
    ]

    alarm, alarm_timer = False, 0.0
    ALERT_DURATION = 12.0
    child_caught, camera_recorded = False, False

    exit_zone = pygame.Rect(60, 60, 120, 120)
    child_area = pygame.Rect(120, HEIGHT-140, 160, 120)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e and player.rect.colliderect(door_rect.inflate(40,40)):
                    door_closed = False
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        player.update(dt, walls)

        # animação do jogador (usa dt; mínima alteração: mantém no loop de run)
        if player.images_ok:
            if player.moving:
                if player.facing != player._prev_facing:
                    player.frame = 0
                    player.anim_timer = 0.0
                    player._prev_facing = player.facing

                player.anim_timer += dt
                if player.anim_timer >= player.anim_speed:
                    player.anim_timer = 0.0
                    frames = player.walk_dir.get(player.facing, player.walk_images)
                    player.frame = (player.frame + 1) % len(frames)
            else:
                player.frame = 0
                player.anim_timer = 0.0

        if not door_closed and door_open_progress < 1.0:
            door_open_progress += dt / DOOR_OPEN_TIME
            if door_open_progress >= 1.0:
                door_open_progress = 1.0
                walls = build_walls(door_closed=False, door_rect=door_rect)
            else:
                current_h = int(door_h * (1.0 - door_open_progress))
                anim_rect = pygame.Rect(door_x, door_y + (door_h - current_h), door_w, current_h)
                walls = build_walls(door_closed=True, door_rect=anim_rect if current_h>0 else None)

        for g in guards:
            if g.alerted: g.chase(player, dt)
            else: g.update(dt)

        if not alarm:
            for g in guards:
                if g.can_see_player(player, walls):
                    g.alerted = alarm = True
                    alarm_timer = ALERT_DURATION
                    if alarm_sound:
                        try:
                            alarm_sound.play(loops=-1)
                        except Exception:
                            pass
        else:
            alarm_timer -= dt
            if alarm_timer <= 0:
                alarm = False
                for g in guards: g.alerted = False
                if alarm_sound:
                    try:
                        alarm_sound.stop()
                    except Exception:
                        pass

        if player.rect.colliderect(child_area): camera_recorded = True

        keys = pygame.key.get_pressed()
        if not statue.stolen and player.hitbox.colliderect(statue.rect):
            if keys[pygame.K_SPACE]:
                player.stealing = True
                player.steal_timer += dt
                if player.steal_timer >= STEAL_TIME:
                    statue.stolen = player.has_statue = True
                    player.stealing = False
                    for g in guards:
                        if g.can_see_player(player, walls): alarm = g.alerted = True
                    if alarm and alarm_sound:
                        try:
                            alarm_sound.play(loops=-1)
                        except Exception:
                            pass
                    if camera_recorded: child_caught = True
            else:
                player.stealing = False
                player.steal_timer = max(0, player.steal_timer - dt*1.6)
        else:
            player.stealing = False
            player.steal_timer = max(0, player.steal_timer - dt*0.8)

        # FIM DE JOGO: CAPTURA
        for g in guards:
            if g.rect.colliderect(player.rect) and g.alerted:
                if alarm_sound:
                    try:
                        alarm_sound.stop()
                    except Exception:
                        pass
                # tenta parar a música de fundo antes de mostrar a tela de game over
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                # usa a imagem GAME_OVER_BG como fundo, se carregada
                return show_end_screen_local(
                    screen, clock, font,
                    "",
                    "",
                    ALARM_COLOR,
                    GAME_OVER_BG,
                    game_over_sound  # << som de derrota
                )

        # FIM DE JOGO: SUCESSO
        if player.has_statue and player.rect.colliderect(exit_zone):
            if alarm_sound:
                try:
                    alarm_sound.stop()
                except Exception:
                    pass
            # para a música de fundo antes das telas finais
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            # Se o vídeo gravou a criança, usamos PRESA_VIDEO_BG
            if child_caught:
                ending = "Estátua recuperada, mas o vídeo incrimina — Gerluce presa."
                bg = PRESA_VIDEO_BG
                end_sound = game_over_sound  # mantém game over se o final for "punição"
            elif alarm:
                ending = "Fugiu com tensão: mas suspeitas permanecem."
                bg = VICTORY_BG
                end_sound = victory_sound  # vitória tensa — toca som de vitória se disponível
            else:
                ending = "Sucesso limpo: Gerluce escapou. Justiça feita!"
                bg = VICTORY_BG
                end_sound = victory_sound  # sucesso limpo — som de vitória

            # usa VICTORY_BG ou PRESA_VIDEO_BG se existir
            return show_end_screen_local(
                screen, clock, font,
                "MISSÃO CONCLUÍDA",
                ending,
                (180,240,180),
                bg,
                end_sound  # passa o som apropriado (vitória ou game_over em casos especiais)
            )

        # DRAWING
        if floor_tile:
            tw, th = floor_tile.get_width(), floor_tile.get_height()
            for yy in range(0, HEIGHT, th):
                for xx in range(0, WIDTH, tw):
                    screen.blit(floor_tile, (xx, yy))
            screen.blit(floor_overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)

        for w in walls: pygame.draw.rect(screen, WALL_COLOR, w)
        mat_rect = pygame.Rect(door_x - 14, door_y + door_h, door_w + 28, 22)
        pygame.draw.rect(screen, MAT_COLOR, mat_rect)
        draw_text(screen, "ENTRADA", door_x + door_w//2 - 28, mat_rect.y + 2, WHITE, font)

        if door_open_progress < 1.0:
            current_h = int(door_h * (1.0 - door_open_progress))
            if current_h > 0:
                pygame.draw.rect(screen, DOOR_COLOR, (door_x, door_y + (door_h - current_h), door_w, current_h))

        pygame.draw.rect(screen, (40,120,40), exit_zone, 2)
        draw_text(screen, "Saída", exit_zone.x+8, exit_zone.y+4, HINT_COLOR, font)
    
        statue.draw(screen)
        for g in guards: g.draw(screen)
        player.draw(screen)  # agora desenha sprite se disponível

        if door_closed and player.rect.colliderect(door_rect.inflate(40,40)):
            draw_text(screen, "Pressione E para abrir a porta", 18, HEIGHT-54, HINT_COLOR, font)

        hud_y = HEIGHT - 26
        status = "Estatueta: OK" if player.has_statue else "Estatueta: —"
        status2 = "Alarme: ATIVO" if alarm else "Alarme: off"
        draw_text(screen, status + "   " + status2, 18, hud_y, WHITE, font)
        if player.stealing:
            w = int((player.steal_timer/STEAL_TIME)*180)
            pygame.draw.rect(screen, (200,200,200), (WIDTH-220, hud_y, 180, 14), 2)
            pygame.draw.rect(screen, (200,120,40), (WIDTH-220, hud_y, w, 14))
            draw_text(screen, "Roubando...", WIDTH-220, hud_y-22, WHITE, font)

        if timer_box_img:
            box_w, box_h = 120, 110
            box = pygame.transform.smoothscale(timer_box_img, (box_w, box_h))
            x = WIDTH - 16 - box_w - 12
            y = 16
            screen.blit(box, (x, y))
            tempo_font = pygame.font.SysFont("consolas", 30, bold=True)
            tempo_val = int(alarm_timer) if alarm else 0
            tempo_txt = tempo_font.render(f"{tempo_val}", True, (255,255,255))
            screen.blit(
                tempo_txt,
                (x + box_w//2 - tempo_txt.get_width()//2,
                 y + box_h//2 - tempo_txt.get_height()//2)
            )

        draw_text(screen, "WASD: Mover | SPACE: Roubar | E: Porta", 18, 6, WHITE, font)
        pygame.display.flip()
