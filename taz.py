import pygame, sys, random, math, neat, os

pygame.init()
 
# Constantes
tam_quadrado = 40
comp_janela, alt_janela = 1280, 720
comp_tela, alt_tela = 1040, 560
inicio_x = (comp_janela - comp_tela) // 2
inicio_y = (alt_janela - alt_tela) // 2
fps = 15

# Cores
preto = (0,0,0)
cinza_escuro = (54,54,54)
cinza_meio = (70,70,70)
roxo = (25,25,112)
chocolate = (210,105,30)
branco = (255,255,255)

# Background
janela = pygame.display.set_mode((comp_janela, alt_janela))
pygame.display.set_caption("TAZ - Treinamento IA")
fundo = pygame.Surface((comp_tela, alt_tela))
fundo.fill(cinza_escuro)
for x in range(0, comp_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (x,0), (x, alt_tela))
for y in range(0, alt_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (0,y), (comp_tela, y))
fundo = fundo.convert()

class Comida:
    def __init__(self):
        self.pos = []
        self.gerar_nova_posicao()

    def gerar_nova_posicao(self, corpo_cobra=[]):
        # Spawna a comida em algum lugar aleatório (não spawna dentro da cobra)
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        
        self.pos = [random.randrange(0, max_x), random.randrange(0, max_y)]
        
        while self.pos in corpo_cobra:
            self.pos = [random.randrange(0, max_x), random.randrange(0, max_y)]

    def desenhar(self, surface):
        margem = 2
        rect = pygame.Rect(
            (self.pos[0] * tam_quadrado) + margem,
            (self.pos[1] * tam_quadrado) + margem,
            tam_quadrado - (margem * 2),
            tam_quadrado - (margem * 2)
        )
        pygame.draw.rect(surface, chocolate, rect, border_radius=4)


