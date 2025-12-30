import pygame, sys, random

pygame.init()

#cores
preto = (0,0,0)
cinza_escuro = (54,54,54)
cinza_meio = (70,70,70)
cinza_claro = (128,128,128)
roxo = (25,25,112)
verde = (173,255,47)
chocolate = (210,105,30)
branco = (255,255,255)
vermelho = (255,0,0)


# atualização de frames da tela
# jogador = 0 (PESSOA) jogador = 1 (IA)
jogador = 0
if(jogador == 0):fps = 15
else: fps = 10000

clock = pygame.time.Clock()

# configurações da tela
comprimento_janela, altura_janela = 1280, 720
comprimento_tela, altura_tela = 1040, 560

janela = pygame.display.set_mode((comprimento_janela, altura_janela))
pygame.display.set_caption("Snake")

tela = pygame.Surface((comprimento_tela, altura_tela))

inicio_x = (comprimento_janela - comprimento_tela) // 2
inicio_y = (altura_janela - altura_tela) // 2

# placar
fonte_placar = pygame.font.SysFont('arial', 40, True, False)

# grid
tam_quadrado = 40

fundo = pygame.Surface((comprimento_tela, altura_tela))
fundo.fill(cinza_escuro)
for x in range(0, comprimento_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (x,0), (x, altura_tela))

for y in range(0, altura_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (0,y), (comprimento_tela, y))

fundo = fundo.convert()

# funções
def iniciar_variaveis():
    global cobra_cabeca_pos, cobra_corpo, comida_pos, comida_spawn, placar, direcao, jogo, mudou_direcao
    direcao = "DIREITA"
    mudou_direcao = False
    cobra_cabeca_pos = [3, 2]
    cobra_corpo = [cobra_cabeca_pos]
    comida_pos = [random.randrange(0, (comprimento_tela // tam_quadrado)), random.randrange(0, (altura_tela // tam_quadrado))]
    placar = 0
    jogo = True

iniciar_variaveis()

def desenhar(x, y, cor):
    margem = 2
    rect = pygame.Rect(
        (x*tam_quadrado) + margem,
        (y*tam_quadrado) + margem,
        tam_quadrado - (margem * 2), 
        tam_quadrado - (margem * 2)
        )
    pygame.draw.rect(tela, cor, rect, border_radius=4)

def mudar_direcao(evento):
    global direcao, mudou_direcao

    if mudou_direcao: return
    
    if ((evento.key == pygame.K_UP or evento.key == ord("w")) and direcao != "BAIXO"):
        direcao = "CIMA"
        mudou_direcao = True
    elif ((evento.key == pygame.K_DOWN or evento.key == ord("s")) and direcao != "CIMA"):
        direcao = "BAIXO"
        mudou_direcao = True
    elif ((evento.key == pygame.K_RIGHT or evento.key == ord("d")) and direcao != "ESQUERDA"):
        direcao = "DIREITA"
        mudou_direcao = True
    elif ((evento.key == pygame.K_LEFT or evento.key == ord("a")) and direcao != "DIREITA"):
        direcao = "ESQUERDA"
        mudou_direcao = True

def movimento():
    global comida_pos, placar, cobra_cabeca_pos

    nova_posicao = list(cobra_corpo[0])

    if direcao == "CIMA":
        nova_posicao[1] -= 1
    elif direcao == "BAIXO":
        nova_posicao[1] += 1
    elif direcao == "DIREITA":
        nova_posicao[0] += 1
    elif direcao == "ESQUERDA":
        nova_posicao[0] -= 1

    limite_x = comprimento_tela // tam_quadrado
    limite_y = altura_tela // tam_quadrado

    if nova_posicao[0] >= limite_x:
        nova_posicao[0] = 0
    elif nova_posicao[0] < 0:
        nova_posicao[0] = limite_x - 1
    elif nova_posicao[1] >= limite_y:
        nova_posicao[1] = 0
    elif nova_posicao[1] < 0:
        nova_posicao[1] = limite_y - 1
  
    # nova cabeça
    cobra_corpo.insert(0, nova_posicao)

    if nova_posicao == comida_pos:
        placar += 1
        comida_pos = [random.randrange(0, (comprimento_tela // tam_quadrado)), random.randrange(0, (altura_tela // tam_quadrado))]
        
        while comida_pos in cobra_corpo:
            comida_pos = [random.randrange(0, limite_x), random.randrange(0, limite_y)]

    else:
        cobra_corpo.pop()

    cobra_cabeca_pos = cobra_corpo[0]

def verificarMorte():
    global jogo

    if cobra_cabeca_pos in cobra_corpo[1:]:
        jogo = False


# loop principal
while True:

    # loop do jogo
    while jogo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                sys.exit()
            elif evento.type == pygame.KEYDOWN:
                mudar_direcao(evento)

        movimento()
        mudou_direcao = False
        verificarMorte()
        
        tela.blit(fundo, (0,0))
        # desenha cobra com as cores mudando conforme ela cresce
        for i, corpo in enumerate(cobra_corpo):

            r, g, b = roxo

            fator = i*3

            novo_r = min(255, r+ fator)
            novo_g = min(255, g+ fator)
            novo_b = min(255, b+ fator)

            nova_cor = (novo_r, novo_g, novo_b)

            desenhar(corpo[0], corpo[1], nova_cor)
            
        # desenha comida
        desenhar(comida_pos[0], comida_pos[1], chocolate)

        janela.fill(preto)
        janela.blit(tela, (inicio_x, inicio_y))

        placar_mensagem = f"Placar: {placar}"
        placar_formatado = fonte_placar.render(placar_mensagem, True, branco)
        rect_placar = placar_formatado.get_rect(center=(comprimento_janela // 2, inicio_y // 2))

        janela.blit(placar_formatado, rect_placar)

        pygame.display.flip()
        clock.tick(fps)

    janela.fill(preto)
    iniciar_variaveis()

