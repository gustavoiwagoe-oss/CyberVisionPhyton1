import cv2
import time


# --------------------------------
# ABRINDO A CÂMERA
# --------------------------------

camera = cv2.VideoCapture(0)


# --------------------------------
# CONFIGURAÇÕES
# --------------------------------

TEMPO_CALIBRACAO = 5

# Margem de erro para considerar
# que o objeto continua sendo o mesmo
MARGEM_TRACKING = 150

TEMPO_PERDA = 2

# Exige que a mudança seja maior para ser considerada um objeto
AREA_MINIMA = 1500 


# --------------------------------
# VARIÁVEIS
# --------------------------------

frame_referencia = None

inicio_calibracao = time.time()

x_anterior = None
y_anterior = None

# Para lembrar o tamanho do objeto quando ele parar
ultima_box = None 

tracking_ativo = False

ultimo_visto = None

status_tracking = "CALIBRANDO"


# --------------------------------
# LOOP PRINCIPAL
# --------------------------------

while True:

    sucesso, frame = camera.read()

    if not sucesso:
        break


    # -----------------------------
    # ESCALA DE CINZA
    # -----------------------------

    frame_cinza = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    # -----------------------------
    # BLUR
    # -----------------------------

    # Kernel maior para "derreter" e ignorar mais ruído da câmera
    frame_cinza = cv2.GaussianBlur(
        frame_cinza,
        (31, 31),
        0
    )


    agora = time.time()


    # --------------------------------
    # CALIBRAÇÃO DO AMBIENTE
    # --------------------------------

    if frame_referencia is None:

        tempo_passado = agora - inicio_calibracao

        status_tracking = "CALIBRANDO"

        cv2.putText(
            frame,
            "Calibrando ambiente...",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow("CyberVision", frame)

        if tempo_passado >= TEMPO_CALIBRACAO:
            frame_referencia = frame_cinza.copy()
            status_tracking = "OFF"

        if cv2.waitKey(1) == 27:
            break

        continue


    # --------------------------------
    # COMPARAÇÃO COM A REFERÊNCIA
    # --------------------------------

    diferenca = cv2.absdiff(
        frame_referencia,
        frame_cinza
    )


    # --------------------------------
    # THRESHOLD
    # --------------------------------

    # Limiar mais rígido (45) para ignorar variações leves de luz/sombra
    _, threshold = cv2.threshold(
        diferenca,
        45,
        255,
        cv2.THRESH_BINARY
    )


    # --------------------------------
    # DILATAÇÃO
    # --------------------------------

    threshold = cv2.dilate(
        threshold,
        None,
        iterations=2
    )


    # --------------------------------
    # CONTORNOS
    # --------------------------------

    contornos, _ = cv2.findContours(
        threshold,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    # --------------------------------
    # FOCO NO MAIOR ALVO (Fim da Caixa Gigante)
    # --------------------------------

    x_min = None
    y_min = None
    x_max = None
    y_max = None

    objeto_encontrado = False
    
    maior_area = 0
    melhor_contorno = None

    # Passo 1: Varrer todos os contornos e achar o maior
    for contorno in contornos:

        area = cv2.contourArea(contorno)

        # Ignora ruídos pequenos baseado na AREA_MINIMA
        if area < AREA_MINIMA:
            continue

        # Se esta área for maior que a maior área que já vimos, elegemos como alvo
        if area > maior_area:
            maior_area = area
            melhor_contorno = contorno
            objeto_encontrado = True

    # Passo 2: Se achamos um alvo digno, extraímos as coordenadas APENAS dele
    if objeto_encontrado:
        x, y, largura, altura = cv2.boundingRect(melhor_contorno)

        x_min = x
        y_min = y
        x_max = x + largura
        y_max = y + altura


    # --------------------------------
    # TRACKING E MEMÓRIA
    # --------------------------------

    if objeto_encontrado:

        centro_x = (x_min + x_max) // 2
        centro_y = (y_min + y_max) // 2

        # Salva a caixa atual na memória para caso o objeto suma
        ultima_box = (x_min, y_min, x_max, y_max) 

        # Primeiro objeto encontrado
        if x_anterior is None:

            tracking_ativo = True
            status_tracking = "ON"

        else:

            diferenca_x = abs(centro_x - x_anterior)
            diferenca_y = abs(centro_y - y_anterior)

            # Dentro da margem de erro
            if diferenca_x <= MARGEM_TRACKING and diferenca_y <= MARGEM_TRACKING:
                tracking_ativo = True
                status_tracking = "ON"
            else:
                # Movimento muito grande: consideramos um novo alvo principal
                tracking_ativo = True
                status_tracking = "NOVO ALVO"

        # Atualiza sempre as posições e o relógio, pois estamos vendo o objeto
        x_anterior = centro_x
        y_anterior = centro_y
        ultimo_visto = agora

    else:

        # Nenhum objeto detectado visualmente. Vamos checar a memória!
        if ultimo_visto is not None:

            tempo_desaparecido = agora - ultimo_visto

            if tempo_desaparecido < TEMPO_PERDA:
                # Objeto sumiu, mas ainda toleramos a perda
                tracking_ativo = True
                status_tracking = "AGUARDANDO"
            else:
                # Tempo esgotou
                tracking_ativo = False
                status_tracking = "OFF"
                
                # Apagamos a memória
                x_anterior = None
                y_anterior = None
                ultima_box = None 
        else:
            tracking_ativo = False
            status_tracking = "OFF"


    # --------------------------------
    # DESENHAR O OBJETO
    # --------------------------------
    
    # Só desenhamos se o tracking_ativo for True E tivermos uma memória da caixa
    if tracking_ativo and ultima_box is not None:
        
        # Desempacota a memória
        box_x_min, box_y_min, box_x_max, box_y_max = ultima_box

        # Feedback visual de status de tracking
        if status_tracking == "AGUARDANDO":
            cor_caixa = (0, 255, 255) # Amarelo em BGR (Perda temporária)
        elif status_tracking == "NOVO ALVO":
            cor_caixa = (0, 0, 255)   # Vermelho em BGR (Troca de alvo)
        else:
            cor_caixa = (0, 255, 0)   # Verde em BGR (Tracking estável ON)

        cv2.rectangle(
            frame,
            (box_x_min, box_y_min),
            (box_x_max, box_y_max),
            cor_caixa,
            3
        )


    # --------------------------------
    # HUD
    # --------------------------------

    cv2.putText(
        frame,
        f"Tracking: {status_tracking}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )


    # --------------------------------
    # MOSTRAR IMAGEM
    # --------------------------------

    cv2.imshow(
        "CyberVision",
        frame
    )


    # --------------------------------
    # ESC
    # --------------------------------

    if cv2.waitKey(1) == 27:
        break


# --------------------------------
# ENCERRAMENTO
# --------------------------------

camera.release()
cv2.destroyAllWindows()