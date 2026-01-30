# fase2.py — câmeras com varredura
# Essa fase é tipo um “stealth”: atravessar a sala sem ser visto pelas câmeras,
# ou sabotar o painel pra desligar as câmeras.

import pygame
import sys
import math
import os

# ----- CONFIG -----
WIDTH, HEIGHT = 1024, 640
FPS = 60

# cores (só constantes pra facilitar)
WHITE = (240,240,240)
BG_COLOR = (18,18,26)
WALL_COLOR = (25,25,25)
CAM_COLOR = (120,120,200)
PANEL_COLOR = (200,160,60)
PLAYER_COLOR = (200,60,80)
ALARM_COLOR = (220,20,20)
HINT_COLOR = (180,180,255)

# gameplay
PLAYER_SPEED = 200
TIME_LIMIT = 35.0          # tempo total da fase
SABOTAGE_TIME = 0.5        # quanto tempo segurando SPACE pra sabotar
CAM_FOV_ANGLE = 70         # abertura do “cone de visão” da câmera
CAM_FOV_DIST = 260         # alcance do cone

# ----- SONS / ASSETS -----
def _load_sounds(base_dir=None):
    # carrega sons (alarme e som de sabotagem)
    alarm_s = None
    sabotage_s = None
    try:
        # monta caminhos dependendo se veio base_dir (pra rodar pelo main)
        if base_dir:
            alarm_path = os.path.join(base_dir, "assets", "alarme.mp3")
            sabotage_path = os.path.join(base_dir, "assets", "sabotagem.mp3")
        else:
            alarm_path = "assets/alarme.mp3"
            sabotage_path = "assets/sabotagem.mp3"

        # garante mixer inicializado
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        # carrega alarme
        if os.path.exists(alarm_path):
            alarm_s = pygame.mixer.Sound(alarm_path)
            alarm_s.set_volume(0.6)

        # carrega sabotagem
        if os.path.exists(sabotage_path):
            sabotage_s = pygame.mixer.Sound(sabotage_path)
            sabotage_s.set_volume(0.6)

    except Exception:
        alarm_s = None
        sabotage_s = None

    return alarm_s, sabotage_s

def _trim_sprite(surf):
    # recorta a área transparente do sprite (pra ajudar no scale)
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

def _load_player_sprites(base_dir=None):
    # carrega sprites do player (idle / walk / por direção)
    idle = None
    walk = []
    ok = False
    idle_dir = {}
    walk_dir = {}
    base_w = 1
    base_h = 1
    try:
        player_dir = os.path.join(base_dir or "", "assets", "player")
        idle_path = os.path.join(player_dir, "idle.png")

        # idle geral
        if os.path.exists(idle_path):
            idle = pygame.image.load(idle_path).convert_alpha()

        # walk geral (fallback)
        for i in range(3):
            p = os.path.join(player_dir, f"walk_{i}.png")
            if os.path.exists(p):
                walk.append(pygame.image.load(p).convert_alpha())

        # idle por direção
        idle_files = {
            "down": "idledown.png",
            "up": "idleup.png",
            "left": "idleleft.png",
            "right": "idleright.png",
        }
        for d, fn in idle_files.items():
            p = os.path.join(player_dir, fn)
            if os.path.exists(p):
                idle_dir[d] = pygame.image.load(p).convert_alpha()

        # walk por direção (3 frames)
        for d in ["down","up","left","right"]:
            frames = []
            for i in range(3):
                p = os.path.join(player_dir, f"walk_{i}{d}.png")
                if os.path.exists(p):
                    frames.append(pygame.image.load(p).convert_alpha())
            if frames:
                walk_dir[d] = frames

        # se não tiver idle geral, tenta usar o idle down
        if idle is None:
            idle = idle_dir.get("down", None)

        # se tiver idle, considera sprites “ok”
        if idle:
            walk = walk or [idle]  # se não tiver walk, usa idle como walk
            ok = True

        # recorta transparência
        if idle is not None:
            idle = _trim_sprite(idle)
        walk = [_trim_sprite(s) for s in walk]

        for k in list(idle_dir.keys()):
            idle_dir[k] = _trim_sprite(idle_dir[k])

        for k in list(walk_dir.keys()):
            walk_dir[k] = [_trim_sprite(s) for s in walk_dir[k]]

        # pega tamanho base pra escala proporcional
        all_sprites = []
        if idle is not None:
            all_sprites.append(idle)
        all_sprites += walk
        all_sprites += list(idle_dir.values())
        for frames in walk_dir.values():
            all_sprites += list(frames)

        if all_sprites:
            base_w = max(s.get_width() for s in all_sprites)
            base_h = max(s.get_height() for s in all_sprites)

    except Exception:
        ok = False

    return ok, idle, walk, idle_dir, walk_dir, base_w, base_h

