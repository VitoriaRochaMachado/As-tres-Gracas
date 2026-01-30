# main.py
# Aqui fica o “roteador” do jogo: menu -> tutorial -> fase1 -> fase2 -> fase3
import os
import pygame
import sys

from fase1 import Fase1
import fase2
import fase3 

# ---------------- PATHS ----------------
# BASE_DIR é a pasta onde o main.py está (ajuda a achar assets independente de onde roda)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def asset_path(*parts):
    # monta caminhos tipo: asset_path("assets","img.png")
    return os.path.join(BASE_DIR, *parts)

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1024, 640
FPS = 60

# som global pra usar na tela de game over
GAME_OVER_SOUND = None

# ---------------- TUTORIAL ----------------
def mostrar_tutorial(screen, clock):
    # carrega as 4 imagens do tutorial (tuto1.png até tuto4.png)
    pages = []
    try:
        for i in range(1, 5):
            img = pygame.image.load(asset_path("assets", f"tuto{i}.png")).convert_alpha()
            img = pygame.transform.scale(img, (WIDTH, HEIGHT))
            pages.append(img)
    except Exception:
        # se der erro carregando, só volta pro menu
        return

    # página atual do tutorial
    idx = 0

    # loop do tutorial (fica aqui até acabar as páginas ou apertar ESC)
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            # fechar a janela encerra o programa
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ESC sai do tutorial e volta pro menu
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

            # clique esquerdo -> próxima página (tela inteira clicável)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                idx += 1
                if idx >= len(pages):
                    # terminou o tutorial
                    return

        # desenha a página atual
        screen.blit(pages[idx], (0, 0))
        pygame.display.flip()


