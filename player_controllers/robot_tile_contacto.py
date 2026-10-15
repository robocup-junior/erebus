"""robot_tile_contacto.py
Controlador para robot en Webots / Erebus.

Comportamiento:
1. Avanza hacia adelante.
2. Lee el sensor de color ('colour_sensor') apuntando al piso.
3. Al detectar el color cyan del tile de contacto (RGB ~ 0, 162, 162):
   - Avanza un breve instante para centrarse bien dentro del tile.
   - Se detiene completamente durante el tiempo configurado en TIEMPO_EN_TILE.
4. Tras cumplirse el tiempo, puede reanudar la marcha o quedarse detenido.
"""

from controller import Robot, Camera

# ==============================================================================
# VARIABLES DE CONFIGURACIÓN (Ajusta estos valores según lo que necesites)
# ==============================================================================

# Tiempo (en segundos de simulación) que el robot debe quedarse detenido en el tile:
TIEMPO_EN_TILE = 12.0

# Velocidad de avance de las ruedas en rad/s (máx reglamentario suele ser 6.28):
VELOCIDAD_AVANCE = 2.0

# Tiempo (en segundos) que avanza tras detectar el color para meterse bien al centro del tile:
TIEMPO_ACOMODARSE = 0.5

# Si es True, el robot vuelve a avanzar hacia adelante una vez cumplido el tiempo.
# Si es False, el robot se queda quieto para siempre una vez cambiado el pack.
REANUDAR_DESPUES_DE_TIEMPO = True

# Cada cuántos segundos de simulación imprimir en consola la lectura del sensor de color:
INTERVALO_DEBUG_COLOR = 1.0


# ==============================================================================
# FUNCIONES AUXILIARES DE COLOR
# ==============================================================================

def es_tile_contacto(r: int, g: int, b: int) -> bool:
    """
    Detecta si el color RGB corresponde al tile de contacto (Cyan: diffuseColor 0 0.635 0.635).
    En Webots se lee con:
      - R (rojo) muy bajo (< 70)
      - G (verde) alto (> 90)
      - B (azul) alto (> 90)
      - Tanto G como B son significativamente mayores que R.
    """
    return (r < 70) and (g > 90) and (b > 90) and (g - r > 40) and (b - r > 40)


def leer_rgb(sensor):
    """Obtiene los valores R, G, B (0 a 255) de la cámara o colour_sensor de 1x1."""
    img = sensor.getImage()
    if img is None:
        return None
    try:
        r = Camera.imageGetRed(img, 1, 0, 0)
        g = Camera.imageGetGreen(img, 1, 0, 0)
        b = Camera.imageGetBlue(img, 1, 0, 0)
        return r, g, b
    except Exception:
        # Lectura alternativa directa de bytes BGRA de Webots
        b = img[0]
        g = img[1]
        r = img[2]
        return r, g, b


# ==============================================================================
# INICIALIZACIÓN DE WEBOTS
# ==============================================================================

robot = Robot()
time_step = int(robot.getBasicTimeStep())

# Motores de las ruedas
motor_izq = robot.getDevice("wheel1 motor")
motor_der = robot.getDevice("wheel2 motor")

if motor_izq is None:
    motor_izq = robot.getDevice("wheel1")
if motor_der is None:
    motor_der = robot.getDevice("wheel2")

if motor_izq is None or motor_der is None:
    print("[ERROR] No se encontraron los dispositivos de motor 'wheel1 motor'/'wheel2 motor'.")
else:
    # Modo de control por velocidad (posición infinita)
    motor_izq.setPosition(float('inf'))
    motor_der.setPosition(float('inf'))
    motor_izq.setVelocity(0.0)
    motor_der.setVelocity(0.0)

# Sensor de color mirando al piso
colour_sensor = robot.getDevice("colour_sensor")
if colour_sensor is None:
    colour_sensor = robot.getDevice("camera")

if colour_sensor is not None:
    colour_sensor.enable(time_step)
    print("-> Sensor de color ('colour_sensor') habilitado correctamente.")
else:
    print("[ADVERTENCIA] No se encontró el dispositivo 'colour_sensor'. Verifica el robot en el mapa.")


def fijar_velocidad(v_izq: float, v_der: float):
    if motor_izq and motor_der:
        motor_izq.setVelocity(v_izq)
        motor_der.setVelocity(v_der)


# ==============================================================================
# MÁQUINA DE ESTADOS Y BUCLE PRINCIPAL
# ==============================================================================

