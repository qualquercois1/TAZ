import pygame, sys, random, math, neat, os
import pickle

# 1. Inicializa o Pygame e a Janela (Globalmente)
pygame.init()

# Constantes
tam_quadrado = 40
comp_janela, alt_janela = 1280, 720
comp_tela, alt_tela = 1040, 560
inicio_x = (comp_janela - comp_tela) // 2
inicio_y = (alt_janela - alt_tela) // 2
fps = 30 

# --- VARIÁVEIS GLOBAIS DE CONTROLE ---
gen = 0
mostrar_todas = False 
renderizar = True 

# Cores
preto = (0,0,0)
cinza_escuro = (54,54,54)
cinza_meio = (70,70,70)
roxo = (25,25,112)
chocolate = (210,105,30)
branco = (255,255,255)
verde_neon = (0, 255, 0)
vermelho = (206, 0, 0)
ciano = (0, 255, 255)
amarelo = (255, 255, 0)

# Setup da Janela
janela = pygame.display.set_mode((comp_janela, alt_janela))
pygame.display.set_caption("TAZ - Treinamento IA (Relativo + Raycasting)")

# Background
fundo = pygame.Surface((comp_tela, alt_tela))
fundo.fill(cinza_escuro)
for x in range(0, comp_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (x,0), (x, alt_tela))
for y in range(0, alt_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (0,y), (comp_tela, y))
fundo = fundo.convert()

def distancia_toroidal(p1, p2):
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    largura_grid = comp_tela // tam_quadrado
    altura_grid = alt_tela // tam_quadrado

    if dx > largura_grid / 2: dx = largura_grid - dx
    if dy > altura_grid / 2: dy = altura_grid - dy

    return math.sqrt(dx**2 + dy**2)

class Comida:
    def __init__(self):
        self.pos = []
        self.gerar_nova_posicao()

    def gerar_nova_posicao(self, corpo_cobra=[]):
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
        # Início Aleatório para evitar vício
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        
        x = random.randint(2, max_x - 3)
        y = random.randint(2, max_y - 3)
        
        self.cabeca_pos = [x, y]
        self.corpo = [list(self.cabeca_pos)]
        self.direcao = random.choice(["DIREITA", "ESQUERDA", "CIMA", "BAIXO"])
        
        self.viva = True
        self.fome_max = 200 
        self.fome = self.fome_max

    # Helper para "olhar" em uma direção relativa
    def olhar_na_direcao_vetor(self, vec_x, vec_y):
        olho_x, olho_y = self.cabeca_pos
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        distancia = 0
        
        # Limita a visão a metade do mapa (mundo toroidal)
        limite = max(max_x, max_y) // 2 

        for _ in range(limite):
            olho_x = (olho_x + vec_x) % max_x
            olho_y = (olho_y + vec_y) % max_y
            distancia += 1
            
            if [olho_x, olho_y] in self.corpo:
                return 1.0 / distancia # Retorna inverso da distância (1.0 = PERTO)
            
        return 0.0

    def inputs(self, pos_comida):
        # Mapeamento de Vetores Relativos
        vetores = {
            "CIMA":     (0, -1),
            "BAIXO":    (0, 1),
            "ESQUERDA": (-1, 0),
            "DIREITA":  (1, 0)
        }
        
        frente = vetores[self.direcao]
        esquerda = (frente[1], -frente[0]) 
        direita = (-frente[1], frente[0])  
        
        # Vetores Diagonais
        diag_fe = (frente[0] + esquerda[0], frente[1] + esquerda[1])
        diag_fd = (frente[0] + direita[0], frente[1] + direita[1])

        # --- 1. SENSORES DE PERIGO (5 Sensores) ---
        p_frente = self.olhar_na_direcao_vetor(frente[0], frente[1])
        p_esq = self.olhar_na_direcao_vetor(esquerda[0], esquerda[1])
        p_dir = self.olhar_na_direcao_vetor(direita[0], direita[1])
        p_diag_fe = self.olhar_na_direcao_vetor(diag_fe[0], diag_fe[1])
        p_diag_fd = self.olhar_na_direcao_vetor(diag_fd[0], diag_fd[1])

        # --- 2. COMIDA (Angulo Relativo Toroidal) ---
        cx, cy = pos_comida
        hx, hy = self.cabeca_pos
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado

        dx = cx - hx
        dy = cy - hy

        if abs(dx) > max_x / 2: dx = -dx
        if abs(dy) > max_y / 2: dy = -dy

        # Normaliza Deltas
        ndx = dx / max_x
        ndy = dy / max_y

        # Produto escalar para saber direção da comida
        dot_frente = (dx * frente[0]) + (dy * frente[1])
        dot_esq = (dx * esquerda[0]) + (dy * esquerda[1])
        dot_dir = (dx * direita[0]) + (dy * direita[1])

        c_frente = 1 if dot_frente > 0 else 0
        c_esq = 1 if dot_esq > 0 else 0
        c_dir = 1 if dot_dir > 0 else 0
        
        # Retorna 12 Inputs
        return [
            p_frente, p_esq, p_dir, p_diag_fe, p_diag_fd, 
            c_frente, c_esq, c_dir, 
            ndx, ndy, 
            0, 0 # Padding
        ]

    def mover(self, acao_relativa):
        # 0 = Esquerda, 1 = Reto, 2 = Direita
        ordem_horaria = ["CIMA", "DIREITA", "BAIXO", "ESQUERDA"]
        idx_atual = ordem_horaria.index(self.direcao)

        if acao_relativa == 0: # Esquerda
            idx_novo = (idx_atual - 1) % 4
            self.direcao = ordem_horaria[idx_novo]
        elif acao_relativa == 2: # Direita
            idx_novo = (idx_atual + 1) % 4
            self.direcao = ordem_horaria[idx_novo]

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

    def verificar_morte(self):
        if self.cabeca_pos in self.corpo[1:]:
            self.viva = False
            return True
        return False

    def desenhar(self, surface):
        for i, pedaco in enumerate(self.corpo):
            cor = verde_neon if i == 0 else roxo
            rect = pygame.Rect(
                (pedaco[0] * tam_quadrado) + 2,
                (pedaco[1] * tam_quadrado) + 2,
                tam_quadrado - 4,
                tam_quadrado - 4
            )
            pygame.draw.rect(surface, cor, rect, border_radius=4)

