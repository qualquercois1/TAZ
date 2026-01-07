import pygame, sys, os, pickle, neat

# Importa as classes e configurações do seu arquivo principal (taz.py)
# Certifique-se de que o arquivo principal se chama 'taz.py' e está na mesma pasta
from taz import Cobra, Comida, comp_tela, alt_tela, comp_janela, alt_janela, tam_quadrado, inicio_x, inicio_y

# Constantes de Cores
preto = (0,0,0)
cinza_escuro = (54,54,54)
cinza_meio = (70,70,70)
chocolate = (210,105,30)
verde_neon = (0, 255, 0)
branco = (255,255,255)
amarelo = (255, 255, 0)

def replay_genome(config_path, genome_path="winner.pkl"):
    # 1. Carrega configuração
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    # 2. Verifica se o arquivo existe
    if not os.path.exists(genome_path):
        print(f"Erro: Arquivo '{genome_path}' não encontrado. Treine a IA primeiro!")
        return

    # 3. Carrega o cérebro salvo
    with open(genome_path, "rb") as f:
        genome = pickle.load(f)

    # 4. Cria a rede neural
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    # 5. Setup Pygame
    pygame.init()
    janela = pygame.display.set_mode((comp_janela, alt_janela))
    pygame.display.set_caption("TAZ - REPLAY VENCEDOR (Relativo)")
    
    clock = pygame.time.Clock()
    fonte = pygame.font.SysFont('arial', 20, True, False)
    fonte_grande = pygame.font.SysFont('arial', 40, True, False)
    
    # Background (pré-renderizado)
    fundo = pygame.Surface((comp_tela, alt_tela))
    fundo.fill(cinza_escuro)
    for x in range(0, comp_tela, tam_quadrado):
        pygame.draw.line(fundo, cinza_meio, (x,0), (x, alt_tela))
    for y in range(0, alt_tela, tam_quadrado):
        pygame.draw.line(fundo, cinza_meio, (0,y), (comp_tela, y))
    fundo = fundo.convert()

    renderizar = True 

    # Loop Infinito (Reinicia o jogo quando morre)
    while True:
        cobra = Cobra()
        comida = Comida()
        run = True
        pontuacao = 0
        
        while run:
            if renderizar:
                clock.tick(15) # Velocidade confortável para assistir

            # Eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        renderizar = not renderizar

            # --- IA JOGA ---
            # 1. Pega os inputs (Visão Relativa e Profundidade)
            dados = cobra.inputs(comida.pos)
            
            # 2. Rede Processa
            output = net.activate(dados)
            
            # 3. Decisão (0=Esq, 1=Reto, 2=Dir)
            acao = output.index(max(output))

            # 4. Executa Movimento
            # O método mover da classe Cobra já sabe converter 0/1/2 em rotação
            cobra.mover(acao)

            # --- LÓGICA DE JOGO ---
            if cobra.cabeca_pos == comida.pos:
                comida.gerar_nova_posicao(cobra.corpo)
                cobra.fome = cobra.fome_max
                pontuacao += 1
            else:
                cobra.corpo.pop()

            if cobra.verificar_morte() or cobra.fome <= 0:
                print(f"Game Over! Pontuação Final: {pontuacao}")
                run = False # Sai do loop interno e cria nova cobra
                break
            
            cobra.fome -= 1

            # --- DESENHO ---
            if renderizar:
                janela.fill(preto)
                janela.blit(fundo, (inicio_x, inicio_y))
                
                # Surface temporária transparente para desenhar os objetos
                tela_jogo = pygame.Surface((comp_tela, alt_tela), pygame.SRCALPHA)
                
                cobra.desenhar(tela_jogo)
                comida.desenhar(tela_jogo)
                
                janela.blit(tela_jogo, (inicio_x, inicio_y))

                # HUD
                txt_score = fonte.render(f"Pontos: {pontuacao} | Fome: {cobra.fome}", True, branco)
                txt_dica = fonte.render("G: Turbo ON/OFF", True, cinza_meio)
                janela.blit(txt_score, (10, 10))
                janela.blit(txt_dica, (10, 35))

                pygame.display.flip()
            
            else:
                # Desenha só texto no modo turbo
                # (Renderiza a cada 5 frames para economizar CPU)
                if cobra.fome % 5 == 0: 
                    janela.fill(preto)
                    aviso = fonte_grande.render("MODO TURBO (REPLAY)", True, amarelo)
                    placar = fonte.render(f"Pontos: {pontuacao}", True, branco)
                    fome_txt = fonte.render(f"Fome: {cobra.fome}", True, branco)
                    
                    janela.blit(aviso, (comp_janela//2 - 150, alt_janela//2 - 50))
                    janela.blit(placar, (comp_janela//2 - 50, alt_janela//2 + 20))
                    janela.blit(fome_txt, (comp_janela//2 - 40, alt_janela//2 + 50))
                    pygame.display.flip()

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    replay_genome(config_path)