"""
DIGITAL TWIN - TANQUE DE PISCICULTURA

Modelo dinâmico simplificado de:
- temperatura da água
- oxigênio dissolvido (OD)
- pH
- amônia total (TAN)
- NH3 não ionizada
- nível da água
- biomassa
- alimentação
- aeração
- entrada de água

O modelo utiliza:
- hora real
- dia do ano
- estação do ano
- hemisfério
- fotoperíodo
- ciclo solar aproximado
- inércia térmica da água
- fotossíntese
- respiração
- consumo de oxigênio pelos peixes
- influência da temperatura
- influência da alimentação
- relação pH/temperatura/amônia
- controle automático dos aeradores

IMPORTANTE:
Este é um modelo de engenharia/simulação.
Para operar um tanque real, os parâmetros precisam ser
calibrados com dados reais da propriedade.
"""

from influxdb_client_3 import InfluxDBClient3, Point

import math
import random
import time

from dataclasses import dataclass
from datetime import datetime, timedelta


# ============================================================
# CONFIGURAÇÃO INFLUXDB
# ============================================================

HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "7nrflevA_ZN2YGy57rSJu2YxtyidVzsZQYDROoHZSQI6F2mIixMRVdKo2rxMrZIIB6hpOTmOVB5OKYwNkYcsWw=="
ORG = "Fish"
DATABASE = "fishfarm_sim"

client = InfluxDBClient3(
host=HOST,
token=TOKEN,
org=ORG,
database=DATABASE
)


# ============================================================
# CONFIGURAÇÃO DO TANQUE
# ============================================================

@dataclass
class TankConfig:

    tank_id: str = "TANK_01"

    # --------------------------------------------------------
    # GEOGRAFIA
    # --------------------------------------------------------

    latitude: float = -25.43
    longitude: float = -49.27

    # Brasil -> hemisfério Sul
    hemisphere: str = "south"

    # --------------------------------------------------------
    # TANQUE
    # --------------------------------------------------------

    # GEOMETRIA REAL

    length_m: float = 150.0

    width_m: float = 16.0

    depth_m: float = 2.0

    area_m2: float = 2400.0

    volume_liters: float = 4800000.0

    # --------------------------------------------------------
    # PEIXES
    # --------------------------------------------------------

    # ESTOCAGEM

    fish_per_m2: float = 30.0

    initial_weight_g: float = 30.0
    fish_count: int = int(area_m2 * fish_per_m2)

    # GOMPERTZ

    gompertz_A: float = 1200.0

    gompertz_B: float = 3.6889

    gompertz_k: float = 0.0085

    # consumo aproximado de O2 por kg de biomassa/h
    fish_o2_rate: float = 0.015

    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------

    # temperatura ambiental média por estação
    seasonal_temperature = {
    "summer": 24.0,
    "autumn": 19.0,
    "winter": 16.0,
    "spring": 21.0
    }

    # amplitude térmica diária
    daily_temperature_amplitude = 4.0

    # velocidade de resposta da água
    # menor = maior inércia térmica
    thermal_response = 0.035

    # --------------------------------------------------------
    # OXIGÊNIO
    # --------------------------------------------------------

    # OD inicial
    initial_do: float = 6.5

    # produção máxima de O2 pela fotossíntese
    photosynthesis_rate: float = 0.020

    # respiração base
    respiration_rate: float = 0.010

    # troca de oxigênio com atmosfera
    reaeration_rate: float = 0.015

    # capacidade máxima dos aeradores
    aerator_capacity: float = 1.50

    # --------------------------------------------------------
    # PH
    # --------------------------------------------------------

    initial_ph: float = 7.4

    # sensibilidade do pH à fotossíntese
    ph_photosynthesis_effect: float = 0.015

    # sensibilidade do pH à respiração
    ph_respiration_effect: float = 0.010

    # retorno lento para pH de equilíbrio
    ph_stabilization: float = 0.002

    target_ph: float = 7.4

    # --------------------------------------------------------
    # AMÔNIA
    # --------------------------------------------------------

    initial_tan: float = 0.20

    # produção de TAN por kg de biomassa/h
    ammonia_production_rate: float = 0.00010

    # nitrificação
    nitrification_rate: float = 0.003

    # --------------------------------------------------------
    # NÍVEL
    # --------------------------------------------------------

    initial_water_level: float = 95.0

    # evaporação média diária
    evaporation_per_day: float = 0.15

    # entrada de água
    inlet_rate: float = 0.20

    # --------------------------------------------------------
    # ALIMENTAÇÃO
    # --------------------------------------------------------

    feed_rate_percent: float = 0.025

    # --------------------------------------------------------
    # CONTROLE
    # --------------------------------------------------------

    aerator_on_do: float = 5.0

    aerator_off_do: float = 7.0
