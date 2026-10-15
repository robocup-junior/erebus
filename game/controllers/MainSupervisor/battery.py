"""bateria.py — Módulo de batería reutilizable para supervisores de Erebus.
Incluye soporte para consumo pasivo (sensores) y consumo activo de motores V.2.

Uso básico
----------
En el __init__ del Robot (o cualquier supervisor):

    from bateria import Battery
    self.battery = Battery(robot_num=self._num, rws=self._erebus.rws)

Para activarla (cuando se detecta el componente Battery en el JSON):

    self.battery.configure(max_energy=100)   # activa + ajusta consumo

En el update loop (ej. update_time_elapsed):

    self.battery.update(time_elapsed, vel_left, vel_right)

Para leer el estado desde afuera:

    self.battery.level          # float, % restante (0.0 — 100.0)
    self.battery.active         # bool, True si tiene batería
"""

from __future__ import annotations
import os
from typing import Optional

from ConsoleLog import Console


class Battery:
    """Gestiona el nivel de batería de un robot individual con consumo pasivo y activo (motores).

    Es completamente independiente de la clase Robot: sólo necesita el
    número de robot y una referencia al RobotWindowSender (rws) para
    poder enviar actualizaciones a la ventana HTML.

    Args:
        robot_num (int): Índice del robot (0 o 1).
        rws: Instancia de RobotWindowSender (erebus.rws).
        consumo_por_segundo (float): % descontado por segundo de simulación.
            Por defecto 0.016 (% / s).
    """

    DEFAULT_CONSUMO: float = 0.0     # % por segundo de consumo pasivo base (se calcula de Battery_Per_Step)
    PRINT_INTERVAL: float = 0.2      # intervalo de actualización en segundos (más fluido)

    def __init__(
        self,
        robot_num: int,
        rws,
        consumo_por_segundo: float = DEFAULT_CONSUMO,
    ) -> None:
        self._num: int = robot_num
        self._rws = rws

        self.active: bool = True                # Siempre activa
        self.has_battery_pack: bool = False     # True si tiene el componente Battery en el JSON
        self.level: float = 100.0               # % de batería restante
        self.consumo_por_segundo: float = consumo_por_segundo

        # Parámetros de consumo activo de motores V.2
        self.base_motor_drain_per_step: float = 0.0
        self.motor_drain_per_step: float = 0.0   # % por TIME_STEP (16ms) a vel. max
        self.motor_max_velocity: float = 6.28     # rad/s max

        # Consumo pasivo constante por TIME_STEP (cargado desde Battery_Per_Step)
        self.base_battery_per_step: float = 0.0   # % base cargado desde config
        self.battery_per_step: float = 0.0        # % activo escalado según componentes

        # Tiempo (segundos) parado en un tile de contacto para recargar al 100%
        self.change_battery_time: float = 10.0

        self._last_time: Optional[float] = None        # último step procesado
        self._last_print: Optional[float] = None       # último envío a la UI
        self._last_sent_level: float = 100.0

        self.sensor_costs: dict[str, float] = {}

        self.load_config()

    def load_config(self) -> None:
        """Carga parámetros de configuración de energía si existe sensorEnergyConfig.txt."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "sensorEnergyConfig.txt")
        if not os.path.isfile(config_path):
            return

        self.sensor_costs = {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip().rstrip(",")
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        try:
                            val = float(v.strip())
                            k_norm = k.lower().replace(" ", "").replace("_", "")
                            if k_norm == "motordrainperstep":
                                self.base_motor_drain_per_step = max(0.0, val)
                                self.motor_drain_per_step = self.base_motor_drain_per_step
                            elif k_norm == "motormaxvelocity":
                                self.motor_max_velocity = max(0.1, val)
                            elif k_norm == "batteryperstep":
                                self.base_battery_per_step = max(0.0, val)
                                self.battery_per_step = self.base_battery_per_step
                            elif k_norm in ("battery"):
                                pass
                            elif k_norm == "changebatterytime":
                                self.change_battery_time = max(0.0, val)
                            else:
                                self.sensor_costs[k_norm] = max(0.0, val)
                        except ValueError:
                            pass
        except Exception:
            pass

        # Calcular consumo por segundo base a partir de Battery_Per_Step:
        # Por step (16ms = 0.016s), consume battery_per_step (ej: 0.016%).
        # En 1 segundo (62.5 steps), consume (battery_per_step / 0.016) (ej: 1.0%/s).
        self.consumo_por_segundo = round(self.base_battery_per_step / 0.016, 6)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def configure(
        self,
        has_component: bool = False,
        max_energy: float = 100.0,
        robot_json: Optional[dict] = None
    ) -> None:
        """Configura la batería según si tiene o no el componente Battery y sus sensores.

        - Si NO tiene componente (has_component=False): recibe batería estándar de regalo.
        - Si SÍ tiene componente (has_component=True): consume la mitad (dura el doble).
        - Suma el consumo pasivo individual de cada sensor equipado según sensorEnergyConfig.txt.

        Args:
            has_component (bool): True si el robot equipó el componente Battery.
            max_energy (float): Valor de maxEnergy del componente Battery.
            robot_json (dict, optional): Diccionario del JSON del robot con los componentes equipados.
        """
        self.active = True
        self.has_battery_pack = has_component
        self.level = 100.0
        self._last_time = None
        self._last_print = None
        self._last_sent_level = 100.0

        # Calcular consumo pasivo a partir de los sensores instalados en el JSON
        sensor_drain = 0.0
        if robot_json and isinstance(robot_json, dict):
            for comp_key, comp_val in robot_json.items():
                if isinstance(comp_val, dict):
                    raw_name = comp_val.get("name", "")
                    norm_name = raw_name.lower().replace(" ", "").replace("_", "")
                    if norm_name in self.sensor_costs:
                        cost = self.sensor_costs[norm_name]
                        sensor_drain += cost
                        if cost > 0:
                            Console.log_info(
                                f"[Robot {self._num}] Sensor equipado: {raw_name} ({comp_key}) -> +{cost:.6f} %/s"
                            )

        # Base pasiva = consumo pasivo de Battery_Per_Step + suma de sensores equipados
        base_passive = (self.base_battery_per_step / 0.016) + sensor_drain

        if has_component:
            mult = (100.0 / max_energy) * 0.5
            self.consumo_por_segundo = round(base_passive * mult, 6)
            self.motor_drain_per_step = self.base_motor_drain_per_step * mult
            self.battery_per_step = self.base_battery_per_step * mult
            Console.log_info(
                f"[Robot {self._num}] Batería MEJORADA equipada (maxEnergy={max_energy}). "
                f"Consumo a mitad de velocidad (duración x2): pasivo={self.consumo_por_segundo:.6f} %/s, "
                f"motores={self.motor_drain_per_step:.4f} %/step"
            )
        else:
            self.consumo_por_segundo = round(base_passive, 6)
            self.motor_drain_per_step = self.base_motor_drain_per_step
            self.battery_per_step = self.base_battery_per_step
            Console.log_info(
                f"[Robot {self._num}] Batería ESTÁNDAR de regalo activada. "
                f"Consumo normal: pasivo={self.consumo_por_segundo:.6f} %/s, "
                f"motores={self.motor_drain_per_step:.4f} %/step"
            )

        sim_freq = 1000.0 / 16.0
        motor_max_rate = sim_freq * self.motor_drain_per_step
        total_max = self.consumo_por_segundo + motor_max_rate

    def deactivate(self) -> None:
        """Desactiva la batería."""
        self.active = False
        self.level = 100.0
        self._last_time = None
        self._last_print = None

    def recharge_full(self) -> None:
        """Recarga la batería al 100%."""
        self.level = 100.0

    @property
    def is_depleted(self) -> bool:
        """Indica si la batería está activa y se ha agotado por completo."""
        return self.active and self.level <= 0.0

    def calculate_motor_drain(self, vel_left: float, vel_right: float, dt: float) -> float:
        """Calcula el consumo de energía activo de los motores proporcional a la velocidad."""
        if self.motor_max_velocity <= 0 or dt <= 0:
            return 0.0

        factor = (abs(vel_left) + abs(vel_right)) / (2.0 * self.motor_max_velocity)
        factor = min(1.0, max(0.0, factor))

        sim_freq = 1000.0 / 16.0  # 62.5 Hz (asumiendo TIME_STEP=16ms)
        rate_per_second = sim_freq * self.motor_drain_per_step * factor
        return rate_per_second * dt

    def update(self, time_elapsed: float, vel_left: float = 0.0, vel_right: float = 0.0) -> None:
        """Descuenta batería (pasivo + activo de motores) y envía el nivel actualizado a la ventana HTML.

        Args:
            time_elapsed (float): Tiempo transcurrido de simulación (en segundos).
            vel_left (float): Velocidad angular de la rueda izquierda en rad/s.
            vel_right (float): Velocidad angular de la rueda derecha en rad/s.
        """
        if not self.active:
            return

        # Primer step: inicializar referencias de tiempo
        if self._last_time is None:
            self._last_time = time_elapsed
            self._last_print = time_elapsed
            return

        # Descontar consumo pasivo y activo
        dt: float = time_elapsed - self._last_time
        if dt > 0:
            passive_drain = self.consumo_por_segundo * dt
            motor_drain = self.calculate_motor_drain(vel_left, vel_right, dt)
            total_drain = passive_drain + motor_drain

            self.level -= total_drain
            self.level = max(self.level, 0.0)
            self._last_time = time_elapsed

        # Enviar al HTML si cambió al menos 0.01% o se agotó
        time_to_print = self._last_print is None or (time_elapsed - self._last_print >= self.PRINT_INTERVAL)
        level_changed = abs(self._last_sent_level - self.level) >= 0.01

        if (time_to_print and level_changed) or self.level <= 0.0:
            self._rws.send("batteryUpdate", f"{self._num},{self.level:.2f}")
            self._last_print = time_elapsed
            self._last_sent_level = self.level
