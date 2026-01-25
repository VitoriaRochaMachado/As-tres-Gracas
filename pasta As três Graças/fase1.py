import pygame
import math
import random

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
        self.player_rect = pygame.Rect(50, 50, 28, 36)

        # PAPER: múltiplos possíveis esconderijos (mats). A chave ficará em UM deles, escolhido aleatoriamente.
        # Nota: mantive a posição de exibição do papel quando aberto (paper_rect) igual ao original.
        self.hiding_spots = [
            pygame.Rect(150, 420, 40, 24),
            pygame.Rect(260, 440, 40, 24),
            pygame.Rect(380, 410, 40, 24),
            pygame.Rect(520, 380, 40, 24),
            pygame.Rect(720, 430, 40, 24),
        ]
        # escolhe aleatoriamente qual spot contém o papel nessa execução
        self.hiding_spot = random.choice(self.hiding_spots)

        self.paper_rect = pygame.Rect(800, 100, 60, 40)    # posição de exibição do papel quando aberto
        self.paper_hidden = True       # inicialmente escondido
        self.paper_opened = False      # abriu para ver a senha
        self.code = str(random.randint(1000, 9999))  # código gerado aleatoriamente 4 dígitos
        self.has_seen_code = False     # se o jogador viu a senha (abaixo usado para permitir digitar)

        # SAFE / COFRE
        self.safe_rect = pygame.Rect(500, 500, 50, 50)
        self.level_timer = 45.0
        self.safe_open_requirement = 1.5  # tempo de "processamento" após submeter
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
            # Bordas
            pygame.Rect(0, 0, self.width, 16),
            pygame.Rect(0, self.height-16, self.width, 16),
            pygame.Rect(0, 0, 16, self.height),
            pygame.Rect(self.width-16, 0, 16, self.height)
        ]

        # prev keys (para detecção de transição press -> released)
        self._prev_num_keys = set()

    def draw_text(self, txt, x, y, color=WHITE):
        surf = self.font.render(txt, True, color)
        self.screen.blit(surf, (x, y))

    def _handle_numeric_input(self):
        """
        Detecta transições not-pressed -> pressed para números, backspace, enter e esc.
        Retorna (enter_pressed, esc_pressed).
        Deve ser chamado *uma vez por frame* quando self.entering_code == True e
        self.safe_processing == False.
        """
        keys = pygame.key.get_pressed()

        num_keys = {
            pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3", pygame.K_4: "4",
            pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7", pygame.K_8: "8", pygame.K_9: "9",
            pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2", pygame.K_KP3: "3", pygame.K_KP4: "4",
            pygame.K_KP5: "5", pygame.K_KP6: "6", pygame.K_KP7: "7", pygame.K_KP8: "8", pygame.K_KP9: "9",
        }

        enter_pressed = False
        esc_pressed = False

        # detectar novos pressionamentos para números
        for k, ch in num_keys.items():
            if keys[k] and (k not in self._prev_num_keys):
                if len(self.typed_code) < self.max_code_len:
                    self.typed_code += ch

        # Backspace por transição
        if keys[pygame.K_BACKSPACE] and (pygame.K_BACKSPACE not in self._prev_num_keys):
            if self.typed_code:
                self.typed_code = self.typed_code[:-1]

        # Enter / Escape por transição
        if keys[pygame.K_RETURN] and (pygame.K_RETURN not in self._prev_num_keys):
            enter_pressed = True
        if keys[pygame.K_ESCAPE] and (pygame.K_ESCAPE not in self._prev_num_keys):
            esc_pressed = True

        # atualiza prev keys: mantemos apenas teclas relevantes
        interested = set(list(num_keys.keys()) + [pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_ESCAPE])
        new_prev = set(k for k in interested if keys[k])
        self._prev_num_keys = new_prev

        return enter_pressed, esc_pressed

    def update(self, dt):
        self.level_timer -= dt
        if self.level_timer <= 0:
            return "LOSE_TIME"

        keys = pygame.key.get_pressed()
        dx = dy = 0
        speed = 220
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1
        
        if dx != 0 or dy != 0:
            mag = math.hypot(dx, dy)
            self.player_rect.x += (dx/mag) * speed * dt
            for w in self.walls:
                if self.player_rect.colliderect(w):
                    if dx > 0: self.player_rect.right = w.left
                    if dx < 0: self.player_rect.left = w.right
            
            self.player_rect.y += (dy/mag) * speed * dt
            for w in self.walls:
                if self.player_rect.colliderect(w):
                    if dy > 0: self.player_rect.bottom = w.top
                    if dy < 0: self.player_rect.top = w.bottom

        # Lógica do papel escondido: abrir com SPACE no hiding_spot escolhido aleatoriamente
        if self.paper_hidden and self.player_rect.colliderect(self.hiding_spot):
            if keys[pygame.K_SPACE]:
                self.paper_hidden = False
                self.paper_opened = True
                self.has_seen_code = True

        # Interação com o cofre: apertar SPACE perto do cofre para entrar em modo digitar (se já viu a senha)
        if self.player_rect.colliderect(self.safe_rect.inflate(28, 28)):
            if not self.entering_code and keys[pygame.K_SPACE] and self.has_seen_code:
                self.entering_code = True
                self.typed_code = ""

        # Se estiver no modo de digitar e nao em processamento, processa entrada
        if self.entering_code and not self.safe_processing:
            enter_pressed, esc_pressed = self._handle_numeric_input()

            if esc_pressed:
                # sair do modo digitar
                self.entering_code = False

            if enter_pressed:
                # inicia processamento
                self.safe_processing = True
                self.safe_timer = 0.0

        # PROCESSAMENTO do cofre
        if self.safe_processing:
            self.safe_timer += dt
            if self.safe_timer >= self.safe_open_requirement:
                self.safe_processing = False
                # verificar código
                if self.typed_code == self.code:
                    # sucesso: o jogador "pega a chave"
                    self.has_key = True
                    return "NEXT"
                else:
                    # falha: reset e feedback (pode digitar de novo)
                    self.typed_code = ""
                    self.entering_code = False
                    # penalidade de tempo
                    self.level_timer = max(0.0, self.level_timer - 4.0)

        return None

    def draw(self):
        for w in self.walls: pygame.draw.rect(self.screen, WALL_COLOR, w)
        
        # desenhar todos os esconderijos (mats) - pista sutil em cada um
        for spot in self.hiding_spots:
            pygame.draw.rect(self.screen, (90,50,30), spot)
            # mesma pista em cada ponto de procura
            self.draw_text("Piso solto?", spot.x - 4, spot.y - 18, HINT_COLOR)

        # papel: se aberto, desenha papel com a senha visível
        if not self.paper_hidden:
            pygame.draw.rect(self.screen, PAPER_COLOR, self.paper_rect)
            if self.paper_opened:
                self.draw_text("SENHA:", self.paper_rect.x + 6, self.paper_rect.y + 6, (0,0,0))
                self.draw_text(self.code, self.paper_rect.x + 6, self.paper_rect.y + 24, (0,0,0))

        # cofre
        pygame.draw.rect(self.screen, SAFE_COLOR, self.safe_rect)
        self.draw_text("COFRE", self.safe_rect.x-5, self.safe_rect.y-25)
        
        # jogador
        pygame.draw.rect(self.screen, (200,60,80), self.player_rect)

        # UI do modo digitar
        if self.player_rect.colliderect(self.safe_rect.inflate(28,28)):
            if not self.has_seen_code:
                self.draw_text("Procure um papel escondido para ver a senha", 20, self.height-60, HINT_COLOR)
            else:
                if not self.entering_code:
                    self.draw_text("Pressione SPACE perto do COFRE para digitar a senha", 20, self.height-60, HINT_COLOR)
                else:
                    self.draw_text("Digite números (Backspace apaga). ENTER para confirmar. ESC para cancelar.", 20, self.height-60, HINT_COLOR)
                    self.draw_text(f"> {self.typed_code}", 20, self.height-90, WHITE)

        # barra de processamento do cofre
        if self.safe_processing:
            prog = (self.safe_timer / self.safe_open_requirement) * 200
            pygame.draw.rect(self.screen, WHITE, (self.width//2-100, self.height-80, 200, 15), 2)
            pygame.draw.rect(self.screen, HINT_COLOR, (self.width//2-100, self.height-80, prog, 15))

        # HUD timer
        self.draw_text(f"TEMPO: {int(self.level_timer)}s", self.width//2 - 40, 30, ALARM_COLOR)