CONFIG = TankConfig()


# ============================================================
# VELOCIDADE DA SIMULAÇÃO
# ============================================================

REAL_TIME_MODE = False

# 1 minuto real = 1 dia simulado
SIMULATION_SPEED = 1440

# ============================================================
# ESTADO DO DIGITAL TWIN
# ============================================================

@dataclass
class TankState:

    temperature: float
    do: float
    ph: float
    tan: float
    water_level: float

    fish_count: int

    average_weight_g: float

    biomass_kg: float

    age_days: float = 0.0

    aerator_1: int = 0
    aerator_2: int = 0
    aerator_3: int = 0

    feeder: int = 0

    inlet_valve: float = 0.0

    cumulative_feed_kg: float = 0.0


state = TankState(
temperature=22.0,
do=CONFIG.initial_do,
ph=CONFIG.initial_ph,
tan=CONFIG.initial_tan,
water_level=CONFIG.initial_water_level,

fish_count=CONFIG.fish_count,

average_weight_g=CONFIG.initial_weight_g,

biomass_kg=(
    CONFIG.fish_count
    * CONFIG.initial_weight_g
) / 1000
)


# ============================================================
# UTILIDADES
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def gaussian_noise(std):
    return random.gauss(0, std)


# ============================================================
# GOMPERTZ
# ============================================================

def gompertz_weight(days):

    return (
        CONFIG.gompertz_A
        * math.exp(
            -CONFIG.gompertz_B
            * math.exp(
                -CONFIG.gompertz_k
                * days
            )
        )
    )

# ============================================================
# ESTAÇÃO DO ANO
# ============================================================

def get_season(now=None):

    if now is None:
        now = datetime.now()

    month = now.month

    if CONFIG.hemisphere == "south":

        if month in (12, 1, 2):
            return "summer"

        elif month in (3, 4, 5):
            return "autumn"

        elif month in (6, 7, 8):
            return "winter"

        else:
            return "spring"

    else:

        if month in (12, 1, 2):
            return "winter"

        elif month in (3, 4, 5):
            return "spring"

        elif month in (6, 7, 8):
            return "summer"

        else:
            return "autumn"

# ============================================================
# DIA DO ANO
# ============================================================

def get_day_of_year(now):

    return now.timetuple().tm_yday


# ============================================================
# CICLO SOLAR
# ============================================================

def get_solar_factor(now):

    """
    Aproximação simplificada da radiação solar.

    0 = noite
    1 = máximo solar

    O modelo utiliza aproximadamente:
    nascer: 06:00
    máximo: 12:00
    pôr: 18:00
    """

    hour = (
        now.hour
        + now.minute / 60
        + now.second / 3600
    )

    sunrise = 6.0
    sunset = 18.0

    if hour <= sunrise or hour >= sunset:
        return 0.0

    x = math.pi * (hour - sunrise) / (sunset - sunrise)

    return max(0.0, math.sin(x))


# ============================================================
# FOTOPERÍODO SAZONAL
# ============================================================
def get_photoperiod_factor(now):

    """
    Pequena variação anual do comprimento do dia.

    É uma aproximação.
    Para máxima precisão, posteriormente podemos substituir
    por cálculo astronômico baseado em latitude.
    """

    day = get_day_of_year(now)

    seasonal = math.sin(
        2 * math.pi * (day - 80) / 365
    )

    return clamp(
        0.75 + 0.25 * seasonal,
        0.45,
        1.0
    )


# ============================================================
# TEMPERATURA AMBIENTE TEÓRICA
# ============================================================

def get_air_temperature(now):

    season = get_season(now)

    seasonal_average = CONFIG.seasonal_temperature[season]

    hour = (
        now.hour
        + now.minute / 60
    )

    # mínimo aproximadamente 06h
    # máximo aproximadamente 15h

    daily_cycle = (
        CONFIG.daily_temperature_amplitude
        * math.sin(
            2 * math.pi * (hour - 9) / 24
        )
    )

    # pequena variação anual
    day = get_day_of_year(now)

    annual_cycle = 2.0 * math.sin(
        2 * math.pi * (day - 20) / 365
    )

    return (
        seasonal_average
        + daily_cycle
        + annual_cycle
        + gaussian_noise(0.10)
    )

