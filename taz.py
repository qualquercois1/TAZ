import pygame, sys, random, math, neat, os
import pickle

# 1. Inicializa o Pygame
pygame.init()

# --- CONSTANTES ---
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

# --- CORES ---
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

# --- SETUP DA JANELA ---
janela = pygame.display.set_mode((comp_janela, alt_janela))
pygame.display.set_caption("TAZ - Treinamento IA (BFS + Flood Fill)")

# Background Pré-renderizado
fundo = pygame.Surface((comp_tela, alt_tela))
fundo.fill(cinza_escuro)
for x in range(0, comp_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (x,0), (x, alt_tela))
for y in range(0, alt_tela, tam_quadrado):
    pygame.draw.line(fundo, cinza_meio, (0,y), (comp_tela, y))
fundo = fundo.convert()

# --- FUNÇÕES AUXILIARES ---
def distancia_toroidal(p1, p2):
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    largura_grid = comp_tela // tam_quadrado
    altura_grid = alt_tela // tam_quadrado

    if dx > largura_grid / 2: dx = largura_grid - dx
    if dy > altura_grid / 2: dy = altura_grid - dy

    return math.sqrt(dx**2 + dy**2)

# --- CLASSES ---
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
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        
        # Posição aleatória segura (longe das bordas iniciais)
        x = random.randint(2, max_x - 3)
        y = random.randint(2, max_y - 3)
        
        self.cabeca_pos = [x, y]
        self.corpo = [list(self.cabeca_pos)]
        self.direcao = random.choice(["DIREITA", "ESQUERDA", "CIMA", "BAIXO"])
        
        self.viva = True
        self.fome_max = 200 
        self.fome = self.fome_max

    # --- SENSOR 1: Raycasting (Visão de Profundidade) ---
    def olhar_na_direcao_vetor(self, vec_x, vec_y):
        olho_x, olho_y = self.cabeca_pos
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        distancia = 0
        
        # Limita a visão a metade do mapa
        limite = max(max_x, max_y) // 2 

        for _ in range(limite):
            olho_x = (olho_x + vec_x) % max_x
            olho_y = (olho_y + vec_y) % max_y
            distancia += 1
            if [olho_x, olho_y] in self.corpo:
                return 1.0 / distancia # Retorna inverso (1.0 = PERIGO IMEDIATO)
        return 0.0

    # --- SENSOR 2: BFS (Pathfinding - Onde ir?) ---
    def bfs_proximo_passo(self, alvo):
        start = tuple(self.cabeca_pos)
        target = tuple(alvo)
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        
        # A ponta da cauda NÃO é obstáculo (ela vai sair dali)
        obstaculos = set(tuple(x) for x in self.corpo[:-1]) 
        
        queue = [(start, [])]
        visited = set()
        visited.add(start)
        
        while queue:
            current, path = queue.pop(0)
            
            if current == target:
                if not path: return None 
                return path[0] 
            
            x, y = current
            neighbors = [
                ((x, y - 1), "CIMA"),
                ((x, y + 1), "BAIXO"),
                ((x - 1, y), "ESQUERDA"),
                ((x + 1, y), "DIREITA")
            ]
            
            for pos, direcao in neighbors:
                nx = pos[0] % max_x
                ny = pos[1] % max_y
                next_node = (nx, ny)
                
                if next_node not in visited and next_node not in obstaculos:
                    visited.add(next_node)
                    queue.append((next_node, path + [direcao]))
        return None

    # --- SENSOR 3: Flood Fill (Espaço Disponível - É seguro entrar?) ---
    def calcular_espaco_disponivel(self, inicio_x, inicio_y):
        # Otimização: Se tiver espaço para o corpo todo + 5, tá ótimo
        limite = len(self.corpo) + 5
        
        if [inicio_x, inicio_y] in self.corpo:
            return 0.0

        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        
        # Aqui consideramos a cauda como obstáculo por segurança
        obstaculos = set(tuple(x) for x in self.corpo)
        
        queue = [(inicio_x, inicio_y)]
        visited = set()
        visited.add((inicio_x, inicio_y))
        count = 0
        
        while queue:
            cx, cy = queue.pop(0)
            count += 1
            if count >= limite: return 1.0 
            
            neighbors = [
                (cx, cy - 1), (cx, cy + 1),
                (cx - 1, cy), (cx + 1, cy)
            ]
            
            for nx, ny in neighbors:
                nx = nx % max_x
                ny = ny % max_y
                node = (nx, ny)
                if node not in visited and node not in obstaculos:
                    visited.add(node)
                    queue.append(node)
        
        return count / limite

    # --- MESTRE DOS SENSORES (Inputs para a Rede Neural) ---
    def inputs(self, pos_comida):
        # Mapeia vetores relativos
        vetores = {
            "CIMA":     (0, -1),
            "BAIXO":    (0, 1),
            "ESQUERDA": (-1, 0),
            "DIREITA":  (1, 0)
        }
        
        frente = vetores[self.direcao]
        esquerda = (frente[1], -frente[0]) 
        direita = (-frente[1], frente[0])  
        
        diag_fe = (frente[0] + esquerda[0], frente[1] + esquerda[1])
        diag_fd = (frente[0] + direita[0], frente[1] + direita[1])

        # 1. PERIGO (5 Inputs)
        p_frente = self.olhar_na_direcao_vetor(frente[0], frente[1])
        p_esq = self.olhar_na_direcao_vetor(esquerda[0], esquerda[1])
        p_dir = self.olhar_na_direcao_vetor(direita[0], direita[1])
        p_diag_fe = self.olhar_na_direcao_vetor(diag_fe[0], diag_fe[1])
        p_diag_fd = self.olhar_na_direcao_vetor(diag_fd[0], diag_fd[1])

        # 2. PATHFINDING (Comida ou Cauda - 3 Inputs)
        prox_direcao = self.bfs_proximo_passo(pos_comida)
        if prox_direcao is None:
            prox_direcao = self.bfs_proximo_passo(self.corpo[-1])

        c_frente = 0
        c_esq = 0
        c_dir = 0
        
        if prox_direcao:
            # Traduz direção global para relativa
            if self.direcao == "CIMA":
                if prox_direcao == "CIMA": c_frente = 1
                elif prox_direcao == "ESQUERDA": c_esq = 1
                elif prox_direcao == "DIREITA": c_dir = 1
            elif self.direcao == "BAIXO":
                if prox_direcao == "BAIXO": c_frente = 1
                elif prox_direcao == "DIREITA": c_esq = 1
                elif prox_direcao == "ESQUERDA": c_dir = 1
            elif self.direcao == "ESQUERDA":
                if prox_direcao == "ESQUERDA": c_frente = 1
                elif prox_direcao == "BAIXO": c_esq = 1
                elif prox_direcao == "CIMA": c_dir = 1
            elif self.direcao == "DIREITA":
                if prox_direcao == "DIREITA": c_frente = 1
                elif prox_direcao == "CIMA": c_esq = 1
                elif prox_direcao == "BAIXO": c_dir = 1

        # 3. ESPAÇO LIVRE (Flood Fill - 3 Inputs)
        max_x = comp_tela // tam_quadrado
        max_y = alt_tela // tam_quadrado
        hx, hy = self.cabeca_pos
        
        # Calcula coord absoluta dos vizinhos para rodar flood fill
        fx = (hx + frente[0]) % max_x
        fy = (hy + frente[1]) % max_y
        area_frente = self.calcular_espaco_disponivel(fx, fy)
        
        ex = (hx + esquerda[0]) % max_x
        ey = (hy + esquerda[1]) % max_y
        area_esq = self.calcular_espaco_disponivel(ex, ey)
        
        dx_pos = (hx + direita[0]) % max_x
        dy_pos = (hy + direita[1]) % max_y
        area_dir = self.calcular_espaco_disponivel(dx_pos, dy_pos)

        # 4. Deltas (2 Inputs)
        dx = pos_comida[0] - hx
        dy = pos_comida[1] - hy
        if abs(dx) > max_x / 2: dx = -dx
        if abs(dy) > max_y / 2: dy = -dy

        # TOTAL: 15 INPUTS
        return [
            p_frente, p_esq, p_dir, p_diag_fe, p_diag_fd, 
            c_frente, c_esq, c_dir, 
            area_frente, area_esq, area_dir,
            dx / max_x, dy / max_y, 
            0, 0 # Padding (se config pedir mais)
        ]

    def mover(self, acao_relativa):
        # 0 = Esq, 1 = Reto, 2 = Dir
        ordem_horaria = ["CIMA", "DIREITA", "BAIXO", "ESQUERDA"]
        idx_atual = ordem_horaria.index(self.direcao)

        if acao_relativa == 0: 
            idx_novo = (idx_atual - 1) % 4
            self.direcao = ordem_horaria[idx_novo]
        elif acao_relativa == 2: 
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

