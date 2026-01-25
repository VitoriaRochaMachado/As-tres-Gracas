# fase2.py (versão finalizada)
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
WALL_COLOR = (80,80,80)
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
    try:
        if base_dir:
            path = os.path.join(base_dir, "assets", "alarme.mp3")
        else:
            path = "assets/alarme.mp3"
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass
        if pygame.mixer.get_init() is not None:
            alarm_sound = pygame.mixer.Sound(path)
            alarm_sound.set_volume(0.6)
    except Exception:
        alarm_sound = None
    return alarm_sound

def _load_images(base_dir=None):
    GAME_OVER_BG = None
    VICTORY_BG = None
    try:
        if base_dir:
            go_path = os.path.join(base_dir, "assets", "game_over.png")
            vi_path = os.path.join(base_dir, "assets", "vitoria.png")
        else:
            go_path = "assets/game_over.png"
            vi_path = "assets/vitoria.png"

        # carregar game over (se existir)
        try:
            GAME_OVER_BG = pygame.image.load(go_path).convert()
            GAME_OVER_BG = pygame.transform.scale(GAME_OVER_BG, (WIDTH, HEIGHT))
        except Exception:
            GAME_OVER_BG = None

        # carregar victory (opcional)
        try:
            VICTORY_BG = pygame.image.load(vi_path).convert()
            VICTORY_BG = pygame.transform.scale(VICTORY_BG, (WIDTH, HEIGHT))
        except Exception:
            VICTORY_BG = None
    except Exception:
        GAME_OVER_BG = None
        VICTORY_BG = None

    return GAME_OVER_BG, VICTORY_BG

# ----- ENTITIES -----
class Player:
    def __init__(self, x,y):
        self.rect = pygame.Rect(x,y,28,36)
        self.speed = PLAYER_SPEED
        self.stealing = False
        self.steal_timer = 0.0
        self.has_statue = False
        self.mask = False

    def update(self, dt, walls):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1
        if dx != 0 or dy != 0:
            l = math.hypot(dx,dy)
            dx /= l; dy /= l
        self.rect.x += dx * self.speed * dt
        self._collide(walls, dx, 0)
        self.rect.y += dy * self.speed * dt
        self._collide(walls, 0, dy)

    def _collide(self, walls, dx, dy):
        for w in walls:
            if self.rect.colliderect(w):
                if dx > 0: self.rect.right = w.left
                if dx < 0: self.rect.left = w.right
                if dy > 0: self.rect.bottom = w.top
                if dy < 0: self.rect.top = w.bottom

    def draw(self, surf):
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
def show_end_screen_local(screen, clock, font, title, msg, color, bg_image=None):
    """
    Exibe a tela final. Se bg_image for fornecida, usa-a como fundo.
    Retorna True se o jogador pedir para reiniciar (R).
    """
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
    """
    Substitui o antigo main(). Chamado pelo main.py como:
        fase2.run(screen, clock, font, BASE_DIR)
    Recebe screen/clock/font já inicializados pelo chamador.
    """
    # carregar sons e imagens (uma vez)
    alarm_sound = _load_sounds(base_dir)
    GAME_OVER_BG, VICTORY_BG = _load_images(base_dir)

    # inicialização local de entidades / estado
    door_w, door_h = 120, 16
    door_x, door_y = 200 + (600 - door_w) // 2, 120 + 200 - 16
    door_rect = pygame.Rect(door_x, door_y, door_w, door_h)
    door_closed, door_open_progress = True, 0.0
    DOOR_OPEN_TIME = 0.4

    walls = build_walls(door_closed=True, door_rect=door_rect)
    player = Player(100, HEIGHT//2)
    statue = Statue(600, 220)
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
        if not statue.stolen and player.rect.colliderect(statue.rect):
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
                # usa a imagem GAME_OVER_BG como fundo, se carregada
                return show_end_screen_local(
                    screen, clock, font,
                    "",
                    "",
                    ALARM_COLOR,
                    GAME_OVER_BG
                )

        # FIM DE JOGO: SUCESSO
        if player.has_statue and player.rect.colliderect(exit_zone):
            if alarm_sound:
                try:
                    alarm_sound.stop()
                except Exception:
                    pass
            if child_caught: ending = "Estatua recuperada mas vídeo incrimina — Gerluce presa."
            elif alarm: ending = "Fugiu com tensão: mas suspeitas permanecem."
            else: ending = "Sucesso limpo: Gerluce escapou. Justiça feita!"
            # usa VICTORY_BG se existir
            return show_end_screen_local(
                screen, clock, font,
                "MISSÃO CONCLUÍDA",
                ending,
                (180,240,180),
                VICTORY_BG
            )

        # DRAWING
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
        pygame.draw.rect(screen, (60,60,60), child_area, 1)
        draw_text(screen, "Vizinho", child_area.x+6, child_area.y+6, HINT_COLOR, font)

        statue.draw(screen)
        for g in guards: g.draw(screen)
        player.draw(screen)

        if door_closed and player.rect.colliderect(door_rect.inflate(40,40)):
            draw_text(screen, "Pressione E para abrir a porta", 18, HEIGHT-54, HINT_COLOR, font)

        hud_y = HEIGHT - 26
        status = "Estatueta: ✅" if player.has_statue else "Estatueta: —"
        status2 = "Alarme: ATIVO" if alarm else "Alarme: off"
        draw_text(screen, status + "   " + status2, 18, hud_y, WHITE, font)
        if player.stealing:
            w = int((player.steal_timer/STEAL_TIME)*180)
            pygame.draw.rect(screen, (200,200,200), (WIDTH-220, hud_y, 180, 14), 2)
            pygame.draw.rect(screen, (200,120,40), (WIDTH-220, hud_y, w, 14))
            draw_text(screen, "Roubando...", WIDTH-220, hud_y-22, WHITE, font)

        draw_text(screen, "WASD: Mover | SPACE: Roubar | E: Porta", 18, 6, WHITE, font)
        pygame.display.flip()