# Estados posibles:
# 'BUSCANDO'   : Avanza derecho buscando el tile de contacto.
# 'ENTRANDO'   : Avanza unos instantes más para centrarse dentro del tile.
# 'DETENIDO'   : Quieto dentro del tile durante TIEMPO_EN_TILE segundos.
# 'COMPLETADO' : Ya cumplió la parada en el tile.
estado = "BUSCANDO"

tiempo_inicio_entrada = None
tiempo_inicio_parada = None
ultimo_debug_tiempo = 0.0

print(f"\n=======================================================")
print(f" Robot iniciado en modo búsqueda de Tile de Contacto")
print(f" Tiempo configurado para quedarse: {TIEMPO_EN_TILE} segundos")
print(f" Velocidad de avance: {VELOCIDAD_AVANCE} rad/s")
print(f"=======================================================\n")

# Inicia avanzando hacia adelante
fijar_velocidad(VELOCIDAD_AVANCE, VELOCIDAD_AVANCE)

while robot.step(time_step) != -1:
    current_time = robot.getTime()

    # Lectura del color del piso
    color_actual = leer_rgb(colour_sensor) if colour_sensor else None

    # Mostrar lectura de color periódicamente para facilitar calibración
    if current_time - ultimo_debug_tiempo >= INTERVALO_DEBUG_COLOR:
        if color_actual:
            r, g, b = color_actual
            es_contacto = es_tile_contacto(r, g, b)
            tag = " [CYAN CONTACTO]" if es_contacto else ""
            print(f"[{current_time:.1f}s] Sensor Color RGB: ({r}, {g}, {b}){tag} | Estado: {estado}")
        ultimo_debug_tiempo = current_time

    # --------------------------------------------------------------------------
    # 1. ESTADO: BUSCANDO
    # --------------------------------------------------------------------------
    if estado == "BUSCANDO":
        fijar_velocidad(VELOCIDAD_AVANCE, VELOCIDAD_AVANCE)

        if color_actual:
            r, g, b = color_actual
            if es_tile_contacto(r, g, b):
                print(f"\n[{current_time:.2f}s] ¡Tile de contacto detectado! (RGB: {r}, {g}, {b})")
                print(f"Avanzando {TIEMPO_ACOMODARSE}s para acomodarse en el centro del tile...")
                tiempo_inicio_entrada = current_time
                estado = "ENTRANDO"

    # --------------------------------------------------------------------------
    # 2. ESTADO: ENTRANDO (Centrándose en el tile)
    # --------------------------------------------------------------------------
    elif estado == "ENTRANDO":
        fijar_velocidad(VELOCIDAD_AVANCE, VELOCIDAD_AVANCE)

        if current_time - tiempo_inicio_entrada >= TIEMPO_ACOMODARSE:
            # Frenar por completo
            fijar_velocidad(0.0, 0.0)
            tiempo_inicio_parada = current_time
            estado = "DETENIDO"
            print(f"[{current_time:.2f}s] Robot detenido en el tile.")
            print(f"Permaneciendo quieto durante {TIEMPO_EN_TILE} segundos para cambio de batería...\n")

    # --------------------------------------------------------------------------
    # 3. ESTADO: DETENIDO (Esperando que se cumpla el tiempo para la recarga)
    # --------------------------------------------------------------------------
    elif estado == "DETENIDO":
        fijar_velocidad(0.0, 0.0)

        tiempo_detenido = current_time - tiempo_inicio_parada

        if tiempo_detenido >= TIEMPO_EN_TILE:
            print(f"\n[{current_time:.2f}s] ¡Tiempo completado ({tiempo_detenido:.1f}s >= {TIEMPO_EN_TILE}s)!")
            print("Batería cambiada al 100%.")

            if REANUDAR_DESPUES_DE_TIEMPO:
                print(f"Reanudando marcha hacia adelante a {VELOCIDAD_AVANCE} rad/s...\n")
                fijar_velocidad(VELOCIDAD_AVANCE, VELOCIDAD_AVANCE)
            else:
                print("Robot permanece detenido en el tile.\n")

            estado = "COMPLETADO"

    # --------------------------------------------------------------------------
    # 4. ESTADO: COMPLETADO
    # --------------------------------------------------------------------------
    elif estado == "COMPLETADO":
        if REANUDAR_DESPUES_DE_TIEMPO:
            fijar_velocidad(VELOCIDAD_AVANCE, VELOCIDAD_AVANCE)
        else:
            fijar_velocidad(0.0, 0.0)