# --- LOOP DE TREINAMENTO ---
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

        # --- LÓGICA POR COBRA ---
        for i, cobra in reversed(list(enumerate(cobras))):
            dist_antes = distancia_toroidal(cobra.cabeca_pos, comidas[i].pos)
            cobra.fome -= 1
            
            # IA Decide
            dados_entrada = cobra.inputs(comidas[i].pos)
            output = redes[i].activate(dados_entrada)
            acao = output.index(max(output))

            cobra.mover(acao) 

            dist_depois = distancia_toroidal(cobra.cabeca_pos, comidas[i].pos)

            # Recompensa
            if dist_depois < dist_antes:
                lista_ge[i].fitness += 1.0
            else:
                lista_ge[i].fitness -= 0.1 # Punição baixa para permitir manobras BFS

            lista_ge[i].fitness += 0.05

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
            t1 = fonte_grande.render("MODO TURBO (FULL AI)", True, amarelo)
            t2 = fonte.render(f"Gen: {gen} | Vivos: {len(cobras)}", True, branco)
            janela.blit(t1, (comp_janela//2 - 200, alt_janela//2 - 50))
            janela.blit(t2, (comp_janela//2 - 80, alt_janela//2 + 20))
            pygame.display.flip()

# --- MAIN ---
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    winner = p.run(eval_genomes, 50)
    print('\nMelhor genoma salvo em winner.pkl')
    with open("winner.pkl", "wb") as f:
        pickle.dump(winner, f)

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)