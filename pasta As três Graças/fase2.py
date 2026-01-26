# fase2.py — câmeras com varredura (sweep) — mínima alteração sobre a versão anterior
import pygame
import sys
import math
import os

# ----- CONFIG -----
WIDTH, HEIGHT = 1024, 640
FPS = 60

# cores
WHITE = (240,240,240)
BG_COLOR = (18,18,26)
WALL_COLOR = (80,80,80)
CAM_COLOR = (120,120,200)
PANEL_COLOR = (200,160,60)
PLAYER_COLOR = (200,60,80)
ALARM_COLOR = (220,20,20)
HINT_COLOR = (180,180,255)

# gameplay
PLAYER_SPEED = 200
TIME_LIMIT = 35.0
SABOTAGE_TIME = 1.8
CAM_FOV_ANGLE = 70
CAM_FOV_DIST = 260

# ----- SONS / ASSETS -----
def _load_sounds(base_dir=None):
    alarm_s = None
    sabotage_s = None
    try:
        if base_dir:
            alarm_path = os.path.join(base_dir, "assets", "alarme.mp3")
            sabotage_path = os.path.join(base_dir, "assets", "sabotagem.mp3")
        else:
            alarm_path = "assets/alarme.mp3"
            sabotage_path = "assets/sabotagem.mp3"

        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        if os.path.exists(alarm_path):
            alarm_s = pygame.mixer.Sound(alarm_path)
            alarm_s.set_volume(0.6)

        if os.path.exists(sabotage_path):
            sabotage_s = pygame.mixer.Sound(sabotage_path)
            sabotage_s.set_volume(0.6)

    except Exception:
        alarm_s = None
        sabotage_s = None

    return alarm_s, sabotage_s

def _load_player_sprites(base_dir=None):
    idle = None
    walk = []
    ok = False
    try:
        player_dir = os.path.join(base_dir or "", "assets", "player")
        idle_path = os.path.join(player_dir, "idle.png")

        if os.path.exists(idle_path):
            idle = pygame.image.load(idle_path).convert_alpha()

        for i in range(8):
            p = os.path.join(player_dir, f"walk_{i}.png")
            if os.path.exists(p):
                walk.append(pygame.image.load(p).convert_alpha())

        if idle:
            walk = walk or [idle]
            ok = True

    except Exception:
        ok = False

    return ok, idle, walk

# ----- ENTIDADES -----
class Player:
    def __init__(self, x,y):
        self.rect = pygame.Rect(x, y, 45, 75)

        self.speed = PLAYER_SPEED
        self.images_ok = False
        self.idle = None
        self.walk = []
        self.frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.12
        self.moving = False
        self.facing_left = False

    def update(self, dt, walls):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        if dx or dy:
            l = math.hypot(dx,dy)
            dx /= l; dy /= l

        self.facing_left = dx < 0
        self.moving = bool(dx or dy)

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
        if self.images_ok and self.idle:
            sprite = self.walk[self.frame] if self.moving else self.idle
            try:
                sprite = pygame.transform.smoothscale(sprite, self.rect.size)
            except Exception:
                sprite = pygame.transform.scale(sprite, self.rect.size)
            if self.facing_left:
                sprite = pygame.transform.flip(sprite, True, False)
            surf.blit(sprite, self.rect.topleft)
        else:
            pygame.draw.rect(surf, PLAYER_COLOR, self.rect)