def eval_genomes(genomes, config):
    global placar, gen, renderizar, mostrar_todas
    gen += 1
    
    redes = []
    lista_ge = []
    cobras = []
    comidas = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        redes.append(net)
        cobras.append(Cobra())
        comidas.append(Comida())
        lista_ge.append(genome)

    clock = pygame.time.Clock()
    tela = pygame.Surface((comp_tela, alt_tela))
    fonte = pygame.font.SysFont('arial', 20, True, False)
    fonte_grande = pygame.font.SysFont('arial', 50, True, False)

    rodando = True
    while rodando and len(cobras) > 0:
        if renderizar: clock.tick(fps)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v: mostrar_todas = not mostrar_todas
                if event.key == pygame.K_g: renderizar = not renderizar

        # --- LÓGICA ---
        for i, cobra in reversed(list(enumerate(cobras))):
            dist_antes = distancia_toroidal(cobra.cabeca_pos, comidas[i].pos)
            cobra.fome -= 1
            
            # --- DECISÃO DA IA ---
            dados_entrada = cobra.inputs(comidas[i].pos)
            output = redes[i].activate(dados_entrada)
            acao = output.index(max(output))

            cobra.mover(acao) 

            dist_depois = distancia_toroidal(cobra.cabeca_pos, comidas[i].pos)

            # Recompensa Quente/Frio
            if dist_depois < dist_antes:
                lista_ge[i].fitness += 1.0
            else:
                lista_ge[i].fitness -= 0.1 # Punição leve para permitir desvios

            lista_ge[i].fitness += 0.05 # Sobrevivência

            if cobra.cabeca_pos == comidas[i].pos:
                lista_ge[i].fitness += 20 
                cobra.fome = cobra.fome_max
                comidas[i].gerar_nova_posicao(cobra.corpo)
            else:
                cobra.corpo.pop()

            morreu_colisao = cobra.verificar_morte()
            morreu_fome = cobra.fome <= 0

            if morreu_colisao or morreu_fome or lista_ge[i].fitness < -20:
                if morreu_colisao: lista_ge[i].fitness -= 20
                if morreu_fome: lista_ge[i].fitness -= 10
                
                redes.pop(i)
                lista_ge.pop(i)
                cobras.pop(i)
                comidas.pop(i)

        if len(cobras) == 0: break

        # --- DESENHO ---
        if renderizar:
            janela.fill(preto)
            tela.blit(fundo, (0,0))

            if mostrar_todas:
                for j, c in enumerate(cobras):
                    c.desenhar(tela)
                    comidas[j].desenhar(tela)
                txt_m = "Modo: Todas"
            else:
                cobras[0].desenhar(tela)
                comidas[0].desenhar(tela)
                txt_m = "Modo: Foco"

            janela.blit(tela, (inicio_x, inicio_y))

            infos = [f"Geração: {gen}", f"Vivos: {len(cobras)}", f"Fome: {cobras[0].fome}", txt_m]
            for idx, info in enumerate(infos):
                t = fonte.render(info, True, branco)
                janela.blit(t, (10, 10 + (idx * 25)))
            
            pygame.display.flip()
        else:
            janela.fill(preto)
            t1 = fonte_grande.render("MODO TURBO", True, amarelo)
            t2 = fonte.render(f"Gen: {gen} | Vivos: {len(cobras)}", True, branco)
            janela.blit(t1, (comp_janela//2 - 100, alt_janela//2 - 50))
            janela.blit(t2, (comp_janela//2 - 80, alt_janela//2 + 20))
            pygame.display.flip()

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    winner = p.run(eval_genomes, 50) # Roda 300 gerações
    print('\nMelhor genoma salvo em winner.pkl')
    with open("winner.pkl", "wb") as f:
        pickle.dump(winner, f)

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)