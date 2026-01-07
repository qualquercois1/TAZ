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
pygame.display.set_caption("TAZ - Treinamento IA (Relativo)")

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
        # MUDANÇA: Início Aleatório para evitar vício de posição
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        
        x = random.randint(2, max_x - 3)
        y = random.randint(2, max_y - 3)
        
        self.cabeca_pos = [x, y]
        self.corpo = [list(self.cabeca_pos)]
        self.direcao = random.choice(["DIREITA", "ESQUERDA", "CIMA", "BAIXO"])
        
        self.viva = True
        self.fome_max = 100
        self.fome = self.fome_max

    # Helper para "olhar" em uma direção relativa
    def olhar_na_direcao_vetor(self, vec_x, vec_y):
        olho_x, olho_y = self.cabeca_pos
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        distancia = 0
        
        # Olha até o infinito (ou até achar corpo)
        while True:
            olho_x = (olho_x + vec_x) % max_x
            olho_y = (olho_y + vec_y) % max_y
            distancia += 1
            
            # Se bateu no corpo
            if [olho_x, olho_y] in self.corpo:
                return 1.0 / distancia # Retorna inverso da distância
            
            # Se deu a volta completa no mapa e não achou nada, é seguro (0)
            if distancia > max(max_x, max_y):
                return 0.0

    def inputs(self, pos_comida):
        # --- DEFINIR VETORES RELATIVOS ---
        # Baseado na direção atual, o que é Frente, Esquerda e Direita?
        # Vetor (x, y)
        vetores = {
            "CIMA":     {"frente": (0, -1), "esquerda": (-1, 0), "direita": (1, 0)},
            "BAIXO":    {"frente": (0, 1),  "esquerda": (1, 0),  "direita": (-1, 0)},
            "ESQUERDA": {"frente": (-1, 0), "esquerda": (0, 1),  "direita": (0, -1)},
            "DIREITA":  {"frente": (1, 0),  "esquerda": (0, -1), "direita": (0, 1)}
        }
        
        v = vetores[self.direcao]

        # --- 1. PERIGO (Relative Raycasting) ---
        # "Tem perigo na minha frente?"
        p_frente = self.olhar_na_direcao_vetor(v["frente"][0], v["frente"][1])
        p_esq = self.olhar_na_direcao_vetor(v["esquerda"][0], v["esquerda"][1])
        p_dir = self.olhar_na_direcao_vetor(v["direita"][0], v["direita"][1])

        # --- 2. COMIDA (Angulo Relativo) ---
        # Vamos descobrir onde a comida está em relação à cabeça
        # Usando lógica toroidal
        cx, cy = pos_comida
        hx, hy = self.cabeca_pos
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado

        dx = cx - hx
        dy = cy - hy

        # Ajuste Toroidal
        if abs(dx) > max_x / 2: dx = -dx
        if abs(dy) > max_y / 2: dy = -dy

        # Agora, a comida está à esquerda, direita ou frente da direção atual?
        # Isso é pura geometria. Vamos simplificar com Booleanos para a comida
        
        food_frente = 0
        food_esq = 0
        food_dir = 0
        
        # Lógica simplificada: Comida está na direção do vetor?
        # Ex: Se estou indo para CIMA (dy < 0) e a comida está em cima (dy < 0) -> Frente
        
        if self.direcao == "CIMA":
            if dy < 0: food_frente = 1
            if dx < 0: food_esq = 1
            if dx > 0: food_dir = 1
        elif self.direcao == "BAIXO":
            if dy > 0: food_frente = 1
            if dx > 0: food_esq = 1 # Se olho pra baixo, direita global é minha esquerda
            if dx < 0: food_dir = 1
        elif self.direcao == "ESQUERDA":
            if dx < 0: food_frente = 1
            if dy > 0: food_esq = 1
            if dy < 0: food_dir = 1
        elif self.direcao == "DIREITA":
            if dx > 0: food_frente = 1
            if dy < 0: food_esq = 1
            if dy > 0: food_dir = 1

        # Inputs do NEAT (11 Neurônios)
        # [PerigoF, PerigoE, PerigoD, ComidaF, ComidaE, ComidaD, ...]
        # Adicionei os deltas normalizados também para ajudar na precisão
        return [
            p_frente, p_esq, p_dir,
            food_frente, food_esq, food_dir,
            # Inputs extras que ajudam a triangular a posição exata
            dx / max_x, 
            dy / max_y
        ]

    def mover(self, acao_relativa):
        # Ação Relativa: 0 = Esquerda, 1 = Reto, 2 = Direita
        
        ordem_horaria = ["CIMA", "DIREITA", "BAIXO", "ESQUERDA"]
        idx_atual = ordem_horaria.index(self.direcao)

        if acao_relativa == 0: # Virar Esquerda (Anti-horário)
            idx_novo = (idx_atual - 1) % 4
            self.direcao = ordem_horaria[idx_novo]
        elif acao_relativa == 2: # Virar Direita (Horário)
            idx_novo = (idx_atual + 1) % 4
            self.direcao = ordem_horaria[idx_novo]
        # Se for 1, mantém a direção (Reto)

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
            # Desenha cabeça diferente para sabermos onde ela olha
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
            # Agora output tem 3 valores: [Esq, Reto, Dir]
            acao = output.index(max(output))

            cobra.mover(acao) # Passamos a ação (0, 1 ou 2)

            dist_depois = distancia_toroidal(cobra.cabeca_pos, comidas[i].pos)

            # Recompensa Quente/Frio
            if dist_depois < dist_antes:
                lista_ge[i].fitness += 1
            else:
                lista_ge[i].fitness -= 2 # Punição um pouco maior para evitar loops

            if cobra.cabeca_pos == comidas[i].pos:
                lista_ge[i].fitness += 30 
                cobra.fome = cobra.fome_max
                comidas[i].gerar_nova_posicao(cobra.corpo)
            else:
                cobra.corpo.pop()

            morreu_colisao = cobra.verificar_morte()
            morreu_fome = cobra.fome <= 0

            if morreu_colisao or morreu_fome or lista_ge[i].fitness < -20:
                if morreu_colisao: lista_ge[i].fitness -= 30
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

            # Infos
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
    
    winner = p.run(eval_genomes, 50)
    with open("winner.pkl", "wb") as f:
        pickle.dump(winner, f)

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)