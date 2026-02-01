# As Três Graças
Feito por Vitória Machado e Sofia Ishizaki

## Sobre o jogo
As Três Graças é um jogo feito em Python com Pygame, dividido em três fases. A proposta é misturar exploração, quebra de tempo e furtividade. Você controla a personagem e precisa cumprir objetivos específicos em cada fase para avançar, lidando com obstáculos, áreas de risco e interações no cenário.

## Como funciona
O jogo começa em um menu inicial, onde você pode iniciar a campanha ou abrir o tutorial. O tutorial é mostrado em páginas de imagem, e você avança clicando na tela.

Ao iniciar, o jogo segue um fluxo fixo:
1. Fase 1: encontrar a senha escondida e abrir o cofre antes do tempo acabar.
2. Fase 2: atravessar o ambiente sem ser filmada pelas câmeras ou sabotar o painel para desligá-las.
3. Fase 3: roubar a estatueta, evitar os guardas e sair pela porta de fuga.

Se você perder em alguma fase, aparece a tela de Game Over e você pode reiniciar e voltar ao início.

## Controles
Menu inicial
Clique nos botões para iniciar, abrir o tutorial ou sair
Enter inicia o jogo
Esc fecha o jogo

Tutorial
Clique em qualquer lugar da tela para avançar as páginas
Esc volta para o menu

Fase 1
WASD ou Setas movimenta
Space interage com os esconderijos e com o cofre
Digite números para inserir a senha do cofre
Backspace apaga
Enter confirma
Esc cancela a digitação

Fase 2
WASD ou Setas movimenta
Space sabota o painel quando estiver perto
Objetivo: atravessar sem ser filmada ou desligar as câmeras e sair

Fase 3
WASD ou Setas movimenta
E abre a porta da entrada quando estiver perto
Space rouba a estatueta segurando por um tempo
Objetivo: pegar a estatueta e sair pela porta de fuga evitando os guardas

## Requisitos
Python 3
Pygame

## Como executar
1. Instale as dependências
   pip install pygame

2. Execute o jogo
   python main.py

## Estrutura do projeto
main.py controla menu, tutorial e fluxo entre fases
fase1.py lógica da Fase 1
fase2.py lógica da Fase 2
fase3.py lógica da Fase 3
assets/ imagens e sons usados no jogo

## Link do YouTube
https://youtu.be/nF6zYbuNhrs?si=UhpgVWi07z2WWB7D