# ============================================================
# TEMPERATURA DA ÁGUA
# ============================================================

def update_water_temperature(state, now, dt_hours):

    air_temperature = get_air_temperature(now)

    solar = get_solar_factor(now)

    # aquecimento pela radiação
    solar_heating = (
        solar
        * 0.08
        * dt_hours
    )

    # transferência térmica ar -> água
    thermal_exchange = (
        CONFIG.thermal_response
        * (air_temperature - state.temperature)
        * dt_hours
    )

    delta_temperature = (
        thermal_exchange
        + solar_heating
    )

    state.temperature += delta_temperature

    state.temperature = clamp(
        state.temperature,
        10.0,
        40.0
    )


# ============================================================
# SATURAÇÃO DE OXIGÊNIO
# ============================================================

def oxygen_saturation_temperature(temp):

    """
    Aproximação para água doce ao nível do mar.

    O objetivo aqui é criar um modelo dinâmico.
    Para uso operacional devemos incluir:

    altitude
    salinidade
    pressão atmosférica
    """

    # aproximação simplificada
    saturation = (
        14.6
        - 0.41 * temp
        + 0.008 * temp ** 2
    )

    return max(4.0, saturation)


# ============================================================
# FOTOSSÍNTESE
# ============================================================
def calculate_photosynthesis(state, now):

    solar = get_solar_factor(now)

    photoperiod = get_photoperiod_factor(now)

    temperature_factor = clamp(
        1.0 - abs(state.temperature - 27.0) / 20.0,
        0.0,
        1.0
    )

    photosynthesis = (
        CONFIG.photosynthesis_rate
        * solar
        * photoperiod
        * temperature_factor
    )

    return photosynthesis


# ============================================================
# RESPIRAÇÃO
# ============================================================

def calculate_respiration(state):

    """
    Respiração aumenta com temperatura.

    Q10 simplificado:
    aumento de 10 °C -> aproximadamente dobra
    a taxa metabólica.
    """

    q10 = 2.0

    temperature_factor = q10 ** (
        (state.temperature - 25.0) / 10.0
    )

    fish_respiration = (
        CONFIG.fish_o2_rate
        * state.biomass_kg
        * temperature_factor
        / CONFIG.volume_liters
        * 1000
    )

    background_respiration = (
        CONFIG.respiration_rate
        * temperature_factor
    )

    return (
        fish_respiration
        + background_respiration
    )


# ============================================================
# CONTROLE DOS AERADORES
# ============================================================
def control_aeration(state):

    if state.do < CONFIG.aerator_on_do:

        state.aerator_1 = 1

    elif state.do > CONFIG.aerator_off_do:

        state.aerator_1 = 0

    # segundo aerador em situação crítica
    if state.do < 4.0:

        state.aerator_2 = 1

    elif state.do > 5.5:

        state.aerator_2 = 0

    # terceiro aerador em emergência
    if state.do < 3.0:

        state.aerator_3 = 1

    elif state.do > 5.0:

        state.aerator_3 = 0

# ============================================================
# OXIGÊNIO DISSOLVIDO
# ============================================================

def update_dissolved_oxygen(state, now, dt_hours):

    photosynthesis = calculate_photosynthesis(
        state,
        now
    )

    respiration = calculate_respiration(
        state
    )

    saturation = oxygen_saturation_temperature(
        state.temperature
    )

    # troca natural com atmosfera
    atmospheric_exchange = (
        CONFIG.reaeration_rate
        * (saturation - state.do)
    )

    # aeradores
    number_of_aerators = (
        state.aerator_1
        + state.aerator_2
        + state.aerator_3
    )

    mechanical_aeration = (
        number_of_aerators
        * CONFIG.aerator_capacity
    )

    delta_do = (
        photosynthesis
        + atmospheric_exchange
        + mechanical_aeration
        - respiration
    )

    state.do += delta_do * dt_hours

    # ruído de sensor/modelo
    state.do += gaussian_noise(0.015)

    state.do = clamp(
        state.do,
        0.0,
        saturation + 3.0
    )


# ============================================================
# ALIMENTAÇÃO
# ============================================================

