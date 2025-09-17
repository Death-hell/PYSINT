import os
import time
import random
import sys
from getch import getch

# Configurações do jogo
LARGURA = 70
ALTURA = 20
RAQUETE_ALTURA = 4
RAQUETE_DISTANCIA = 3

# Posições iniciais
bola_x = LARGURA // 2
bola_y = ALTURA // 2
bola_dx = random.choice([-1, 1])
bola_dy = random.choice([-1, 1])

jogador_y = ALTURA // 2 - RAQUETE_ALTURA // 2
ia_y = ALTURA // 2 - RAQUETE_ALTURA // 2

placar_jogador = 0
placar_ia = 0

# Dificuldade da IA (1 = mais lenta, 5 = quase perfeita)
DIFICULDADE_IA = 3  # Ajuste entre 1 e 5

# Função para limpar a tela
def limpar_tela():
    os.system('clear')

# Função para desenhar o campo
def desenhar_campo():
    campo = [[' ' for _ in range(LARGURA)] for _ in range(ALTURA)]

    # Bordas superior e inferior
    for x in range(LARGURA):
        campo[0][x] = '═'
        campo[ALTURA-1][x] = '═'

    # Linha central
    for y in range(1, ALTURA-1):
        campo[y][LARGURA//2] = '│'

    # Raquete do jogador
    for i in range(RAQUETE_ALTURA):
        if 0 <= jogador_y + i < ALTURA:
            campo[jogador_y + i][RAQUETE_DISTANCIA] = '█'

    # Raquete da IA
    for i in range(RAQUETE_ALTURA):
        if 0 <= ia_y + i < ALTURA:
            campo[ia_y + i][LARGURA - RAQUETE_DISTANCIA - 1] = '█'

    # Bola
    if 0 < bola_y < ALTURA-1 and 0 < bola_x < LARGURA-1:
        campo[bola_y][bola_x] = '●'

    # Imprimir
    limpar_tela()
    print(f"PLACAR: Você {placar_jogador} x {placar_ia} IA")
    print("W/S = mover | Q = sair")
    print('╔' + '═' * LARGURA + '╗')
    for linha in campo:
        print('║' + ''.join(linha) + '║')
    print('╚' + '═' * LARGURA + '╝')

# Função da IA
def mover_ia():
    global ia_y
    # A IA "vê" a bola e tenta se posicionar
    centro_ia = ia_y + RAQUETE_ALTURA // 2
    erro = random.randint(-1, 1)  # pequena imprecisão pra não ser invencível

    # Se a bola está vindo pra direita, a IA reage
    if bola_dx > 0:
        alvo = bola_y + erro
        if centro_ia < alvo and ia_y < ALTURA - RAQUETE_ALTURA - 1:
            ia_y += min(DIFICULDADE_IA, alvo - centro_ia)
        elif centro_ia > alvo and ia_y > 1:
            ia_y -= min(DIFICULDADE_IA, centro_ia - alvo)

# Loop principal
try:
    while True:
        tecla = None
        if sys.stdin.readable():
            try:
                import select
                if select.select([sys.stdin], [], [], 0)[0]:
                    tecla = getch()
            except:
                pass

        # Movimento do jogador
        if tecla == 'w' and jogador_y > 1:
            jogador_y -= 1
        elif tecla == 's' and jogador_y < ALTURA - RAQUETE_ALTURA - 1:
            jogador_y += 1
        elif tecla == 'q':
            print("Saindo do jogo...")
            break

        # IA se move
        mover_ia()

        # Movimento da bola
        bola_x += bola_dx
        bola_y += bola_dy

        # Colisão com teto/chão
        if bola_y <= 1 or bola_y >= ALTURA - 2:
            bola_dy *= -1

        # Colisão com raquetes
        if (bola_x == RAQUETE_DISTANCIA + 1 and
            jogador_y <= bola_y < jogador_y + RAQUETE_ALTURA):
            bola_dx *= -1
            bola_x += bola_dx

        if (bola_x == LARGURA - RAQUETE_DISTANCIA - 2 and
            ia_y <= bola_y < ia_y + RAQUETE_ALTURA):
            bola_dx *= -1
            bola_x += bola_dx

        # Ponto para IA
        if bola_x <= 0:
            placar_ia += 1
            time.sleep(0.5)
            bola_x, bola_y = LARGURA // 2, ALTURA // 2
            bola_dx = random.choice([-1, 1])
            bola_dy = random.choice([-1, 1])

        # Ponto para jogador
        if bola_x >= LARGURA - 1:
            placar_jogador += 1
            time.sleep(0.5)
            bola_x, bola_y = LARGURA // 2, ALTURA // 2
            bola_dx = random.choice([-1, 1])
            bola_dy = random.choice([-1, 1])

        # Desenhar quadro
        desenhar_campo()
        time.sleep(0.07)

except KeyboardInterrupt:
    print("\nJogo interrompido.")
