import pygame
import math
import random
import os 

# Cores usadas na fase (pra ficar fácil reaproveitar e mudar depois)
WHITE = (240,240,240)
ALARM_COLOR = (220,20,20)
HINT_COLOR = (238, 229, 190)
SAFE_COLOR = (50, 50, 50)
PAPER_COLOR = (238, 229, 190)
WALL_COLOR = (25,25,25)

class Fase1:
    def __init__(self, screen, font):
        # referência pra desenhar na tela e escrever texto
        self.screen = screen
        self.font = font
        self.width, self.height = screen.get_size()

        # tenta carregar o piso (tile) pra repetir na tela toda
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            floor_path = os.path.join(module_dir, "assets", "piso_madeira.png")
            img = pygame.image.load(floor_path).convert()

            # deixa o tile menor (aqui dá pra mudar o tamanho do piso)
            self.floor_tile = pygame.transform.smoothscale(img, (74, 74))
        except Exception:
            self.floor_tile = None

        # overlay escuro em cima do piso, pra dar um clima mais “fechado”
        self.floor_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.floor_overlay.fill((0, 0, 0, 100))

        # tenta carregar a imagem da “caixa do timer”
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            timer_path = os.path.join(module_dir, "assets", "timer_box.png")
            self.timer_box = pygame.image.load(timer_path).convert_alpha()
        except Exception:
            self.timer_box = None


        # ---------------- JOGADOR (posição e colisão) ----------------
        self.player_rect = pygame.Rect(50, 50, 64, 96)  # onde desenha o player
        self.hitbox = self.player_rect.inflate(-30, -30)  # hitbox menor pra colisão ficar mais “justa”
        self.hitbox.midbottom = self.player_rect.midbottom
        self.facing_left = False
        self.facing = "down"

        # ---------------- SPRITES DO JOGADOR ----------------
        # tenta carregar sprites (se falhar, o jogo usa retângulo)
        self._images_ok = False
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            player_dir = os.path.join(module_dir, "assets", "player")
            idle_path = os.path.join(player_dir, "idle.png")
            walk_paths = [os.path.join(player_dir, f"walk_{i}.png") for i in range(4)]

            # sprites “simples” por direção (fallback)
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

            # sprites idle por direção
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

            # sprites de caminhada por direção (3 frames)
            self.player_walk_dir = {}
            for d in ["down","up","left","right"]:
                frames = []
                for i in range(3):
                    p = os.path.join(player_dir, f"walk_{i}{d}.png")
                    if os.path.exists(p):
                        frames.append(pygame.image.load(p).convert_alpha())
                if frames:
                    self.player_walk_dir[d] = frames

            # tenta pegar um idle geral
            if os.path.exists(idle_path):
                self.player_idle = pygame.image.load(idle_path).convert_alpha()
            else:
                # fallback: pega idle down, ou walk down, senão dá erro
                if "down" in self.player_idle_dir:
                    self.player_idle = self.player_idle_dir["down"]
                elif "down" in self.player_dir:
                    self.player_idle = self.player_dir["down"]
                else:
                    raise FileNotFoundError("idle not found")

            # sprites “walk_0.png...walk_3.png” (fallback geral)
            self.player_walk = []
            for p in walk_paths:
                if os.path.exists(p):
                    self.player_walk.append(pygame.image.load(p).convert_alpha())

            # se não tiver walk, usa o idle como walk pra não quebrar
            if len(self.player_walk) >= 1:
                self._images_ok = True
            else:
                self._images_ok = True
                self.player_walk = [self.player_idle]

            # corta transparência em volta (pra sprite ficar “encaixada” melhor)
            for k in list(self.player_dir.keys()):
                self.player_dir[k] = self._trim_sprite(self.player_dir[k])

            for k in list(self.player_idle_dir.keys()):
                self.player_idle_dir[k] = self._trim_sprite(self.player_idle_dir[k])

            for k in list(self.player_walk_dir.keys()):
                self.player_walk_dir[k] = [self._trim_sprite(s) for s in self.player_walk_dir[k]]

            if self.player_idle is not None:
                self.player_idle = self._trim_sprite(self.player_idle)

            self.player_walk = [self._trim_sprite(s) for s in self.player_walk]

            # calcula um “tamanho base” dos sprites pra fazer scale proporcional
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
            # se qualquer coisa der errado, desativa sprites e usa retângulo
            self._images_ok = False
            self.player_idle = None
            self.player_walk = []
            self.player_dir = {}
            self.player_idle_dir = {}
            self.player_walk_dir = {}
            self.base_w = 1
            self.base_h = 1

        # controle de animação
        self.player_frame = 0
        self.player_anim_timer = 0.0
        self.player_anim_speed = 0.12
        self.player_moving = False
        self._prev_facing = self.facing
        # ------------------------------------------------------------

        # ---------------- PAPEL (onde pode estar escondido) ----------------
        # lista de lugares possíveis pra procurar o papel
        self.hiding_spots = [
            pygame.Rect(120, 120, 40, 24),
            pygame.Rect(220, 160, 40, 24),
            pygame.Rect(260, 320, 40, 24),
            pygame.Rect(180, 520, 40, 24),
            pygame.Rect(420, 140, 40, 24),
            pygame.Rect(520, 180, 40, 24),
            pygame.Rect(460, 320, 40, 24),
            pygame.Rect(620, 520, 40, 24),
            pygame.Rect(820, 140, 40, 24),
            pygame.Rect(880, 360, 40, 24),
        ]

        # escolhe aleatório onde o papel vai estar
        self.hiding_spot = random.choice(self.hiding_spots)
        self.paper_rect = pygame.Rect(self.hiding_spot.x, self.hiding_spot.y, 85, 50)
        self.paper_hidden = True         # ainda não achou
        self.paper_opened = False        # abriu (mostra senha)
        self.code = str(random.randint(1000, 9999))  # senha aleatória
        self.has_seen_code = False       # só pode digitar depois de ver a senha

        # ---------------- COFRE ----------------
        # cofre fica no canto inferior direito
        self.safe_rect = pygame.Rect(self.width - 16 - 140, self.height - 16 - 140, 140, 140)

        # tenta carregar imagem do cofre
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            cofre_path = os.path.join(module_dir, "assets", "cofre.png")
            self.cofre_img = pygame.image.load(cofre_path).convert_alpha() if os.path.exists(cofre_path) else None
        except Exception:
            self.cofre_img = None

        # ---------------- TEMPO / INTERAÇÃO COM COFRE ----------------
        self.level_timer = 45.0               # tempo total da fase
        self.safe_open_requirement = 1.5      # tempo “processando” ao apertar ENTER
        self.safe_processing = False
        self.safe_timer = 0.0

        # entrada da senha
        self.entering_code = False
        self.typed_code = ""
        self.max_code_len = 6
        self.has_key = False  # parece sobrar, mas deixa pronto caso use depois

        # ---------------- PAREDES (colisão) ----------------
        # são retângulos que formam o labirinto / sala
        self.walls = [
            # bordas
            pygame.Rect(0, 0, self.width, 16),
            pygame.Rect(0, self.height-16, self.width, 16),
            pygame.Rect(0, 0, 16, self.height),
            pygame.Rect(self.width-16, 0, 16, self.height),

            # parede vertical principal (porta MUITO larga)
            pygame.Rect(340, 16, 20, 210),
            pygame.Rect(320, 420, 20, self.height-16-420),

            # parede horizontal superior (porta larga no centro)
            pygame.Rect(340, 220, 220, 20),
            pygame.Rect(720, 220, (self.width-16) - 720, 20),

            # parede vertical direita (porta muito larga)
            pygame.Rect(740, 240, 20, 140),
            pygame.Rect(740, 560, 20, (self.height-16) - 560),

            # parede horizontal inferior (deixa corredor largo — sem “dente”)
            pygame.Rect(340, 420, 260, 20),
        ]

        # remove esconderijos que encostam em paredes (pra não ficar impossível)
        self.hiding_spots = [r for r in self.hiding_spots if not any(r.colliderect(w) for w in self.walls)]
        if len(self.hiding_spots) == 0:
            self.hiding_spots = [pygame.Rect(120, 120, 40, 24)]
        self.hiding_spot = random.choice(self.hiding_spots)

        # guarda teclas numéricas anteriores pra evitar repetir quando segura a tecla
        self._prev_num_keys = set()

        # ---------------- SOM DO CRONÔMETRO ----------------
        self.timer_sound = None
        self.timer_channel = None  
        self.timer_base_volume = 0.18
        self.timer_max_volume = 1.0
        self._initial_level_timer = self.level_timer

        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            cron_path = os.path.join(module_dir, "assets", "cronometro.mp3")

            # só toca se o mixer estiver ativo e o arquivo existir
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
        # ----------------------------------------------------

    def _trim_sprite(self, surf):
        # recorta área transparente em volta do sprite (melhora o scale/posicionamento)
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
        # helper simples pra renderizar texto
        surf = self.font.render(txt, True, color)
        self.screen.blit(surf, (x, y))

    def _handle_numeric_input(self):
        # lê teclado pra digitar números, backspace, enter e esc
        keys = pygame.key.get_pressed()

        num_keys = {
            pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3", pygame.K_4: "4",
            pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7", pygame.K_8: "8", pygame.K_9: "9",
            pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2", pygame.K_KP3: "3", pygame.K_KP4: "4",
            pygame.K_KP5: "5", pygame.K_KP6: "6", pygame.K_KP7: "7", pygame.K_KP8: "8", pygame.K_KP9: "9",
        }

        enter_pressed = False
        esc_pressed = False

        # adiciona número só quando a tecla “acabou de ser pressionada”
        for k, ch in num_keys.items():
            if keys[k] and (k not in self._prev_num_keys):
                if len(self.typed_code) < self.max_code_len:
                    self.typed_code += ch

        # backspace apaga um caractere
        if keys[pygame.K_BACKSPACE] and (pygame.K_BACKSPACE not in self._prev_num_keys):
            if self.typed_code:
                self.typed_code = self.typed_code[:-1]

        # enter confirma e esc cancela
        if keys[pygame.K_RETURN] and (pygame.K_RETURN not in self._prev_num_keys):
            enter_pressed = True
        if keys[pygame.K_ESCAPE] and (pygame.K_ESCAPE not in self._prev_num_keys):
            esc_pressed = True

        # atualiza o conjunto de teclas que estão pressionadas agora
        interested = set(list(num_keys.keys()) + [
            pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_ESCAPE
        ])
        self._prev_num_keys = {k for k in interested if keys[k]}

        return enter_pressed, esc_pressed

    def update(self, dt):
        # diminui o tempo da fase
        self.level_timer -= dt

        # aumenta o volume do som do cronômetro conforme o tempo vai acabando
        if self.timer_sound and self._initial_level_timer > 0:
            progress = max(0.0, min(1.0, (self._initial_level_timer - self.level_timer) / self._initial_level_timer))
            eased = (math.exp(4.2 * progress) - 1.0) / (math.exp(4.2) - 1.0)
            volume = self.timer_base_volume + (self.timer_max_volume - self.timer_base_volume) * eased
            self.timer_sound.set_volume(max(0.0, min(1.0, volume)))

        # se o tempo acabou, perde a fase
        if self.level_timer <= 0:
            if self.timer_channel:
                self.timer_channel.stop()
            return "LOSE_TIME"

        keys = pygame.key.get_pressed()
        dx = dy = 0
        speed = 220

        # enquanto está digitando, trava o movimento
        if not self.entering_code:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1

        # atualiza direção do personagem (pra escolher sprite certo)
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

        # movimentação com normalização (pra diagonal não ser mais rápida)
        if dx or dy:
            mag = math.hypot(dx, dy)
            if mag != 0:
                # move no eixo X e resolve colisão com paredes e cofre
                self.hitbox.x += (dx/mag) * speed * dt
                for w in self.walls:
                    if self.hitbox.colliderect(w):
                        if dx > 0: self.hitbox.right = w.left
                        if dx < 0: self.hitbox.left = w.right

                if self.hitbox.colliderect(self.safe_rect):
                    if dx > 0:
                        self.hitbox.right = self.safe_rect.left
                    elif dx < 0:
                        self.hitbox.left = self.safe_rect.right

                # move no eixo Y e resolve colisão com paredes e cofre
                self.hitbox.y += (dy/mag) * speed * dt
                for w in self.walls:
                    if self.hitbox.colliderect(w):
                        if dy > 0: self.hitbox.bottom = w.top
                        if dy < 0: self.hitbox.top = w.bottom

                if self.hitbox.colliderect(self.safe_rect):
                    if dy > 0:
                        self.hitbox.bottom = self.safe_rect.top
                    elif dy < 0:
                        self.hitbox.top = self.safe_rect.bottom

                # atualiza onde desenha o player a partir da hitbox
                self.player_rect.midbottom = self.hitbox.midbottom

        self.player_moving = (dx != 0 or dy != 0)

        # se encostar no lugar certo e apertar SPACE, revela o papel e a senha
        if self.player_rect.colliderect(self.hiding_spot.inflate(20, 20)):
            if keys[pygame.K_SPACE]:
                self.paper_rect.center = self.hiding_spot.center
                self.paper_hidden = False
                self.paper_opened = True
                self.has_seen_code = True

        # perto do cofre, SPACE abre o modo de digitar (só se já viu a senha)
        if self.player_rect.colliderect(self.safe_rect.inflate(28, 28)):
            if not self.entering_code and keys[pygame.K_SPACE] and self.has_seen_code:
                self.entering_code = True
                self.typed_code = ""

        # enquanto digitando: pega teclas e decide enter/esc
        if self.entering_code and not self.safe_processing:
            enter_pressed, esc_pressed = self._handle_numeric_input()
            if esc_pressed:
                self.entering_code = False
            if enter_pressed:
                self.safe_processing = True
                self.safe_timer = 0.0

        # “processamento” do cofre (tipo um tempo abrindo)
        if self.safe_processing:
            self.safe_timer += dt
            if self.safe_timer >= self.safe_open_requirement:
                self.safe_processing = False
                if self.typed_code == self.code:
                    # acertou: passa de fase
                    if self.timer_channel:
                        self.timer_channel.stop()
                    return "NEXT"
                else:
                    # errou: limpa input e tira tempo como punição
                    self.typed_code = ""
                    self.entering_code = False
                    self.level_timer = max(0.0, self.level_timer - 4.0)

        # atualiza animação do sprite (só se tiver sprites)
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

        # se não aconteceu nada especial, continua na fase
        return None

    def draw(self):
        # desenha o piso (tile repetido) ou cor sólida se não tiver imagem
        if self.floor_tile:
            tw, th = self.floor_tile.get_width(), self.floor_tile.get_height()
            for y in range(0, self.height, th):
                for x in range(0, self.width, tw):
                    self.screen.blit(self.floor_tile, (x, y))
            self.screen.blit(self.floor_overlay, (0, 0))
        else:
            self.screen.fill((20,20,25))

        # desenha as paredes
        for w in self.walls:
            pygame.draw.rect(self.screen, WALL_COLOR, w)

        # desenha os lugares onde pode ter papel (mesmo que o papel não esteja em todos)
        for spot in self.hiding_spots:
            pygame.draw.rect(self.screen, PAPER_COLOR, spot)

        # se o papel ainda está escondido, mostra dica quando encosta num spot
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

        # se achou o papel, desenha ele e escreve a senha em cima
        if not self.paper_hidden:
            pygame.draw.rect(self.screen, PAPER_COLOR, self.paper_rect)
            if self.paper_opened:
                self.draw_text("SENHA:", self.paper_rect.x + 6, self.paper_rect.y + 6, (0,0,0))
                self.draw_text(self.code, self.paper_rect.x + 6, self.paper_rect.y + 24, (0,0,0))

        # desenha o cofre com imagem (se tiver), senão retângulo
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

        # ---------------- DESENHO DO JOGADOR ----------------
        # se tiver sprites, usa sprites; senão desenha um retângulo simples
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

            # escala mantendo proporção
            w, h = sprite.get_size()
            scale = min(self.player_rect.width / self.base_w, self.player_rect.height / self.base_h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

            try:
                sprite_scaled = pygame.transform.smoothscale(sprite, new_size)
            except Exception:
                sprite_scaled = pygame.transform.scale(sprite, new_size)

            # flip quando está virado pra esquerda (pra alguns casos de sprite)
            if self.facing_left and (self.facing not in self.player_dir) and (self.facing not in self.player_idle_dir):
                sprite_scaled = pygame.transform.flip(sprite_scaled, True, False)

            x = self.player_rect.centerx - sprite_scaled.get_width() // 2
            y = self.player_rect.centery - sprite_scaled.get_height() // 2
            self.screen.blit(sprite_scaled, (x, y))
        else:
            pygame.draw.rect(self.screen, (200,60,80), self.player_rect)
        # -----------------------------------------------------

        # dicas perto do cofre
        if self.player_rect.colliderect(self.safe_rect.inflate(28,28)):
            if not self.has_seen_code:
                self.draw_text("Procure um papel escondido para ver a senha", 20, self.height-60, HINT_COLOR)
            elif not self.entering_code:
                self.draw_text("Pressione SPACE perto do COFRE para digitar a senha", 20, self.height-60, HINT_COLOR)
            else:
                self.draw_text("Digite números (Backspace apaga). ENTER para confirmar. ESC para cancelar.", 20, self.height-60, HINT_COLOR)
                self.draw_text(f"> {self.typed_code}", 20, self.height-90, WHITE)

        # barra de progresso quando está “abrindo” o cofre
        if self.safe_processing:
            prog = (self.safe_timer / self.safe_open_requirement) * 200
            pygame.draw.rect(self.screen, WHITE, (self.width//2-100, self.height-80, 200, 15), 2)
            pygame.draw.rect(self.screen, PAPER_COLOR, (self.width//2-100, self.height-80, prog, 15))

        # desenha o timer na caixa (se existir), senão desenha o número simples
        if self.timer_box:
            box_w, box_h = 120, 110  
            box = pygame.transform.smoothscale(self.timer_box, (box_w, box_h))
            x = self.width - 16 - box_w - 12
            y = 16

            self.screen.blit(box, (x, y))

            tempo_font = pygame.font.SysFont("consolas", 30, bold=True)
            tempo_txt = tempo_font.render(f"{int(self.level_timer)}", True, (255,255,255))
            self.screen.blit(
                tempo_txt,
                (x + box_w//2 - tempo_txt.get_width()//2,
                 y + box_h//2 - tempo_txt.get_height()//2)
            )
        else:
            self.draw_text(f"{int(self.level_timer)}", self.width//2 - 40, 30, ALARM_COLOR)