def feeding_schedule(now):

    """
    Exemplo:
    08:00
    13:00
    18:00

    Posteriormente isso pode vir do PLC,
    calendário ou sistema real de alimentação.
    """

    hour = now.hour
    minute = now.minute

    feeding_hours = [8, 13, 18]

    if hour in feeding_hours and minute == 0:
        return True

    return False


def execute_feeding(state, now):

    if feeding_schedule(now):

        daily_feed = (
            state.biomass_kg
            * CONFIG.feed_rate_percent
        )

        feed_event = daily_feed / 3.0

        state.cumulative_feed_kg += feed_event

        state.feeder = 1

        return feed_event

    state.feeder = 0

    return 0.0

# ============================================================
# AMÔNIA
# ============================================================
def update_ammonia(
    state,
    feed_kg,
    dt_hours
):

    # produção metabólica
    biomass_ammonia = (
        CONFIG.ammonia_production_rate
        * state.biomass_kg
    )

    # alimentação aumenta carga orgânica
    feed_ammonia = (
        feed_kg
        * 0.005
    )

    production = (
        biomass_ammonia
        + feed_ammonia
    )

    # nitrificação aumenta com temperatura
    temperature_factor = 1.07 ** (
        state.temperature - 25.0
    )

    nitrification = (
        CONFIG.nitrification_rate
        * state.tan
        * temperature_factor
    )

    state.tan += (
        production
        - nitrification
    ) * dt_hours

    state.tan += gaussian_noise(0.0005)

    state.tan = clamp(
        state.tan,
        0.0,
        10.0
    )


# ============================================================
# FRAÇÃO DE NH3 NÃO IONIZADA
# ============================================================

def calculate_un_ionized_ammonia(
    temperature,
    ph,
    tan
):

    """
    Aproximação baseada no equilíbrio:

    NH4+ <-> NH3 + H+

    A fração tóxica aumenta com:
    temperatura
    pH

    TAN = NH3 + NH4+
    """

    pKa = (
        0.09018
        + 2729.92 / (temperature + 273.15)
    )

    fraction_nh3 = (
        1.0
        / (
            1.0
            + 10 ** (pKa - ph)
        )
    )

    nh3 = tan * fraction_nh3

    return nh3


# ============================================================
# PH
# ============================================================

def update_ph(state, now, dt_hours):

    solar = get_solar_factor(now)

    # fotossíntese tende a aumentar pH
    photosynthesis_effect = (
        solar
        * CONFIG.ph_photosynthesis_effect
    )

    # respiração tende a reduzir pH
    respiration_effect = (
        calculate_respiration(state)
        * CONFIG.ph_respiration_effect
    )

    stabilization = (
        CONFIG.target_ph - state.ph
    ) * CONFIG.ph_stabilization

    state.ph += (
        photosynthesis_effect
        - respiration_effect
        + stabilization
    ) * dt_hours

    state.ph += gaussian_noise(0.003)

    state.ph = clamp(
        state.ph,
        5.5,
        10.0
    )

# ============================================================
# NÍVEL DA ÁGUA
# ============================================================

def update_water_level(state, now, dt_hours):

    # evaporação
    evaporation = (
        CONFIG.evaporation_per_day
        / 24.0
        * dt_hours
    )

    state.water_level -= evaporation

    # controle automático da entrada

    if state.water_level < 85:

        state.inlet_valve = 80

    elif state.water_level < 90:

        state.inlet_valve = 40

    else:

        state.inlet_valve = 0

    water_in = (
        CONFIG.inlet_rate
        * state.inlet_valve
        / 100
        * dt_hours
    )

    state.water_level += water_in

    state.water_level = clamp(
        state.water_level,
        70,
        100
    )


# ============================================================
# BIOMASSA
# ============================================================
def update_biomass(state, dt_hours):

    temperature_factor = clamp(
        1.0 - abs(state.temperature - 27.0) / 15.0,
        0.0,
        1.0
    )

    oxygen_factor = clamp(
        (state.do - 2.0) / 4.0,
        0.0,
        1.0
    )

    nh3 = calculate_un_ionized_ammonia(
        state.temperature,
        state.ph,
        state.tan
    )

    ammonia_factor = clamp(
        1.0 - nh3 / 0.5,
        0.0,
        1.0
    )

    environment_factor = (
        temperature_factor
        * oxygen_factor
        * ammonia_factor
    )

    state.age_days += (
        dt_hours
        / 24.0
        * environment_factor
    )

    state.average_weight_g = (
        gompertz_weight(
            state.age_days
        )
    )

    state.biomass_kg = (
        state.fish_count
        * state.average_weight_g
    ) / 1000
    
