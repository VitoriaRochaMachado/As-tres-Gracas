import pygame
import math
import random
import os 

# Configurações locais da Fase 1
WHITE = (240,240,240)
ALARM_COLOR = (220,20,20)
HINT_COLOR = (180,180,255)
SAFE_COLOR = (50, 50, 50)
PAPER_COLOR = (255, 255, 200)
WALL_COLOR = (80,80,80)

class Fase1:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.width, self.height = screen.get_size()
        
        # Estado do jogador
        self.player_rect = pygame.Rect(50, 50, 64, 96)
        self.facing_left = False
        self.facing = "down"

        # --- SPRITES DO JOGADOR ---
        self._images_ok = False
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            player_dir = os.path.join(module_dir, "assets", "player")
            idle_path = os.path.join(player_dir, "idle.png")
            walk_paths = [os.path.join(player_dir, f"walk_{i}.png") for i in range(4)]

            self.player_dir = {}
            dir_files = {
                "down": "walk_0down.png",
                "up": "walk_0up.png",
                "left": "walk_0left.png",
                "right": "walk_0right.png",
            }
            for d, fn in dir_files.items():
                p = os.path.join(player_dir, fn)
                if os.path.exists(p):
                    self.player_dir[d] = pygame.image.load(p).convert_alpha()

            self.player_idle_dir = {}
            idle_files = {
                "down": "idledown.png",
                "up": "idleup.png",
                "left": "idleleft.png",
                "right": "idleright.png",
            }
            for d, fn in idle_files.items():
                p = os.path.join(player_dir, fn)
                if os.path.exists(p):
                    self.player_idle_dir[d] = pygame.image.load(p).convert_alpha()

            self.player_walk_dir = {}
            for d in ["down","up","left","right"]:
                frames = []
                for i in range(3):
                    p = os.path.join(player_dir, f"walk_{i}{d}.png")
                    if os.path.exists(p):
                        frames.append(pygame.image.load(p).convert_alpha())
                if frames:
                    self.player_walk_dir[d] = frames

            if os.path.exists(idle_path):
                self.player_idle = pygame.image.load(idle_path).convert_alpha()
            else:
                if "down" in self.player_idle_dir:
                    self.player_idle = self.player_idle_dir["down"]
                elif "down" in self.player_dir:
                    self.player_idle = self.player_dir["down"]
                else:
                    raise FileNotFoundError("idle not found")

            self.player_walk = []
            for p in walk_paths:
                if os.path.exists(p):
                    self.player_walk.append(pygame.image.load(p).convert_alpha())

            if len(self.player_walk) >= 1:
                self._images_ok = True
            else:
                self._images_ok = True
                self.player_walk = [self.player_idle]

            for k in list(self.player_dir.keys()):
                self.player_dir[k] = self._trim_sprite(self.player_dir[k])

            for k in list(self.player_idle_dir.keys()):
                self.player_idle_dir[k] = self._trim_sprite(self.player_idle_dir[k])

            for k in list(self.player_walk_dir.keys()):
                self.player_walk_dir[k] = [self._trim_sprite(s) for s in self.player_walk_dir[k]]

            if self.player_idle is not None:
                self.player_idle = self._trim_sprite(self.player_idle)

            self.player_walk = [self._trim_sprite(s) for s in self.player_walk]

            all_sprites = []
            all_sprites += list(self.player_dir.values())
            all_sprites += list(self.player_idle_dir.values())
            for frames in self.player_walk_dir.values():
                all_sprites += list(frames)
            if self.player_idle is not None:
                all_sprites.append(self.player_idle)
            for s in self.player_walk:
                all_sprites.append(s)

            if all_sprites:
                self.base_w = max(s.get_width() for s in all_sprites)
                self.base_h = max(s.get_height() for s in all_sprites)
            else:
                self.base_w = 1
                self.base_h = 1

        except Exception:
            self._images_ok = False
            self.player_idle = None
            self.player_walk = []
            self.player_dir = {}
            self.player_idle_dir = {}
            self.player_walk_dir = {}
            self.base_w = 1
            self.base_h = 1

        self.player_frame = 0
        self.player_anim_timer = 0.0
        self.player_anim_speed = 0.12
        self.player_moving = False
        self._prev_facing = self.facing
        # --------------------------------------------

        # PAPER: múltiplos possíveis esconderijos
        self.hiding_spots = [
            pygame.Rect(150, 420, 40, 24),
            pygame.Rect(260, 440, 40, 24),
            pygame.Rect(380, 410, 40, 24),
            pygame.Rect(520, 380, 40, 24),
            pygame.Rect(720, 430, 40, 24),
        ]
        self.hiding_spot = random.choice(self.hiding_spots)

        self.paper_rect = pygame.Rect(800, 100, 60, 40)
        self.paper_hidden = True
        self.paper_opened = False
        self.code = str(random.randint(1000, 9999))
        self.has_seen_code = False

        # COFRE
        self.safe_rect = pygame.Rect(self.width - 16 - 140, self.height - 16 - 140, 140, 140)

        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            cofre_path = os.path.join(module_dir, "assets", "cofre.png")
            self.cofre_img = pygame.image.load(cofre_path).convert_alpha() if os.path.exists(cofre_path) else None
        except Exception:
            self.cofre_img = None

        self.level_timer = 45.0
        self.safe_open_requirement = 1.5
        self.safe_processing = False
        self.safe_timer = 0.0

        # teclado/entrada
        self.entering_code = False
        self.typed_code = ""
        self.max_code_len = 6
        self.has_key = False

        # paredes
        self.walls = [
            pygame.Rect(300, 20, 20, 400),
            pygame.Rect(600, 200, 400, 20),
            pygame.Rect(0, 0, self.width, 16),
            pygame.Rect(0, self.height-16, self.width, 16),
            pygame.Rect(0, 0, 16, self.height),
            pygame.Rect(self.width-16, 0, 16, self.height)
        ]

        self._prev_num_keys = set()

        # --- SOM DO CRONÔMETRO ---
        self.timer_sound = None
        self.timer_channel = None  
        self.timer_base_volume = 0.18
        self.timer_max_volume = 1.0
        self._initial_level_timer = self.level_timer

        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            cron_path = os.path.join(module_dir, "assets", "cronometro.mp3")

            if os.path.exists(cron_path) and pygame.mixer.get_init():
                try:
                    self.timer_sound = pygame.mixer.Sound(cron_path)
                    self.timer_sound.set_volume(self.timer_base_volume)
                    self.timer_channel = self.timer_sound.play(loops=-1)
                except Exception as e:
                    print("Fase1: erro ao carregar/tocar cronometro:", e)
                    self.timer_sound = None
                    self.timer_channel = None

        except Exception as e:
            print("Fase1: erro ao configurar timer_sound:", e)
            self.timer_sound = None
        # ----------------------------------------

    def _trim_sprite(self, surf):
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

    def draw_text(self, txt, x, y, color=WHITE):
        surf = self.font.render(txt, True, color)
        self.screen.blit(surf, (x, y))

    def _handle_numeric_input(self):
        keys = pygame.key.get_pressed()

        num_keys = {
            pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3", pygame.K_4: "4",
            pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7", pygame.K_8: "8", pygame.K_9: "9",
            pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2", pygame.K_KP3: "3", pygame.K_KP4: "4",
            pygame.K_KP5: "5", pygame.K_KP6: "6", pygame.K_KP7: "7", pygame.K_KP8: "8", pygame.K_KP9: "9",
        }

        enter_pressed = False
        esc_pressed = False

        for k, ch in num_keys.items():
            if keys[k] and (k not in self._prev_num_keys):
                if len(self.typed_code) < self.max_code_len:
                    self.typed_code += ch

        if keys[pygame.K_BACKSPACE] and (pygame.K_BACKSPACE not in self._prev_num_keys):
            if self.typed_code:
                self.typed_code = self.typed_code[:-1]

        if keys[pygame.K_RETURN] and (pygame.K_RETURN not in self._prev_num_keys):
            enter_pressed = True
        if keys[pygame.K_ESCAPE] and (pygame.K_ESCAPE not in self._prev_num_keys):
            esc_pressed = True

        interested = set(list(num_keys.keys()) + [
            pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_ESCAPE
        ])
        self._prev_num_keys = {k for k in interested if keys[k]}

        return enter_pressed, esc_pressed

    def update(self, dt):
        # decrementa tempo
        self.level_timer -= dt

        # atualiza volume do cronômetro
        if self.timer_sound and self._initial_level_timer > 0:
            progress = max(0.0, min(1.0, (self._initial_level_timer - self.level_timer) / self._initial_level_timer))
            eased = (math.exp(4.2 * progress) - 1.0) / (math.exp(4.2) - 1.0)
            volume = self.timer_base_volume + (self.timer_max_volume - self.timer_base_volume) * eased
            self.timer_sound.set_volume(max(0.0, min(1.0, volume)))

        if self.level_timer <= 0:
            if self.timer_channel:
                self.timer_channel.stop()
            return "LOSE_TIME"

        keys = pygame.key.get_pressed()
        dx = dy = 0
        speed = 220

        # trava movimento enquanto digita a senha
        if not self.entering_code:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1

        # atualiza facing com base em dx
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

        if dx or dy:
            mag = math.hypot(dx, dy)
            if mag != 0:  
                self.player_rect.x += (dx/mag) * speed * dt
                for w in self.walls:
                    if self.player_rect.colliderect(w):
                        if dx > 0: self.player_rect.right = w.left
                        if dx < 0: self.player_rect.left = w.right

                if self.player_rect.colliderect(self.safe_rect):
                    if dx > 0:
                        self.player_rect.right = self.safe_rect.left
                    elif dx < 0:
                        self.player_rect.left = self.safe_rect.right
                
                self.player_rect.y += (dy/mag) * speed * dt
                for w in self.walls:
                    if self.player_rect.colliderect(w):
                        if dy > 0: self.player_rect.bottom = w.top
                        if dy < 0: self.player_rect.top = w.bottom

                if self.player_rect.colliderect(self.safe_rect):
                    if dy > 0:
                        self.player_rect.bottom = self.safe_rect.top
                    elif dy < 0:
                        self.player_rect.top = self.safe_rect.bottom

        self.player_moving = (dx != 0 or dy != 0)

        if self.paper_hidden and self.player_rect.colliderect(self.hiding_spot):
            if keys[pygame.K_SPACE]:
                self.paper_hidden = False
                self.paper_opened = True
                self.has_seen_code = True

        if self.player_rect.colliderect(self.safe_rect.inflate(28, 28)):
            if not self.entering_code and keys[pygame.K_SPACE] and self.has_seen_code:
                self.entering_code = True
                self.typed_code = ""

        if self.entering_code and not self.safe_processing:
            enter_pressed, esc_pressed = self._handle_numeric_input()
            if esc_pressed:
                self.entering_code = False
            if enter_pressed:
                self.safe_processing = True
                self.safe_timer = 0.0

        if self.safe_processing:
            self.safe_timer += dt
            if self.safe_timer >= self.safe_open_requirement:
                self.safe_processing = False
                if self.typed_code == self.code:
                    if self.timer_channel:
                        self.timer_channel.stop()
                    return "NEXT"
                else:
                    self.typed_code = ""
                    self.entering_code = False
                    self.level_timer = max(0.0, self.level_timer - 4.0)

        if self._images_ok:
            if self.player_moving:
                if self.facing != self._prev_facing:
                    self.player_frame = 0
                    self.player_anim_timer = 0.0
                    self._prev_facing = self.facing

                self.player_anim_timer += dt
                if self.player_anim_timer >= self.player_anim_speed:
                    self.player_anim_timer = 0.0
                    frames = self.player_walk_dir.get(self.facing, self.player_walk)
                    self.player_frame = (self.player_frame + 1) % len(frames)
            else:
                self.player_frame = 0
                self.player_anim_timer = 0.0

        return None

    def draw(self):
        for w in self.walls:
            pygame.draw.rect(self.screen, WALL_COLOR, w)

        for spot in self.hiding_spots:
            pygame.draw.rect(self.screen, (20,25,25), spot)

        # mensagem contextual de procura
        if self.paper_hidden:
            for spot in self.hiding_spots:
                if self.player_rect.colliderect(spot.inflate(20, 20)):
                    self.draw_text(
                        "Aperte SPACE / ESPAÇO para procurar",
                        20,
                        self.height - 90,
                        HINT_COLOR
                    )
                    break

        if not self.paper_hidden:
            pygame.draw.rect(self.screen, PAPER_COLOR, self.paper_rect)
            if self.paper_opened:
                self.draw_text("SENHA:", self.paper_rect.x + 6, self.paper_rect.y + 6, (0,0,0))
                self.draw_text(self.code, self.paper_rect.x + 6, self.paper_rect.y + 24, (0,0,0))

        # Substitui retângulo do cofre pela imagem (fallback para retângulo se imagem ausente)
        if getattr(self, "cofre_img", None):
            try:
                cofre_scaled = pygame.transform.scale(
                    self.cofre_img,
                    (self.safe_rect.width, self.safe_rect.height)
                )
                self.screen.blit(cofre_scaled, self.safe_rect.topleft)
            except Exception:
                pygame.draw.rect(self.screen, SAFE_COLOR, self.safe_rect)
        else:
            pygame.draw.rect(self.screen, SAFE_COLOR, self.safe_rect)

        self.draw_text("COFRE", self.safe_rect.x-5, self.safe_rect.y-25)

        # --- DESENHO DO JOGADOR: sprite se possível, senão retângulo  ---
        if self._images_ok and (self.player_idle is not None):
            if self.player_moving:
                frames = self.player_walk_dir.get(self.facing)
                if frames:
                    sprite = frames[self.player_frame % len(frames)]
                elif self.facing in self.player_dir:
                    sprite = self.player_dir[self.facing]
                else:
                    sprite = self.player_walk[self.player_frame]
            else:
                sprite = self.player_idle_dir.get(self.facing, self.player_dir.get(self.facing, self.player_idle))

            w, h = sprite.get_size()
            scale = min(self.player_rect.width / self.base_w, self.player_rect.height / self.base_h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

            try:
                sprite_scaled = pygame.transform.smoothscale(sprite, new_size)
            except Exception:
                sprite_scaled = pygame.transform.scale(sprite, new_size)

            #flip horizontal quando estiver virado à esquerda 
            if self.facing_left and (self.facing not in self.player_dir) and (self.facing not in self.player_idle_dir):
                sprite_scaled = pygame.transform.flip(sprite_scaled, True, False)

            x = self.player_rect.centerx - sprite_scaled.get_width() // 2
            y = self.player_rect.centery - sprite_scaled.get_height() // 2
            self.screen.blit(sprite_scaled, (x, y))
        else:
            pygame.draw.rect(self.screen, (200,60,80), self.player_rect)
        # ------------------------------------------------------------------------------

        if self.player_rect.colliderect(self.safe_rect.inflate(28,28)):
            if not self.has_seen_code:
                self.draw_text("Procure um papel escondido para ver a senha", 20, self.height-60, HINT_COLOR)
            elif not self.entering_code:
                self.draw_text("Pressione SPACE perto do COFRE para digitar a senha", 20, self.height-60, HINT_COLOR)
            else:
                self.draw_text("Digite números (Backspace apaga). ENTER para confirmar. ESC para cancelar.", 20, self.height-60, HINT_COLOR)
                self.draw_text(f"> {self.typed_code}", 20, self.height-90, WHITE)

        if self.safe_processing:
            prog = (self.safe_timer / self.safe_open_requirement) * 200
            pygame.draw.rect(self.screen, WHITE, (self.width//2-100, self.height-80, 200, 15), 2)
            pygame.draw.rect(self.screen, HINT_COLOR, (self.width//2-100, self.height-80, prog, 15))

        self.draw_text(f"TEMPO: {int(self.level_timer)}s", self.width//2 - 40, 30, ALARM_COLOR)
