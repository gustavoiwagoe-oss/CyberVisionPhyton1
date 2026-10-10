# 👁️ CyberVision

A filosofia central do projeto é o **Minimalismo Visual com Inteligência de Back-end**: o sistema escaneia o ambiente, processa dezenas de variáveis, mas entrega ao usuário apenas a informação estritamente necessária (ex: bounding boxes precisas e status de tracking limpos), sem poluir a tela com dados inúteis.

Atualmente, o projeto é um protótipo focado em **Detecção de Movimento e Tracking Passivo com Memória**, construído inteiramente com lógica matemática e processamento de imagem, preparando o terreno para a futura integração de Inteligência Artificial (YOLO).

---

## 🛠️ Tecnologias Utilizadas
* **Python 3.x**
* **OpenCV (`cv2`)** - Biblioteca principal de Visão Computacional.
* **NumPy** - Para processamento de matrizes sob o capô do OpenCV.

---

## 🧠 Como o Código Funciona (Pipeline Explicado)

Para fins didáticos, o código foi construído etapa por etapa. Abaixo está o significado de cada função chave do OpenCV utilizada no nosso pipeline, para que qualquer pessoa consiga entender como o computador "enxerga" o movimento.

### 1. Captura e Simplificação
* `cv2.VideoCapture(0)`: Abre a comunicação com a webcam padrão do computador. O "vídeo" que vemos é, na verdade, um loop infinito processando frame a frame.
* `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)`: Converte a imagem colorida para **escala de cinza**.
  * *Por que usamos?* A cor não importa para detectar movimento. Uma imagem em preto e branco tem 1 canal de cor em vez de 3, o que deixa o processamento matemático muito mais leve e rápido.

### 2. Filtro de Ruído
* `cv2.GaussianBlur(frame_cinza, (31, 31), 0)`: Aplica um desfoque na imagem.
  * *Por que usamos?* Câmeras geram ruído (granulação) e captam leves oscilações de luz. O Blur "derrete" esses pequenos ruídos, impedindo que o sistema ache que a parede está se mexendo.

### 3. Calibração e Detecção
* `cv2.absdiff(frame_referencia, frame_cinza)`: Calcula a diferença absoluta entre o cenário vazio (calibrado nos 5 primeiros segundos) e o frame atual.
  * *Por que usamos?* Em vez de comparar apenas o frame atual com o frame anterior (o que faria o objeto "sumir" se parasse de se mexer), comparamos com o fundo. Assim, mesmo parado, o objeto intruso continua sendo detectado.
* `cv2.threshold(diferenca, 45, 255, cv2.THRESH_BINARY)`: Transforma a imagem de diferenças em uma imagem estritamente Binária (Preto e Branco puro).
  * *Como funciona:* Se um pixel mudou mais que `45` tons de cinza em relação ao fundo, ele vira Branco (255). Se mudou menos, vira Preto (0). Isso destaca exatamente onde está o movimento.

### 4. Tratamento de Formas
* `cv2.dilate(threshold, None, iterations=2)`: Expande as manchas brancas da imagem binária.
  * *Por que usamos?* Quando movemos uma mão, os dedos podem aparecer como 5 manchas separadas. A dilatação "incha" essas manchas para que elas se fundam em um único grande bloco branco, facilitando o tracking.
* `cv2.findContours(...)`: Analisa a imagem binária e desenha contornos em volta de todas as manchas brancas (movimentos).
* `cv2.contourArea(contorno)`: Calcula o tamanho (área em pixels) de cada contorno encontrado.
  * *Por que usamos?* É o nosso filtro principal. Se a área for menor que `1500`, o sistema ignora, considerando que é apenas um reflexo ou sombra (ruído).

### 5. Foco e Desenho
* `cv2.boundingRect(melhor_contorno)`: Calcula as coordenadas perfeitas `(x, y, largura, altura)` para desenhar um retângulo exato em volta do nosso contorno principal.
* `cv2.rectangle(...)` e `cv2.putText(...)`: Funções de front-end para desenhar a *bounding box* verde/amarela e escrever os textos de status na tela (Nossa HUD).

---

## 🎯 A Lógica do Tracking (Memória de Alvo)

O grande diferencial deste protótipo não é apenas achar movimento, mas **acompanhá-lo de forma inteligente**. O sistema possui as seguintes lógicas:

1. **Foco no Maior Alvo:** O algoritmo varre todos os contornos da tela e ignora movimentos secundários, focando matematicamente sempre no objeto que possui a maior área.
2. **Memória de Posição (`ultima_box`):** Quando o alvo é detectado, o sistema salva suas coordenadas. 
3. **Tolerância a Perda (`TEMPO_PERDA`):** Se o objeto for parcialmente escondido ou parar de gerar diferença na câmera, o sistema não pisca ou desliga instantaneamente. Ele entra no estado `"AGUARDANDO"`, pinta a caixa de Amarelo e congela na última posição por 2 segundos antes de desativar, garantindo estabilidade no rastreio.
4. **Troca de Alvo:** Se o centro matemático do objeto der um "salto" maior que a `MARGEM_TRACKING`, o sistema compreende que é um novo alvo e notifica na interface (`"NOVO ALVO"` em Vermelho).

---

## 🚀 Roadmap (Próximos Passos)

O projeto está sendo construído em módulos escaláveis. Nossos próximos passos incluem:

- [ ] **Lock Target (F10):** Permitir que o usuário trave o rastreio em um alvo específico, ignorando novos movimentos.
- [ ] **Integração com IA (YOLO):** Substituir a detecção cega de pixels por detecção semântica (Saber que a mancha é um "Notebook" ou uma "Pessoa").
- [ ] **Target Hunt (Template Matching):** Capacidade de alimentar o sistema com a foto de um alvo e fazê-lo caçar esse padrão no ambiente.
- [ ] **Sistema de Menus HUD:** Mapeamento das teclas (F1 a F9) para ativar/desativar OCR, Inteligência Artificial, e Visão Noturna apenas quando solicitado.
- [ ] **Hardware Embarcado:** Migrar o *CyberVision Core* para um Raspberry Pi com sistema Linux, tornando o projeto autônomo, offline e acoplável a um dispositivo vestível (óculos inteligente).

---

## 💻 Como Rodar o Projeto

1. Clone este repositório.
2. Crie um ambiente virtual (recomendado).
3. Instale as dependências:
   ```bash
   pip install opencv-python numpy