class Camera:
    """
    Camera now supports an optional sweep:
      - angle: current angle in degrees
      - min_angle, max_angle: bounds for sweeping (deg)
      - sweep_speed: degrees per second (positive)
      - sweep_dir: 1 or -1 (current sweep direction)
    """
    def __init__(self, x, y, angle, min_angle=None, max_angle=None, sweep_speed=0):
        self.pos = pygame.Vector2(x,y)
        self.angle = float(angle)
        self.rect = pygame.Rect(x-10,y-10,20,20)

        # sweep parameters (optional). If min/max are None or speed==0 => static camera
        self.min_angle = float(min_angle) if min_angle is not None else None
        self.max_angle = float(max_angle) if max_angle is not None else None
        self.sweep_speed = float(sweep_speed)
        self.sweep_dir = 1  # 1 -> increasing angle, -1 -> decreasing

    def update(self, dt):
        # if sweep is configured, advance angle and bounce between min/max
        if self.min_angle is not None and self.max_angle is not None and self.sweep_speed != 0:
            self.angle += self.sweep_dir * self.sweep_speed * dt
            # bounce
            if self.angle > self.max_angle:
                self.angle = self.max_angle
                self.sweep_dir = -1
            elif self.angle < self.min_angle:
                self.angle = self.min_angle
                self.sweep_dir = 1

    def can_see(self, player_rect, walls):
        start = self.pos
        target = pygame.Vector2(player_rect.center)
        vec = target - start
        dist = vec.length()
        if dist == 0:
            return True
        if dist > CAM_FOV_DIST:
            return False

        to_player_angle = math.degrees(math.atan2(vec.y, vec.x))
        diff = (to_player_angle - self.angle + 180) % 360 - 180
        if abs(diff) > CAM_FOV_ANGLE/2:
            return False

        steps = max(6, int(dist // 8))
        for i in range(1, steps+1):
            p = start + vec * (i/steps)
            r = pygame.Rect(p.x-2, p.y-2, 4, 4)
            for w in walls:
                if r.colliderect(w):
                    return False
        return True

    def draw(self, surf):
        pygame.draw.rect(surf, CAM_COLOR, self.rect)
        # cone visualization based on current angle
        a1 = math.radians(self.angle - CAM_FOV_ANGLE/2)
        a2 = math.radians(self.angle + CAM_FOV_ANGLE/2)
        p1 = self.pos + pygame.Vector2(math.cos(a1), math.sin(a1)) * CAM_FOV_DIST
        p2 = self.pos + pygame.Vector2(math.cos(a2), math.sin(a2)) * CAM_FOV_DIST
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (80,80,200,40), [self.pos, p1, p2])
        surf.blit(s, (0,0))

# ----- HELPERS -----
def draw_text(surf, txt, x, y, font, color=WHITE):
    surf.blit(font.render(txt, True, color), (x,y))

def build_walls():
    return [
        pygame.Rect(0,0,WIDTH,16),
        pygame.Rect(0,0,16,HEIGHT),
        pygame.Rect(0,HEIGHT-16,WIDTH,16),
        pygame.Rect(WIDTH-16,0,16,HEIGHT),
        pygame.Rect(240,100,16,440),
        pygame.Rect(500,100,16,440),
        pygame.Rect(760,100,16,440),
    ]

# ----- RUN -----
def run(screen, clock, font, base_dir=None):
    alarm_sound, sabotage_sound = _load_sounds(base_dir)
    sprites_ok, idle_img, walk_imgs = _load_player_sprites(base_dir)

    # --- MÚSICA DE FUNDO DA FASE 2 (ADIÇÃO MÍNIMA) ---
    try:
        if base_dir:
            fase2_music_path = os.path.join(base_dir, "assets", "som_fase2.mp3")
        else:
            fase2_music_path = "assets/som_fase2.mp3"

        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        if os.path.exists(fase2_music_path) and pygame.mixer.get_init() is not None:
            try:
                pygame.mixer.music.load(fase2_music_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)  # loop infinito
            except Exception:
                pass
    except Exception:
        pass
    # ----------------------------------------------

    def stop_alarm():
        try:
            if alarm_sound:
                alarm_sound.stop()
        except Exception:
            pass
        # também para a música de fundo (adicional mínimo)
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    walls = build_walls()
    player = Player(80, HEIGHT//2)
    player.images_ok = sprites_ok
    player.idle = idle_img
    player.walk = walk_imgs

    # Cameras: now with sweep. Arguments: x,y,initial_angle,min_angle,max_angle,sweep_speed
    cams = [
        Camera(360,200, -35, -60, 0, 30.0),   # varre de -60 a 0 graus a 30°/s
        Camera(620,360, 215, 180, 250, 22.0), # varre de 180 a 250 graus a 22°/s
    ]

    panel = pygame.Rect(480,120,40,40)
    sabotage_timer = 0.0
    recorded = False
    timer = TIME_LIMIT

    alarm_playing = False

    # feedback when sabotage completes
    sabotage_success_time = 0.0
    SHOW_SABOTAGE_MSG = 0.9
    sabotage_success = False

    while True:
        dt = clock.tick(FPS)/1000.0
        timer -= dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                stop_alarm()
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    stop_alarm()
                    pygame.quit(); sys.exit()

        if timer <= 0:
            stop_alarm()
            return "LOSE"

        player.update(dt, walls)

        if player.images_ok:
            if player.moving:
                player.anim_timer += dt
                if player.anim_timer >= player.anim_speed:
                    player.anim_timer = 0.0
                    player.frame = (player.frame+1) % len(player.walk)
            else:
                player.frame = 0

        keys = pygame.key.get_pressed()
        # sabotagem: acumula enquanto estiver pressionando SPACE sobre o painel
        if not sabotage_success and player.rect.colliderect(panel) and keys[pygame.K_SPACE]:
            sabotage_timer += dt
            if sabotage_sound and sabotage_timer < 0.06:
                try:
                    sabotage_sound.play()
                except Exception:
                    pass
            if sabotage_timer >= SABOTAGE_TIME:
                # ---- MINIMAL FIX: when sabotage completes, clear cams AND clear recorded/alarm ----
                cams.clear()
                recorded = False
                # stop any playing alarm and reset flag
                stop_alarm()
                alarm_playing = False
                sabotage_success = True
                sabotage_success_time = 0.0
        else:
            if not sabotage_success:
                sabotage_timer = max(0.0, sabotage_timer - dt*1.6)

        # if sabotage just succeeded, show message then continue (do not let cameras trigger during the message)
        if sabotage_success:
            sabotage_success_time += dt
            # draw a quick message frame
            screen.fill(BG_COLOR)
            for w in walls:
                pygame.draw.rect(screen, WALL_COLOR, w)
            for c in cams:
                c.draw(screen)
            pygame.draw.rect(screen, PANEL_COLOR, panel)
            player.draw(screen)
            draw_text(screen, f"TEMPO: {int(timer)}s", 18, 18, font, ALARM_COLOR)
            draw_text(screen, "SABOTAGEM: SUCESSO", WIDTH//2 - 120, HEIGHT//2 - 10, font, HINT_COLOR)
            pygame.display.flip()
            if sabotage_success_time >= SHOW_SABOTAGE_MSG:
                sabotage_success = False
                sabotage_timer = 0.0
            else:
                continue  # show message fully before proceeding

        # Update camera angles (sweep) BEFORE visibility checks
        for c in cams:
            c.update(dt)

        # check cameras only if there are cameras
        saw_now = False
        if cams:
            for c in cams:
                if c.can_see(player.rect, walls):
                    saw_now = True
                    break

        if saw_now:
            recorded = True
            # start alarm if not already playing
            if alarm_sound and not alarm_playing:
                try:
                    alarm_sound.play(loops=-1)
                    alarm_playing = True
                except Exception:
                    alarm_playing = False

        # if recorded, show message briefly then return RECORDED (main shows game over)
        if recorded:
            # show immediate message frame so player sees it
            screen.fill(BG_COLOR)
            for w in walls:
                pygame.draw.rect(screen, WALL_COLOR, w)
            for c in cams:
                c.draw(screen)
            pygame.draw.rect(screen, PANEL_COLOR, panel)
            player.draw(screen)
            draw_text(screen, f"TEMPO: {int(timer)}s", 18, 18, font, ALARM_COLOR)
            draw_text(screen, "CÂMERAS GRAVARAM", WIDTH//2 - 120, HEIGHT//2 - 10, font, ALARM_COLOR)
            pygame.display.flip()
            # stop alarm and music (we show message, then return)
            stop_alarm()
            alarm_playing = False
            return "RECORDED"

        # exit condition: reach right edge
        if player.rect.right >= WIDTH - 64 and not cams:
            stop_alarm()
            return "CLEAN"

        # drawing normal frame
        screen.fill(BG_COLOR)
        for w in walls:
            pygame.draw.rect(screen, WALL_COLOR, w)
        for c in cams:
            c.draw(screen)
        pygame.draw.rect(screen, PANEL_COLOR, panel)
        player.draw(screen)

        # HUD / instructions
        draw_text(screen, f"TEMPO: {int(timer)}s", 18, 18, font, ALARM_COLOR)
        draw_text(screen, "OBJETIVO: atravesse sem ser filmada", 18, 44, font, HINT_COLOR)
        draw_text(screen, "WASD / Setas: mover", 18, HEIGHT-70, font, WHITE)
        draw_text(screen, "SPACE: sabotar painel", 18, HEIGHT-44, font, WHITE)

        if panel.colliderect(player.rect):
            draw_text(screen, "Pressione SPACE para sabotar", panel.x-120, panel.y-26, font, HINT_COLOR)

        pygame.display.flip()