# ============================================================
# CICLO COMPLETO DO DIGITAL TWIN
# ============================================================

def update_digital_twin(state, now, dt_hours):

    # 1. Temperatura
    update_water_temperature(
        state,
        now,
        dt_hours
    )

    # 2. Alimentação
    feed_kg = execute_feeding(
        state,
        now
    )

    # 3. Controle dos aeradores
    control_aeration(
        state
    )

    # 4. Oxigênio dissolvido
    update_dissolved_oxygen(
        state,
        now,
        dt_hours
    )

    # 5. Amônia
    update_ammonia(
        state,
        feed_kg,
        dt_hours
    )

    # 6. pH
    update_ph(
        state,
        now,
        dt_hours
    )

    # 7. Nível da água
    update_water_level(
        state,
        now,
        dt_hours
    )

    # 8. Biomassa
    update_biomass(
        state,
        dt_hours
    )

# ============================================================
# STATUS DO SISTEMA
# ============================================================

def get_system_status(state):

    nh3 = calculate_un_ionized_ammonia(
        state.temperature,
        state.ph,
        state.tan
    )

    if state.do < 3:

        oxygen_status = "CRITICAL"

    elif state.do < 5:

        oxygen_status = "LOW"

    elif state.do > 10:

        oxygen_status = "HIGH"

    else:

        oxygen_status = "NORMAL"

    if nh3 > 0.5:

        ammonia_status = "CRITICAL"

    elif nh3 > 0.2:

        ammonia_status = "HIGH"

    else:

        ammonia_status = "NORMAL"

    return (
        oxygen_status,
        ammonia_status,
        nh3
    )

# ============================================================
# GRAVAÇÃO INFLUXDB
# ============================================================

def write_to_influx(state, now):

    season = get_season(now)

    solar = get_solar_factor(now)

    photoperiod = get_photoperiod_factor(now)

    air_temperature = get_air_temperature(now)

    nh3 = calculate_un_ionized_ammonia(
        state.temperature,
        state.ph,
        state.tan
    )

    oxygen_saturation = oxygen_saturation_temperature(
        state.temperature
    )

    oxygen_status, ammonia_status, _ = (
        get_system_status(state)
    )

    point = (
        Point("tank_state")
        .time(datetime.utcnow().isoformat())

        .tag("tank", CONFIG.tank_id)
        .tag("season", season)
        .tag("oxygen_status", oxygen_status)
        .tag("ammonia_status", ammonia_status)

        .field("air_temperature", round(air_temperature, 2))
        .field("solar_factor", round(solar, 4))
        .field("photoperiod_factor", round(photoperiod, 4))

        .field("temperature", round(state.temperature, 3))

        .field("do", round(state.do, 3))

        .field(
            "dissolved_oxygen",
            round(state.do, 3)
        )

        .field(
            "do_saturation",
            round(oxygen_saturation, 3)
        )

        .field(
            "do_saturation_percent",
            round(
                100 * state.do / oxygen_saturation,
                2
            )
        )

        .field("ph", round(state.ph, 3))

        .field("tan", round(state.tan, 4))

        .field(
            "ammonia",
            round(state.tan, 4)
        )

        .field("nh3", round(nh3, 5))

        .field(
            "water_level",
            round(state.water_level, 2)
        )

        .field(
            "biomass_kg",
            round(state.biomass_kg, 3)
        )

        .field(
            "feed_kg_total",
            round(state.cumulative_feed_kg, 3)
        )

        .field(
            "aerator_1",
            state.aerator_1
        )

        .field(
            "aerator_2",
            state.aerator_2
        )

        .field(
            "aerator_3",
            state.aerator_3
        )

        .field(
            "feeder",
            state.feeder
        )

        .field(
            "inlet_valve",
            state.inlet_valve
        )
        .field(
    "fish_count",
    state.fish_count
)

        .field(
            "average_weight_g",
            round(
                state.average_weight_g,
                2
            )
        )

        .field(
            "culture_day",
            round(
                state.age_days,
                2
            )
        )
    )

    client.write(
        record=point
    )

