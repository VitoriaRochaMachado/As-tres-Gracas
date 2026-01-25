import os
import pygame
import sys

from fase1 import Fase1
import fase2  # NÃO renomeie nada

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def asset_path(*parts):
    return os.path.join(BASE_DIR, *parts)

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1024, 640
FPS = 60


# ---------------- TUTORIAL ----------------
def mostrar_tutorial(screen, clock):
    font = pygame.font.SysFont("consolas", 22)
    lines = [
        "OBJETIVO:",
        "Infiltre-se e recupere a estatueta.",
        "",
        "CONTROLES:",
        "WASD / Setas  - Mover",
        "SPACE         - Interagir / Roubar",
        "E             - Abrir portas",
        "",
        "Evite guardas e câmeras.",
        "",
        "Pressione ENTER para voltar ao menu."
    ]

    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

        screen.fill((15, 15, 20))
        y = 80
        for l in lines:
            txt = font.render(l, True, (235,235,220))
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
            y += 32

        pygame.display.flip()


# ---------------- GAME OVER DISPLAY ----------------
def mostrar_game_over(screen, clock, bg):
    font = pygame.font.SysFont("consolas", 28)
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    return True
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        if bg:
            screen.blit(bg, (0,0))
        else:
            screen.fill((35,8,8))
            t = font.render("GAME OVER", True, (220,60,60))
            screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 60))

        instr = font.render("APERTE R PARA VOLTAR AO INÍCIO", True, (235,235,220))
        screen.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT - 80))
        pygame.display.flip()


# ---------------- VICTORY DISPLAY ----------------
def mostrar_victory(screen, clock, bg, title, msg):
    font = pygame.font.SysFont("consolas", 28)
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    return True
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        if bg:
            screen.blit(bg, (0,0))
        else:
            screen.fill((18,80,30))
            t = font.render(title or "MISSÃO CONCLUÍDA", True, (235,235,220))
            screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 60))
            m = font.render(msg or "", True, (200,240,200))
            screen.blit(m, (WIDTH//2 - m.get_width()//2, HEIGHT//2 - 10))

        instr = font.render("APERTE R PARA VOLTAR AO INÍCIO", True, (235,235,220))
        screen.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT - 80))
        pygame.display.flip()


# ---------------- MENU INICIAL (COM SOM) ----------------
def tela_inicial(screen, clock):
    try:
        bg = pygame.image.load(asset_path("assets", "menu_inicial.png")).convert()
        bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    except Exception:
        bg = None

    # som (fallback silencioso)
    try:
        pygame.mixer.init()
        hover_sound = pygame.mixer.Sound(asset_path("assets", "clicar.mp3"))
        click_sound = pygame.mixer.Sound(asset_path("assets", "clicar.mp3"))
    except Exception:
        hover_sound = None
        click_sound = None

    font = pygame.font.SysFont("consolas", 28)

    BTN_BG = (18,20,28)
    BTN_BG_HOVER = (28,32,44)
    BTN_BORDER = (200,190,160)
    BTN_HOVER = (235,225,190)
    TXT = (235,235,220)

    btn_w, btn_h = 260, 52
    base_y = HEIGHT - 260
    gap = 65

    start = pygame.Rect(WIDTH//2 - btn_w//2, base_y, btn_w, btn_h)
    tuto  = pygame.Rect(WIDTH//2 - btn_w//2, base_y+gap, btn_w, btn_h)
    sair  = pygame.Rect(WIDTH//2 - btn_w//2, base_y+gap*2, btn_w, btn_h)

    hovered_last = None

    def draw(rect, text, hover):
        pygame.draw.rect(screen, BTN_BG_HOVER if hover else BTN_BG, rect, border_radius=6)
        pygame.draw.rect(screen, BTN_HOVER if hover else BTN_BORDER, rect, 2, border_radius=6)
        t = font.render(text, True, TXT)
        screen.blit(t, (rect.centerx - t.get_width()//2,
                        rect.centery - t.get_height()//2))

    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start.collidepoint(event.pos):
                    if click_sound: click_sound.play()
                    return "START"
                if tuto.collidepoint(event.pos):
                    if click_sound: click_sound.play()
                    return "TUTORIAL"
                if sair.collidepoint(event.pos):
                    if click_sound: click_sound.play()
                    pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if click_sound: click_sound.play()
                    return "START"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        if bg:
            screen.blit(bg,(0,0))
        else:
            screen.fill((10,10,16))

        # hover sound: toca uma vez ao entrar no botão
        for rect, name in [(start,"START"), (tuto,"TUTO"), (sair,"SAIR")]:
            if rect.collidepoint(mouse):
                if hovered_last != name and hover_sound:
                    hover_sound.play()
                hovered_last = name
                break
        else:
            hovered_last = None

        # desenha botões (usando collidepoint, sem colliderect com mouse)
        draw(start,"INICIAR", start.collidepoint(mouse))
        draw(tuto,"TUTORIAL", tuto.collidepoint(mouse))
        draw(sair,"SAIR", sair.collidepoint(mouse))

        pygame.display.flip()


# ---------------- MAIN ----------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("As Três Graças")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)

    # pré-carrega assets de fim de jogo
    try:
        GAME_OVER_BG = pygame.image.load(asset_path("assets","game_over.png")).convert()
        GAME_OVER_BG = pygame.transform.scale(GAME_OVER_BG,(WIDTH,HEIGHT))
    except Exception:
        GAME_OVER_BG = None

    try:
        VICTORY_BG = pygame.image.load(asset_path("assets","victory.png")).convert()
        VICTORY_BG = pygame.transform.scale(VICTORY_BG,(WIDTH,HEIGHT))
    except Exception:
        VICTORY_BG = None

    while True:
        # menu loop
        while True:
            choice = tela_inicial(screen, clock)
            if choice == "START": break
            if choice == "TUTORIAL":
                mostrar_tutorial(screen, clock)

        # fase 1
        fase1 = Fase1(screen, font)
        result = None

        while True:
            dt = clock.tick(FPS)/1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            result = fase1.update(dt)
            screen.fill((20,20,25))
            fase1.draw()
            pygame.display.flip()

            if result in ("NEXT","LOSE_TIME"):
                break

        if result == "LOSE_TIME":
            # se perder na fase1, mostra sua tela de game over e volta ao menu
            mostrar_game_over(screen, clock, GAME_OVER_BG)
            continue

        # Antes de chamar a Fase 2, injetamos um proxy seguro em fase2.show_end_screen
        # que distingue vitória de derrota pelo `title` passado.
        try:
            def _proxy_show_end_screen(title, msg, color):
                t = (title or "").upper()

                # derrota
                if ("GAME" in t) or ("OVER" in t):
                    # mostra game over com sua arte
                    return mostrar_game_over(screen, clock, GAME_OVER_BG)

                # vitória / missão concluída
                if ("MISS" in t) or ("CONCLU" in t) or ("WIN" in t) or ("VIT" in t):
                    # mostra tela de vitória (usa VICTORY_BG se existir)
                    return mostrar_victory(screen, clock, VICTORY_BG, title, msg)

                # fallback: trata como derrota
                return mostrar_game_over(screen, clock, GAME_OVER_BG)

            fase2.show_end_screen = _proxy_show_end_screen
        except Exception as e:
            print("Aviso: não foi possível sobrescrever show_end_screen em fase2:", e)

        # chama Fase 2 (sem alterar o arquivo)
        # chama Fase 2 (refatorado)
        fase2.run(screen, clock, font, BASE_DIR)



if __name__ == "__main__":
    main()