# ----- ENTIDADES -----
class Player:
    def __init__(self, x,y):
        # rect é o “tamanho visual”; hitbox é menor pra colisão
        self.rect = pygame.Rect(x, y, 64, 96)
        self.hitbox = self.rect.inflate(-30, -40)
        self.hitbox.midbottom = self.rect.midbottom

        self.speed = PLAYER_SPEED

        # dados de sprite (podem ficar vazios e desenhar retângulo)
        self.images_ok = False
        self.idle = None
        self.walk = []
        self.idle_dir = {}
        self.walk_dir = {}
        self.base_w = 1
        self.base_h = 1

        # animação e estado
        self.frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.12
        self.moving = False
        self.facing_left = False
        self.facing = "down"
        self._prev_facing = self.facing

    def update(self, dt, walls):
        # controla movimento pelo teclado
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1

        # normaliza pra diagonal não ser mais rápida
        if dx or dy:
            l = math.hypot(dx,dy)
            if l != 0:
                dx /= l; dy /= l

        # atualiza a direção que o player está olhando (pra escolher sprite)
        if dx != 0 or dy != 0:
            if abs(dx) > abs(dy):
                if dx < 0:
                    self.facing_left = True
                    self.facing = "left"
                elif dx > 0:
                    self.facing_left = False
                    self.facing = "right"
            else:
                if dy < 0:
                    self.facing = "up"
                elif dy > 0:
                    self.facing = "down"

        self.moving = bool(dx or dy)

        # move no eixo X e resolve colisão
        self.hitbox.x += dx * self.speed * dt
        self._collide(walls, dx, 0)

        # move no eixo Y e resolve colisão
        self.hitbox.y += dy * self.speed * dt
        self._collide(walls, 0, dy)

        # atualiza o rect visual baseado na hitbox
        self.rect.midbottom = self.hitbox.midbottom

    def _collide(self, walls, dx, dy):
        # colisão simples: se encostar numa parede, empurra pra fora
        for w in walls:
            if self.hitbox.colliderect(w):
                if dx > 0: self.hitbox.right = w.left
                if dx < 0: self.hitbox.left = w.right
                if dy > 0: self.hitbox.bottom = w.top
                if dy < 0: self.hitbox.top = w.bottom

    def draw(self, surf):
        # se tiver sprites, desenha sprite; senão desenha retângulo
        if self.images_ok and self.idle:
            if self.moving:
                frames = self.walk_dir.get(self.facing)
                if frames:
                    sprite = frames[self.frame % len(frames)]
                else:
                    sprite = self.walk[self.frame] if self.walk else self.idle
            else:
                sprite = self.idle_dir.get(self.facing, self.idle)

            # escala proporcional pra caber no rect do player
            w, h = sprite.get_size()
            scale = min(self.rect.width / self.base_w, self.rect.height / self.base_h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

            try:
                sprite_scaled = pygame.transform.smoothscale(sprite, new_size)
            except Exception:
                sprite_scaled = pygame.transform.scale(sprite, new_size)

            # flip caso esteja indo pra esquerda e não tenha sprite por direção
            if self.facing_left and (self.facing not in self.walk_dir) and (self.facing not in self.idle_dir):
                sprite_scaled = pygame.transform.flip(sprite_scaled, True, False)

            x = self.rect.centerx - sprite_scaled.get_width() // 2
            y = self.rect.centery - sprite_scaled.get_height() // 2
            surf.blit(sprite_scaled, (x, y))
        else:
            pygame.draw.rect(surf, PLAYER_COLOR, self.rect)


class Camera:
    def __init__(self, x, y, angle, min_angle=None, max_angle=None, sweep_speed=0):
        # posição central da câmera
        self.pos = pygame.Vector2(x,y)
        self.angle = float(angle)

        # retângulo visual da câmera
        self.rect = pygame.Rect(x-10,y-10,20,20)

        # configurações de varredura (se tiver min/max)
        self.min_angle = float(min_angle) if min_angle is not None else None
        self.max_angle = float(max_angle) if max_angle is not None else None
        self.sweep_speed = float(sweep_speed)
        self.sweep_dir = 1  # 1 aumenta ângulo, -1 diminui ângulo

        self.sprite = None

    def update(self, dt):
        # se tiver varredura, muda o ângulo e inverte quando bater nos limites
        if self.min_angle is not None and self.max_angle is not None and self.sweep_speed != 0:
            self.angle += self.sweep_dir * self.sweep_speed * dt
            if self.angle > self.max_angle:
                self.angle = self.max_angle
                self.sweep_dir = -1
            elif self.angle < self.min_angle:
                self.angle = self.min_angle
                self.sweep_dir = 1

    def can_see(self, player_rect, walls):
        # checa se o player está dentro do cone e sem parede bloqueando
        start = self.pos
        target = pygame.Vector2(player_rect.center)
        vec = target - start
        dist = vec.length()

        if dist == 0:
            return True
        if dist > CAM_FOV_DIST:
            return False

        # diferença de ângulo entre onde a câmera olha e onde o player está
        to_player_angle = math.degrees(math.atan2(vec.y, vec.x))
        diff = (to_player_angle - self.angle + 180) % 360 - 180
        if abs(diff) > CAM_FOV_ANGLE/2:
            return False

        # “raycast” simples: caminha ponto a ponto e vê se bate em parede
        steps = max(6, int(dist // 8))
        for i in range(1, steps+1):
            p = start + vec * (i/steps)
            r = pygame.Rect(p.x-2, p.y-2, 4, 4)
            for w in walls:
                if r.colliderect(w):
                    return False
        return True

    def draw(self, surf):
        # desenha sprite da câmera (ou retângulo)
        if self.sprite:
            try:
                img = pygame.transform.smoothscale(self.sprite, self.rect.size)
            except Exception:
                img = pygame.transform.scale(self.sprite, self.rect.size)
            surf.blit(img, self.rect.topleft)
        else:
            pygame.draw.rect(surf, CAM_COLOR, self.rect)

        # desenha o cone de visão como um triângulo transparente
        a1 = math.radians(self.angle - CAM_FOV_ANGLE/2)
        a2 = math.radians(self.angle + CAM_FOV_ANGLE/2)
        p1 = self.pos + pygame.Vector2(math.cos(a1), math.sin(a1)) * CAM_FOV_DIST
        p2 = self.pos + pygame.Vector2(math.cos(a2), math.sin(a2)) * CAM_FOV_DIST
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (80,80,200,40), [self.pos, p1, p2])
        surf.blit(s, (0,0))

# ----- HELPERS -----
def draw_text(surf, txt, x, y, font, color=WHITE):
    # helper rápido pra desenhar texto
    surf.blit(font.render(txt, True, color), (x,y))

def build_walls(sw, sh):
    # cria paredes e deixa uma “porta” na parede direita (gap)
    door_h = int(sh * 0.16)
    door_y = sh//2 - door_h//2
    wall_thick = 16

    return [
        # bordas
        pygame.Rect(0,0,sw,16),
        pygame.Rect(0,0,16,sh),
        pygame.Rect(0,sh-16,sw,16),

        # parede direita com buraco no meio (porta)
        pygame.Rect(sw-16, 0, wall_thick, door_y),
        pygame.Rect(sw-16, door_y + door_h, wall_thick, sh - (door_y + door_h)),

        # colunas internas (tipo corredores)
        pygame.Rect(int(sw*0.234),int(sh*0.156),16,int(sh*0.688)),
        pygame.Rect(int(sw*0.488),int(sh*0.156),16,int(sh*0.688)),
        pygame.Rect(int(sw*0.742),int(sh*0.156),16,int(sh*0.688)),
    ]

def _load_camera_sprite(base_dir=None):
    # tenta carregar sprite da câmera (opcional)
    try:
        if base_dir:
            p = os.path.join(base_dir, "assets", "camera.png")
        else:
            p = os.path.join("assets", "camera.png")
        if os.path.exists(p):
            return pygame.image.load(p).convert_alpha()
    except Exception:
        pass
    return None



# ----- RUN -----
def run(screen, clock, font, base_dir=None):
    # pega o tamanho real da tela (pra funcionar em fullscreen também)
    SW, SH = screen.get_size()

    # carrega assets principais
    cam_sprite = _load_camera_sprite(base_dir)
    alarm_sound, sabotage_sound = _load_sounds(base_dir)
    sprites_ok, idle_img, walk_imgs, idle_dir, walk_dir, base_w, base_h = _load_player_sprites(base_dir)

    # --- PISO + OVERLAY + TIMER BOX + PAINEL (VISUAL) ---
    panel_img = None
    try:
        # caminhos de assets
        if base_dir:
            floor_path = os.path.join(base_dir, "assets", "piso_madeira.png")
            timer_box_path = os.path.join(base_dir, "assets", "timer_box.png")
            panel_path = os.path.join(base_dir, "assets", "painel.png")
        else:
            floor_path = os.path.join("assets", "piso_madeira.png")
            timer_box_path = os.path.join("assets", "timer_box.png")
            panel_path = os.path.join("assets", "painel.png")

        # piso em tile
        floor_img = pygame.image.load(floor_path).convert()
        floor_tile = pygame.transform.smoothscale(floor_img, (74, 74))
        
        # imagem da caixa do timer
        timer_box_img = pygame.image.load(timer_box_path).convert_alpha()

        # imagem do painel (onde sabota)
        if os.path.exists(panel_path):
            panel_img = pygame.image.load(panel_path).convert_alpha()
            panel_img = pygame.transform.smoothscale(panel_img, (40, 40))
    except Exception:
        # se der erro, usa fallbacks simples
        floor_tile = None
        timer_box_img = None
        panel_img = None

    # overlay escuro por cima do piso
    floor_overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
    floor_overlay.fill((0, 0, 0, 100))

    def draw_floor_and_walls(walls):
        # desenha fundo + piso tile + paredes
        screen.fill(BG_COLOR)
        if floor_tile:
            tw, th = floor_tile.get_width(), floor_tile.get_height()
            for yy in range(0, SH, th):
                for xx in range(0, SW, tw):
                    screen.blit(floor_tile, (xx, yy))
            screen.blit(floor_overlay, (0, 0))
        for w in walls:
            pygame.draw.rect(screen, WALL_COLOR, w)

    def draw_timer_box(seconds_left):
        # desenha timer na caixa ou como texto simples
        if timer_box_img:
            box_w, box_h = 120, 110
            box = pygame.transform.smoothscale(timer_box_img, (box_w, box_h))
            x = SW - 16 - box_w - 12
            y = 16
            screen.blit(box, (x, y))
            tempo_font = pygame.font.SysFont("consolas", 30, bold=True)
            tempo_txt = tempo_font.render(f"{int(seconds_left)}", True, (255,255,255))
            screen.blit(tempo_txt, (x + box_w//2 - tempo_txt.get_width()//2, y + box_h//2 - tempo_txt.get_height()//2))
        else:
            draw_text(screen, f"TEMPO: {int(seconds_left)}s", 18, 18, font, ALARM_COLOR)

    def draw_panel(rect):
        # desenha o painel (imagem ou quadrado)
        if panel_img:
            screen.blit(panel_img, (rect.x, rect.y))
        else:
            pygame.draw.rect(screen, PANEL_COLOR, rect)

    # --- MÚSICA DE FUNDO ---
    # toca um som de fundo só pra fase 2
    try:
        if base_dir:
            fase2_music_path = os.path.join(base_dir, "assets", "som_fase2.mp3")
        else:
            fase2_music_path = "assets/som_fase2.mp3"
        if os.path.exists(fase2_music_path) and pygame.mixer.get_init() is not None:
            pygame.mixer.music.load(fase2_music_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
    except Exception:
        pass

    def stop_alarm():
        # para o alarme e para a música (usado quando perde/vence)
        try:
            if alarm_sound: alarm_sound.stop()
            pygame.mixer.music.stop()
        except Exception:
            pass

    # paredes da sala
    walls = build_walls(SW, SH)

    # porta de saída (é o buraco da parede direita)
    door_h = int(SH * 0.16)
    door_y = SH//2 - door_h//2
    door_rect = pygame.Rect(SW-16, door_y, 16, door_h)

    # cria player e injeta sprites carregados
    player = Player(80, HEIGHT//2)
    player.images_ok, player.idle, player.walk, player.idle_dir, player.walk_dir, player.base_w, player.base_h = sprites_ok, idle_img, walk_imgs, idle_dir, walk_dir, base_w, base_h

    # lista de câmeras (com varredura usando min/max e sweep_speed)
    cams = [
        Camera(int(SW*0.35), int(SH*0.25), -35, -60, 0, 30.0),
        Camera(int(SW*0.60), int(SH*0.45), 215, 180, 250, 22.0),

        Camera(int(SW*0.86), int(SH*0.20), 0, -50, 50, 25.0),
        Camera(int(SW*0.86), int(SH*0.40), 0, -50, 50, 25.0),
        Camera(int(SW*0.86), int(SH*0.60), 0, -50, 50, 25.0),
        Camera(int(SW*0.86), int(SH*0.80), 0, -50, 50, 25.0),
    ]
    # aplica sprite pra todas as câmeras (se tiver)
    for c in cams:
        c.sprite = cam_sprite

    # painel onde o player pode sabotar (fica no meio)
    panel = pygame.Rect(int(SW*0.49), int(SH*0.18), 40, 40)
    panel_area = panel.inflate(120, 120)  # área maior pra facilitar interação

    # variáveis de estado
    sabotage_timer = 0.0
    recorded = False
    timer = TIME_LIMIT
    alarm_playing = False

    # pra mostrar mensagem de sucesso da sabotagem por um tempo curto
    sabotage_success_time = 0.0
    SHOW_SABOTAGE_MSG = 0.9
    sabotage_success = False

    # loop principal da fase
    while True:
        dt = clock.tick(FPS)/1000.0
        timer -= dt

        # eventos básicos (fechar e ESC)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                stop_alarm()
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                stop_alarm()
                pygame.quit(); sys.exit()

        # se acabou o tempo, perde
        if timer <= 0:
            stop_alarm()
            return "LOSE"

        # atualiza player (movimento/colisão)
        player.update(dt, walls)

        # se não tem mais câmeras (sabotou) e chegou na porta, passa limpo
        if (not cams) and player.hitbox.colliderect(door_rect.inflate(40, 40)):
            stop_alarm()
            return "CLEAN"

        # animação do player
        if player.images_ok:
            if player.moving:
                if player.facing != player._prev_facing:
                    player.frame, player.anim_timer = 0, 0.0
                    player._prev_facing = player.facing
                player.anim_timer += dt
                if player.anim_timer >= player.anim_speed:
                    player.anim_timer = 0.0
                    frames = player.walk_dir.get(player.facing, player.walk)
                    player.frame = (player.frame+1) % len(frames)
            else:
                player.frame = 0

        # -------- SABOTAGEM NO PAINEL --------
        keys = pygame.key.get_pressed()
        if not sabotage_success and player.hitbox.colliderect(panel_area) and keys[pygame.K_SPACE]:
            sabotage_timer += dt

            # toca um “bip” no começo de segurar
            if sabotage_sound and sabotage_timer < 0.06:
                try:
                    sabotage_sound.play()
                except Exception:
                    pass

            # quando completa o tempo, desliga as câmeras
            if sabotage_timer >= SABOTAGE_TIME:
                cams = []             # remove câmeras
                recorded = False      # limpa status
                stop_alarm()
                alarm_playing = False
                sabotage_success = True
                sabotage_success_time = 0.0
        else:
            # se soltou antes de completar, volta o timer um pouco (pra não ficar fácil)
            if not sabotage_success:
                sabotage_timer = max(0.0, sabotage_timer - dt*1.6)

        # mostra a mensagem de “sucesso” por um tempinho e continua o loop
        if sabotage_success:
            sabotage_success_time += dt
            draw_floor_and_walls(walls)
            pygame.draw.rect(screen, PANEL_COLOR, door_rect)
            for c in cams: 
                c.draw(screen)
            draw_panel(panel)
            player.draw(screen)
            draw_timer_box(timer)
            draw_text(screen, "SABOTAGEM: SUCESSO", WIDTH//2 - 120, HEIGHT//2 - 10, font, HINT_COLOR)
            pygame.display.flip()

            if sabotage_success_time >= SHOW_SABOTAGE_MSG:
                sabotage_success = False
                sabotage_timer = 0.0
            else:
                continue

        # atualiza varredura das câmeras
        for c in cams:
            c.update(dt)

        # -------- DETECÇÃO DAS CÂMERAS --------
        saw_now = False
        if cams:
            for c in cams:
                if c.can_see(player.rect, walls):
                    saw_now = True
                    break

        # se alguma câmera viu, aciona gravação e liga alarme
        if saw_now:
            recorded = True
            if alarm_sound and not alarm_playing:
                try:
                    alarm_sound.play(loops=-1)
                    alarm_playing = True
                except Exception:
                    pass

        # se gravou, mostra mensagem e encerra a fase como “RECORDED”
        if recorded:
            draw_floor_and_walls(walls)
            pygame.draw.rect(screen, PANEL_COLOR, door_rect)
            for c in cams: 
                c.draw(screen)
            draw_panel(panel)
            player.draw(screen)
            draw_timer_box(timer)
            draw_text(screen, "CÂMERAS GRAVARAM", WIDTH//2 - 120, HEIGHT//2 - 10, font, ALARM_COLOR)
            pygame.display.flip()

            stop_alarm()
            alarm_playing = False
            return "RECORDED"

        # -------- DESENHO NORMAL (sem derrota/sem mensagem) --------
        draw_floor_and_walls(walls)
        pygame.draw.rect(screen, PANEL_COLOR, door_rect)

        for c in cams:
            c.draw(screen)

        draw_panel(panel)
        player.draw(screen)

        draw_timer_box(timer)

        # textos de ajuda/objetivo
        draw_text(screen, "OBJETIVO: atravesse sem ser filmada", 18, 44, font, HINT_COLOR)
        draw_text(screen, "WASD / Setas: mover", 18, HEIGHT-70, font, WHITE)
        draw_text(screen, "SPACE: sabotar painel", 18, HEIGHT-44, font, WHITE)

        # dica perto do painel
        if panel.colliderect(player.rect):
            draw_text(screen, "Pressione SPACE para sabotar", panel.x-120, panel.y-26, font, HINT_COLOR)

        pygame.display.flip()