# ============================================================
# DIAGNÓSTICO
# ============================================================
def print_status(state, now):

    season = get_season(now)

    solar = get_solar_factor(now)

    nh3 = calculate_un_ionized_ammonia(
        state.temperature,
        state.ph,
        state.tan
    )

    oxygen_status, ammonia_status, _ = (
        get_system_status(state)
    )

    print(
        "\n" + "=" * 70
    )

    print(
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        f"SEASON = {season}"
    )

    print(
        f"SOLAR = {solar:.3f}"
    )

    print(
        f"TEMP WATER = {state.temperature:.2f} °C"
    )

    print(
        f"DO = {state.do:.2f} mg/L "
        f"[{oxygen_status}]"
    )

    print(
        f"pH = {state.ph:.2f}"
    )

    print(
        f"TAN = {state.tan:.3f} mg/L"
    )

    print(
        f"NH3 = {nh3:.4f} mg/L "
        f"[{ammonia_status}]"
    )

    print(
        f"LEVEL = {state.water_level:.2f} %"
    )

    print(
        f"BIOMASS = {state.biomass_kg:.2f} kg"
    )

    print(
        f"AERATOR 1 = {state.aerator_1}"
    )

    print(
        f"AERATOR 2 = {state.aerator_2}"
    )

    print(
        f"AERATOR 3 = {state.aerator_3}"
    )

    print(
        f"FEEDER = {state.feeder}"
    )

    print(
        f"INLET VALVE = {state.inlet_valve:.0f}%"
    )
    print(
    f"FISH COUNT = {state.fish_count}"
    )

    print(
        f"AVG WEIGHT = "
        f"{state.average_weight_g:.2f} g"
    )

    print(
        f"CULTURE DAY = "
        f"{state.age_days:.1f}"
    )

    print(
        "=" * 70
    )

# ============================================================
# CURVA TEÓRICA
# ============================================================
def print_daily_temperature_curve():

    print(
        "\n"
        "--- CURVA TEÓRICA DIÁRIA ---\n"
    )

    now = datetime.now()

    for h in range(24):

        simulated_time = now.replace(
            hour=h,
            minute=0,
            second=0,
            microsecond=0
        )

        air = get_air_temperature(
            simulated_time
        )

        solar = get_solar_factor(
            simulated_time
        )

        season = get_season(
            simulated_time
        )

        print(
            f"{h:02d}:00 | "
            f"season={season:<7} | "
            f"air={air:5.2f} °C | "
            f"solar={solar:.2f}"
        )

# ============================================================
# EXECUÇÃO
# ============================================================

print_daily_temperature_curve()

print("\n""============================================")

print(" DIGITAL TWIN - FISH FARM")

print("============================================")

print(f"Tank: {CONFIG.tank_id}")

print(
f"Latitude: {CONFIG.latitude}"
)

print(f"Longitude: {CONFIG.longitude}")

print(
    f"Biomassa inicial: "
    f"{state.biomass_kg:.2f} kg"
)

print("============================================\n")

# ------------------------------------------------------------
# RELÓGIO DO DIGITAL TWIN
# ------------------------------------------------------------

if REAL_TIME_MODE:

    last_update = datetime.now()

else:

    simulation_time = datetime.now()


while True:

    if REAL_TIME_MODE:

        now = datetime.now()

        elapsed_seconds = (
            now - last_update
        ).total_seconds()

        last_update = now

    else:

        elapsed_seconds = (
            SIMULATION_SPEED
        )

        simulation_time += timedelta(
            seconds=SIMULATION_SPEED
        )

        now = simulation_time

    dt_hours = (
        elapsed_seconds / 3600.0
    )

    # --------------------------------------------------------
    # EVOLUIR DIGITAL TWIN
    # --------------------------------------------------------

    update_digital_twin(
        state,
        now,
        dt_hours
    )

    if state.age_days >= 365:

        print("\n")
        print("=" * 70)
        print("FIM DO CICLO PRODUTIVO")
        print("=" * 70)

        print(
            f"Dias de cultivo: {state.age_days:.1f}"
        )

        print(
            f"Peso médio final: "
            f"{state.average_weight_g:.2f} g"
        )

        print(
            f"Biomassa final: "
            f"{state.biomass_kg:.2f} kg"
        )

        print(
            f"Peixes estocados: "
            f"{state.fish_count}"
        )

        print("=" * 70)

        break
    
    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    write_to_influx(
        state,
        now
    )

    # --------------------------------------------------------
    # CONSOLE
    # --------------------------------------------------------

    print_status(
        state,
        now
    )

    # --------------------------------------------------------
    # INTERVALO DE SIMULAÇÃO
    # --------------------------------------------------------

    time.sleep(1)