# ---------------- GAME OVER DISPLAY ----------------
def mostrar_game_over(screen, clock, bg):
    font = pygame.font.SysFont("consolas", 28)

    # toca o som uma vez quando entra na tela de game over (se existir)
    try:
        if GAME_OVER_SOUND:
            GAME_OVER_SOUND.play()
    except Exception:
        pass

    # loop da tela de game over
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.KEYDOWN:
                # R volta pro início (menu)
                if e.key == pygame.K_r:
                    return True
                # ESC sai do jogo
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # se tiver imagem de fundo, usa ela, senão pinta com cor e escreve texto
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

    # loop da tela de vitória
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.KEYDOWN:
                # R volta pro início
                if e.key == pygame.K_r:
                    return True
                # ESC sai do jogo
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # desenha fundo e textos
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
    # tenta carregar imagem do menu
    try:
        bg = pygame.image.load(asset_path("assets", "menu_inicial.png")).convert()
        bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    except Exception:
        bg = None

    # toca a música do menu em loop
    try:
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        inicio_music_path = asset_path("assets", "tela_inicio_som.mp3")
        if os.path.exists(inicio_music_path) and pygame.mixer.get_init() is not None:
            try:
                pygame.mixer.music.load(inicio_music_path)
                pygame.mixer.music.set_volume(0.45)
                pygame.mixer.music.play(-1)  # loop infinito enquanto estiver no menu
            except Exception:
                pass
    except Exception:
        pass

    # sons de hover/click (se não achar, só fica sem som mesmo)
    try:
        hover_sound = pygame.mixer.Sound(asset_path("assets", "clicar.mp3"))
        click_sound = pygame.mixer.Sound(asset_path("assets", "clicar.mp3"))
    except Exception:
        hover_sound = None
        click_sound = None

    font = pygame.font.SysFont("consolas", 28)

    # cores do botão
    BTN_BG = (18,20,28)
    BTN_BG_HOVER = (28,32,44)
    BTN_BORDER = (200,190,160)
    BTN_HOVER = (235,225,190)
    TXT = (235,235,220)

    # tamanho e posição dos botões
    btn_w, btn_h = 260, 52
    base_y = HEIGHT - 260
    gap = 65

    # retângulos clicáveis dos botões
    start = pygame.Rect(WIDTH//2 - btn_w//2, base_y, btn_w, btn_h)
    tuto  = pygame.Rect(WIDTH//2 - btn_w//2, base_y+gap, btn_w, btn_h)
    sair  = pygame.Rect(WIDTH//2 - btn_w//2, base_y+gap*2, btn_w, btn_h)

    hovered_last = None

    # função pra desenhar um botão (normal ou hover)
    def draw(rect, text, hover):
        pygame.draw.rect(screen, BTN_BG_HOVER if hover else BTN_BG, rect, border_radius=6)
        pygame.draw.rect(screen, BTN_HOVER if hover else BTN_BORDER, rect, 2, border_radius=6)
        t = font.render(text, True, TXT)
        screen.blit(t, (rect.centerx - t.get_width()//2,
                        rect.centery - t.get_height()//2))

    # loop do menu
    while True:
        clock.tick(FPS)
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            # fechar janela encerra
            if event.type == pygame.QUIT:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                pygame.quit(); sys.exit()

            # clique nos botões
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start.collidepoint(event.pos):
                    if click_sound: click_sound.play()
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    return "START"

                if tuto.collidepoint(event.pos):
                    if click_sound: click_sound.play()
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    return "TUTORIAL"

                if sair.collidepoint(event.pos):
                    if click_sound: click_sound.play()
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    pygame.quit(); sys.exit()

            # atalhos do teclado no menu
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if click_sound: click_sound.play()
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    return "START"

                if event.key == pygame.K_ESCAPE:
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    pygame.quit(); sys.exit()

        # desenha o fundo do menu
        if bg:
            screen.blit(bg,(0,0))
        else:
            screen.fill((10,10,16))

        # detecta hover e toca som quando muda de botão
        for rect, name in [(start,"START"), (tuto,"TUTO"), (sair,"SAIR")]:
            if rect.collidepoint(mouse):
                if hovered_last != name and hover_sound:
                    hover_sound.play()
                hovered_last = name
                break
        else:
            hovered_last = None

        # desenha os botões
        draw(start,"INICIAR", start.collidepoint(mouse))
        draw(tuto,"TUTORIAL", tuto.collidepoint(mouse))
        draw(sair,"SAIR", sair.collidepoint(mouse))

        pygame.display.flip()


# ---------------- MAIN ----------------
def main():
    global GAME_OVER_SOUND
    global WIDTH, HEIGHT

    pygame.init()

    # cria a janela (scaled + fullscreen)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
    pygame.display.set_caption("As Três Graças")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)

    # tenta carregar o som de game over (pra usar depois na tela)
    try:
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except Exception:
                pass
        if pygame.mixer.get_init() is not None:
            GAME_OVER_SOUND = pygame.mixer.Sound(asset_path("assets", "game_over_som.mp3"))
            GAME_OVER_SOUND.set_volume(0.75)
    except Exception:
        GAME_OVER_SOUND = None

    # carrega imagens de fundo (game over e vitória) pra usar mais tarde
    try:
        PRESA_VIDEO_BG = pygame.image.load(asset_path("assets","Presa_video.png")).convert()
        PRESA_VIDEO_BG = pygame.transform.scale(PRESA_VIDEO_BG,(WIDTH,HEIGHT))
    except Exception:
        PRESA_VIDEO_BG = None

    try:
        VICTORY_BG = pygame.image.load(asset_path("assets","vitoria.png")).convert()
        VICTORY_BG = pygame.transform.scale(VICTORY_BG,(WIDTH,HEIGHT))
    except Exception:
        VICTORY_BG = None

    # loop geral do jogo (quando volta pro menu, ele recomeça daqui)
    while True:
        # primeiro: fica no menu até escolher START
        while True:
            choice = tela_inicial(screen, clock)
            if choice == "START":
                break
            if choice == "TUTORIAL":
                # limpa eventos pra não “vazar” clique do menu pra dentro do tutorial
                pygame.event.clear()
                mostrar_tutorial(screen, clock)

        # ---------------- FASE 1 ----------------
        fase1 = Fase1(screen, font)
        result = None

        # loop da fase 1
        while True:
            dt = clock.tick(FPS)/1000

            # eventos globais (fechar / ESC)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

            # atualiza e desenha fase 1
            result = fase1.update(dt)
            screen.fill((20,20,25))
            fase1.draw()
            pygame.display.flip()

            # condições de saída da fase 1
            if result in ("NEXT","LOSE_TIME"):
                break

        # se perdeu por tempo, mostra game over e volta pro menu (continue reinicia o loop)
        if result == "LOSE_TIME":
            mostrar_game_over(screen, clock, PRESA_VIDEO_BG)
            continue

        # ---------------- FASE 2 ----------------
        # chama fase2.run e pega o resultado
        try:
            resultado_fase2 = fase2.run(screen, clock, font, BASE_DIR)
        except Exception as e:
            import traceback
            print("Erro ao executar fase2 (traceback):")
            traceback.print_exc()
            resultado_fase2 = None

        # se perdeu na fase 2, game over e volta pro menu
        if resultado_fase2 == "LOSE":
            mostrar_game_over(screen, clock, PRESA_VIDEO_BG)
            continue

        if resultado_fase2 == "RECORDED":
            mostrar_game_over(screen, clock, PRESA_VIDEO_BG)
            continue

        # ---------------- FASE 3 ----------------
        # aqui ele cria um "proxy" pra fase3 usar as telas do main (game over/vitória)
        try:
            def _proxy_show_end_screen(title, msg, color):
                t = (title or "").upper()

                # se o título parece game over, manda pra tela de game over do main
                if ("GAME" in t) or ("OVER" in t):
                    return mostrar_game_over(screen, clock, PRESA_VIDEO_BG)

                # se parece vitória, manda pra tela de vitória do main
                if ("MISS" in t) or ("CONCLU" in t) or ("WIN" in t) or ("VIT" in t):
                    return mostrar_victory(screen, clock, VICTORY_BG, title, msg)

                # fallback: se não reconhecer, mostra game over
                return mostrar_game_over(screen, clock, PRESA_VIDEO_BG)

            fase3.show_end_screen = _proxy_show_end_screen
        except Exception as e:
            print("Aviso: não foi possível sobrescrever show_end_screen em fase3:", e)

        # roda a fase 3 (quando ela termina, volta pro loop principal e cai no menu de novo)
        fase3.run(screen, clock, font, BASE_DIR)


if __name__ == "__main__":
    main()