class Cobra:
    def __init__(self):
        self.resetar()

    def resetar(self):
        self.direcao = "DIREITA"
        self.mudou_direcao = False
        self.cabeca_pos = [3, 2]
        self.corpo = [list(self.cabeca_pos)]
        self.viva = True


    def calcular_diagonal(self):
        # serve para normalizar o vetor
        largura_grid = comp_tela // tam_quadrado
        altura_grid = alt_janela // tam_quadrado
        return math.sqrt(largura_grid**2 + altura_grid**2)

    def distancia_comida(self, pos_comida):
        dist = math.sqrt((pos_comida[0]-self.cabeca_pos[0])**2+(pos_comida[1]-self.cabeca_pos[1])**2)
        # normaliza
        diagonal = self.calcular_diagonal()
        return dist / diagonal
    
    def olha_direcao(self, direcao_x, direcao_y):
        olho_x = self.cabeca_pos[0]
        olho_y = self.cabeca_pos[1]

        distancia = 0
        achou_corpo = False

        max_x = comp_tela // tam_quadrado
        max_y = alt_janela // tam_quadrado

        while True:
            olho_x += direcao_x
            olho_y += direcao_y
            distancia += 1

            if olho_x >= max_x or olho_y >= max_y:
                return 1.0/distancia

            if [olho_x, olho_y] in self.corpo:
                return 1.0/distancia
    
    def inputs(self, pos_comida):
        dist_cima = self.olha_direcao(0,-1)
        dist_baixo = self.olha_direcao(0, 1)
        dist_esquerda = self.olha_direcao(-1, 0)
        dist_direita = self.olha_direcao(1, 0)

        distancia_comida = self.distancia_comida(pos_comida)

        dx = (pos_comida[0] - self.cabeca_pos[0]) / (comp_tela // tam_quadrado)
        dy = (pos_comida[1] - self.cabeca_pos[1]) / (alt_tela // tam_quadrado)

        return [dist_cima, dist_baixo, dist_esquerda, dist_direita, dx, dy]

    def mover(self):
        nova_pos = list(self.corpo[0])

        if self.direcao == "CIMA": nova_pos[1] -= 1
        elif self.direcao == "BAIXO": nova_pos[1] += 1
        elif self.direcao == "DIREITA": nova_pos[0] += 1
        elif self.direcao == "ESQUERDA": nova_pos[0] -= 1

        limite_x = comp_tela // tam_quadrado
        limite_y = alt_tela // tam_quadrado

        if nova_pos[0] >= limite_x: nova_pos[0] = 0
        elif nova_pos[0] < 0: nova_pos[0] = limite_x - 1
        elif nova_pos[1] >= limite_y: nova_pos[1] = 0
        elif nova_pos[1] < 0: nova_pos[1] = limite_y - 1

        self.corpo.insert(0, nova_pos)
        self.cabeca_pos = nova_pos
        self.mudou_direcao = False

    def verificar_morte(self):
        if self.cabeca_pos in self.corpo[1:]:
            self.viva = False
            return True
        return False

    def desenhar(self, surface):
        for i, pedaco in enumerate(self.corpo):
            # Gradiente de cores do corpo
            r, g, b = roxo
            fator = i * 3
            novo_r = min(255, r + fator)
            novo_g = min(255, g + fator)
            novo_b = min(255, b + fator)
            nova_cor = (novo_r, novo_g, novo_b)

            margem = 2
            rect = pygame.Rect(
                (pedaco[0] * tam_quadrado) + margem,
                (pedaco[1] * tam_quadrado) + margem,
                tam_quadrado - (margem * 2),
                tam_quadrado - (margem * 2)
            )
            pygame.draw.rect(surface, nova_cor, rect, border_radius=4)


def eval_genomes(genomes, config):
    global placar, gen
    gen += 1

    redes = []
    lista_ge = []
    cobras = []
    comidas = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        redes.append(net)
        c = Cobra()
        cobras.append(c)
        comidas.append(Comida())
        lista_ge.append(genome)

    pygame.init()
    clock = pygame.time.Clock()
    janela = pygame.display.set_mode((comp_janela, alt_janela))
    tela = pygame.Surface((comp_tela, alt_tela))
    fonte = pygame.font.SysFont('arial', 30, True, False)

    rodando = True
    while rodando and len(cobras) > 0:
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # --- LÓGICA (Iteramos e marcamos quem deve morrer) ---
        # Dica de Ouro: Para remover itens de uma lista sem quebrar o índice,
        # iteramos de trás para frente!
        for i, cobra in reversed(list(enumerate(cobras))):
            
            # Aumenta fitness por sobreviver um pouco
            lista_ge[i].fitness += 0.05

            dados_entrada = cobra.inputs(comidas[i].pos)
            output = redes[i].activate(dados_entrada)
            
            # Escolhe a maior probabilidade
            decisao = output.index(max(output))

            if decisao == 0 and cobra.direcao != "BAIXO": cobra.direcao = "CIMA"
            elif decisao == 1 and cobra.direcao != "CIMA": cobra.direcao = "BAIXO"
            elif decisao == 2 and cobra.direcao != "DIREITA": cobra.direcao = "ESQUERDA"
            elif decisao == 3 and cobra.direcao != "ESQUERDA": cobra.direcao = "DIREITA"

            cobra.mover()

            # Comeu?
            if cobra.cabeca_pos == comidas[i].pos:
                lista_ge[i].fitness += 10 
                comidas[i].gerar_nova_posicao(cobra.corpo)
            else:
                cobra.corpo.pop()

            # Morreu ou fitness muito baixo (punição por ficar rodando)?
            # Adicionei uma punição se ela não comer em muito tempo (fitness > 500 sem comer é suspeito, mas ok)
            if cobra.verificar_morte() or lista_ge[i].fitness < -10:
                lista_ge[i].fitness -= 1 
                # REMOVE AGORA (Seguro porque estamos indo de trás para frente)
                redes.pop(i)
                lista_ge.pop(i)
                cobras.pop(i)
                comidas.pop(i)

        # --- DESENHO (FORA DO LOOP DAS COBRAS) ---
        janela.fill(preto)
        tela.blit(fundo, (0,0))

        # Desenhar apenas se ainda existirem cobras
        if len(cobras) > 0:
            for j, c in enumerate(cobras):
                c.desenhar(tela)
                comidas[j].desenhar(tela)

        janela.blit(tela, (inicio_x, inicio_y))

        texto = fonte.render(f"Geração: {gen} | Vivos: {len(cobras)}", True, branco)
        janela.blit(texto, (10, 10))

        pygame.display.flip()

# Inicialização do NEAT
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    p = neat.Population(config)

    # Estatísticas no terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Roda por 50 gerações chamando a função eval_genomes
    winner = p.run(eval_genomes, 50)

    # Aqui você salvaria o winner com pickle
    print('\nMelhor genoma:\n{!s}'.format(winner))

if __name__ == '__main__':
    gen = 0
    # Caminho para o arquivo de configuração (crie este arquivo na mesma pasta)
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)

# Game
