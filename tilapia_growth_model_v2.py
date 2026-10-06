# ==============================================================
# DIGITAL TWIN DE CRESCIMENTO DE TILÁPIA - V2.1
# ==============================================================
#
# Entrada térmica:
#     temperatura_tanque_para_tilapia.csv
#
# Gerada por:
#     thermal_tank_model_v2.py
#
# Arquitetura:
#
#     MODELO TÉRMICO
#          |
#          v
#     T_media_C diária
#          |
#          v
#     MODELO DE CRESCIMENTO
#
# O modelo de crescimento NÃO altera a temperatura do tanque.
# ==============================================================

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


@dataclass
class ModelConfig:

    # Peixes
    initial_fish: int = 10_000
    initial_weight_g: float = 30.0
    target_weight_g: float = 1_000.0

    # Crescimento
    gompertz_wmax_g: float = 1_200.0
    max_sgr_fraction_per_day: float = 0.022

    # Temperatura
    temp_opt_min_C: float = 26.0
    temp_opt_max_C: float = 30.0
    temp_low_C: float = 18.0
    temp_high_C: float = 34.0

    # Alimentação (% peso vivo/dia)
    feed_rate_small: float = 0.035
    feed_rate_medium: float = 0.025
    feed_rate_large: float = 0.018
    feed_rate_harvest: float = 0.012

    # FCR
    fcr_small: float = 1.20
    fcr_medium: float = 1.35
    fcr_large: float = 1.55
    fcr_harvest: float = 1.70

    # Qualidade da água
    do_optimal_mg_L: float = 6.0
    do_critical_mg_L: float = 1.0

    ph_opt_low: float = 6.5
    ph_opt_high: float = 8.5
    ph_stress_low: float = 5.5
    ph_stress_high: float = 9.0

    ammonia_optimal_mg_L: float = 0.02
    ammonia_critical_mg_L: float = 0.50

    nitrite_optimal_mg_L: float = 0.10
    nitrite_critical_mg_L: float = 1.00

    # Tanque
    tank_volume_m3: float = 4800.0
    density_stress_kg_m3: float = 50.0

    # Variabilidade individual
    individual_cv: float = 0.10

    # Mortalidade
    base_daily_mortality: float = 0.00005

    max_days: int = 600
    random_seed: int = 42




def water_quality_factor(
    do,
    ph,
    ammonia,
    nitrite,
    cfg
):
    """Fator combinado de qualidade da água."""

    if do >= cfg.do_optimal_mg_L:
        f_do = 1.0
    elif do <= cfg.do_critical_mg_L:
        f_do = 0.0
    else:
        f_do = (
            (do - cfg.do_critical_mg_L)
            / (cfg.do_optimal_mg_L - cfg.do_critical_mg_L)
        )

    if cfg.ph_opt_low <= ph <= cfg.ph_opt_high:
        f_ph = 1.0
    elif ph <= cfg.ph_stress_low or ph >= cfg.ph_stress_high:
        f_ph = 0.0
    elif ph < cfg.ph_opt_low:
        f_ph = (
            (ph - cfg.ph_stress_low)
            / (cfg.ph_opt_low - cfg.ph_stress_low)
        )
    else:
        f_ph = (
            (cfg.ph_stress_high - ph)
            / (cfg.ph_stress_high - cfg.ph_opt_high)
        )

    if ammonia <= cfg.ammonia_optimal_mg_L:
        f_nh3 = 1.0
    elif ammonia >= cfg.ammonia_critical_mg_L:
        f_nh3 = 0.0
    else:
        f_nh3 = (
            (cfg.ammonia_critical_mg_L - ammonia)
            / (cfg.ammonia_critical_mg_L - cfg.ammonia_optimal_mg_L)
        )

    if nitrite <= cfg.nitrite_optimal_mg_L:
        f_no2 = 1.0
    elif nitrite >= cfg.nitrite_critical_mg_L:
        f_no2 = 0.0
    else:
        f_no2 = (
            (cfg.nitrite_critical_mg_L - nitrite)
            / (cfg.nitrite_critical_mg_L - cfg.nitrite_optimal_mg_L)
        )

    return (
        np.clip(f_do, 0, 1)
        * np.clip(f_ph, 0, 1)
        * np.clip(f_nh3, 0, 1)
        * np.clip(f_no2, 0, 1)
    )


def feed_rate(weight_g, cfg):
    if weight_g < 100:
        return cfg.feed_rate_small
    if weight_g < 300:
        return cfg.feed_rate_medium
    if weight_g < 700:
        return cfg.feed_rate_large
    return cfg.feed_rate_harvest


def fcr_value(weight_g, cfg):
    if weight_g < 100:
        return cfg.fcr_small
    if weight_g < 300:
        return cfg.fcr_medium
    if weight_g < 700:
        return cfg.fcr_large
    return cfg.fcr_harvest

def temperature_feed_factor(T):
    """
    Consumo relativo de ração em função da temperatura.

    Curva gaussiana baseada na temperatura ótima
    de alimentação da tilápia (~29°C).
    """

    Topt = 29.0
    sigma = 4.5

    return float(
        np.exp(
            -((T - Topt) / sigma) ** 2
        )
    )


def temperature_corrected_fcr(
    base_fcr,
    T
):
    """
    FCR piora fora da temperatura ótima.
    """

    Topt = 29.0

    return (
        base_fcr
        + 0.01 * (Topt - T) ** 2
    )


def estimated_daily_feed(
    weights_g,
    temperature,
    cfg
):
    """
    Quantidade de ração ingerida por dia.
    """

    feed_rates = np.array([
        feed_rate(w, cfg)
        for w in weights_g
    ])

    thermal_factor = (
        temperature_feed_factor(
            temperature
        )
    )

    return (
        weights_g
        * feed_rates
        * thermal_factor
    )

def density_factor(biomass_kg, cfg):
    density = biomass_kg / cfg.tank_volume_m3

    if density <= cfg.density_stress_kg_m3:
        return 1.0

    return float(
        np.clip(
            cfg.density_stress_kg_m3 / density,
            0.0,
            1.0
        )
    )


def load_temperature_from_thermal_model(
    filename="temperatura_tanque_para_tilapia.csv"
):
    """
    Lê a saída diária do modelo térmico.
    """

    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {filename}\n"
            "Execute primeiro thermal_tank_model_v2.py e "
            "a função save_daily_temperature_for_fish_model()."
        )

    df = pd.read_csv(
        path,
        sep=";",
        decimal=","
    )

    if not {"data", "T_media_C"}.issubset(df.columns):
        raise ValueError(
            "O arquivo precisa conter: data e T_media_C"
        )

    df["data"] = pd.to_datetime(df["data"])
    df["T_media_C"] = pd.to_numeric(
        df["T_media_C"],
        errors="coerce"
    )

    return (
        df.dropna(subset=["data", "T_media_C"])
        .sort_values("data")
        .drop_duplicates("data")
        .reset_index(drop=True)
    )


class TilapiaDigitalTwinV21:

    def __init__(
        self,
        temperature_data,
        config=None,
        do_mg_L=6.0,
        ph=7.5,
        ammonia_mg_L=0.02,
        nitrite_mg_L=0.10
    ):

        self.cfg = config or ModelConfig()
        self.temperature_data = temperature_data.copy()

        self.do_mg_L = do_mg_L
        self.ph = ph
        self.ammonia_mg_L = ammonia_mg_L
        self.nitrite_mg_L = nitrite_mg_L

        self.rng = np.random.default_rng(
            self.cfg.random_seed
        )

        self.weights_g = np.full(
            self.cfg.initial_fish,
            self.cfg.initial_weight_g,
            dtype=float
        )

        sigma = np.sqrt(
            np.log(1.0 + self.cfg.individual_cv ** 2)
        )
        mu = -0.5 * sigma ** 2

        self.individual_multiplier = (
            self.rng.lognormal(
                mean=mu,
                sigma=sigma,
                size=self.cfg.initial_fish
            )
        )

        self.alive = np.ones(
            self.cfg.initial_fish,
            dtype=bool
        )

        self.history = []


    def mortality_probability(
        self,
        temperature,
        water_factor,
        density_factor_value
    ):

        thermal_factor = (
            temperature_feed_factor(
                temperature
            )
        )

        stress = 1.0 - (
            thermal_factor
            * water_factor
            * density_factor_value
        )

        probability = (
            self.cfg.base_daily_mortality
            * (1.0 + 10.0 * stress)
        )

        return float(
            np.clip(
                probability,
                0.0,
                1.0
            )
        )


    def simulate(self):

        max_days = min(
            self.cfg.max_days,
            len(self.temperature_data)
        )

        for day_index in range(max_days):

            row = self.temperature_data.iloc[
                day_index
            ]

            date = row["data"]
            temperature = float(
                row["T_media_C"]
            )

            alive_indices = np.where(
                self.alive
            )[0]

            if len(alive_indices) == 0:
                break

            alive_weights = (
                self.weights_g[alive_indices]
            )

            biomass_before_kg = (
                alive_weights.sum() / 1000.0
            )

            density_factor_value = density_factor(
                biomass_before_kg,
                self.cfg
            )

            quality_factor = water_quality_factor(
                self.do_mg_L,
                self.ph,
                self.ammonia_mg_L,
                self.nitrite_mg_L,
                self.cfg
            )

            daily_feed_g = estimated_daily_feed(
                alive_weights,
                temperature,
                self.cfg
            )

            base_fcr_values = np.array([
                fcr_value(w, self.cfg)
                for w in alive_weights
            ])

            real_fcr_values = (
                temperature_corrected_fcr(
                    base_fcr_values,
                    temperature
                )
            )

            gains = (
                daily_feed_g
                / real_fcr_values
            )

            gains *= (
                quality_factor
                * density_factor_value
            )

            gains *= (
                self.individual_multiplier[
                    self.alive
                ]
            )

            gains = np.maximum(
                gains,
                0.0
            )



            self.weights_g[
                alive_indices
            ] += gains

            self.weights_g[
                self.weights_g > self.cfg.target_weight_g
            ] = self.cfg.target_weight_g

            current_weights = (
                self.weights_g[alive_indices]
            )

            feed_kg_day = (
                daily_feed_g.sum()
                / 1000.0
            )

            ammonia_kg_day = (
                feed_kg_day * 0.03
            )

            oxygen_demand_kg_day = (
                feed_kg_day * 0.50
            )

            weighted_fcr = np.average(
                real_fcr_values,
                weights=current_weights
                )

            

            mortality_p = self.mortality_probability(
                temperature,
                quality_factor,
                density_factor_value
            )

            death_mask = (
                self.rng.random(
                    len(alive_indices)
                ) < mortality_p
            )

            deaths_indices = alive_indices[
                death_mask
            ]

            self.alive[
                deaths_indices
            ] = False

            deaths = len(deaths_indices)
            fish_alive = int(self.alive.sum())

            if fish_alive > 0:

                final_weights = (
                    self.weights_g[self.alive]
                )

                biomass_kg = (
                    final_weights.sum() / 1000.0
                )

                mean_weight_g = (
                    final_weights.mean()
                )

                min_weight_g = (
                    final_weights.min()
                )

                max_weight_g = (
                    final_weights.max()
                )

                fish_at_target = int(
                    np.sum(
                        final_weights
                        >= self.cfg.target_weight_g
                    )
                )

            else:

                biomass_kg = 0.0
                mean_weight_g = 0.0
                min_weight_g = 0.0
                max_weight_g = 0.0
                fish_at_target = 0
                ammonia_kg_day = (
                    feed_kg_day * 0.03
                )

                oxygen_demand_kg_day = (
                    feed_kg_day * 0.50
                )
                

            self.history.append({
                "date": date,
                "temperature_C": temperature,
                "fish_alive": fish_alive,
                "deaths": deaths,
                "mean_weight_g": mean_weight_g,
                "min_weight_g": min_weight_g,
                "max_weight_g": max_weight_g,
                "fish_at_target": fish_at_target,
                "biomass_kg": biomass_kg,
                "density_kg_m3": (
                    biomass_kg
                    / self.cfg.tank_volume_m3
                ),
                "feed_kg_day": feed_kg_day,
                "FCR": weighted_fcr,
                "temperature_factor": temperature_feed_factor(
                    temperature,
                ),
                "water_quality_factor": quality_factor,
                "density_factor": density_factor_value,
                "mortality_probability": mortality_p,
                "ammonia_kg_day": ammonia_kg_day,
                "oxygen_demand_kg_day": oxygen_demand_kg_day,
            })

            if mean_weight_g >= (
                self.cfg.target_weight_g * 0.95
            ):

                print(
                    f"\nPeso médio de abate atingido: "
                    f"{mean_weight_g:.1f} g"
                )

                break

        return pd.DataFrame(self.history)


def print_summary(results):

    if results.empty:
        print("Nenhum resultado disponível.")
        return

    last = results.iloc[-1]

    print("\n==========================================")
    print(" TILAPIA DIGITAL TWIN V2.1")
    print("==========================================")
    print(f"Data final       : {last['date']}")
    print(f"Temperatura      : {last['temperature_C']:.2f} °C")
    print(f"Peixes vivos     : {last['fish_alive']:.0f}")
    print(f"Peso médio       : {last['mean_weight_g']:.1f} g")
    print(f"Biomassa         : {last['biomass_kg']:.2f} kg")
    print(f"Densidade        : {last['density_kg_m3']:.2f} kg/m³")
    print(f"Peixes em 1 kg   : {last['fish_at_target']:.0f}")
    print(f"Ração diária     : {last['feed_kg_day']:.2f} kg")
    print(f"FCR              : {last['FCR']:.2f}")
    print("==========================================")


def plot_results(results):

    if results.empty:
        return

    plt.figure(figsize=(14, 5))
    plt.plot(
        results["date"],
        results["temperature_C"]
    )
    plt.xlabel("Data")
    plt.ylabel("Temperatura (°C)")
    plt.title("Temperatura do tanque")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        "tilapia_01_temperatura.png",
        dpi=300
    )
    plt.show()

    plt.figure(figsize=(14, 5))
    plt.plot(
        results["date"],
        results["mean_weight_g"]
    )
    plt.axhline(
        1000,
        linestyle="--",
        label="1 kg"
    )
    plt.xlabel("Data")
    plt.ylabel("Peso médio (g)")
    plt.title("Crescimento médio das tilápias")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        "tilapia_02_crescimento.png",
        dpi=300
    )
    plt.show()

    plt.figure(figsize=(14, 5))
    plt.plot(
        results["date"],
        results["biomass_kg"]
    )
    plt.xlabel("Data")
    plt.ylabel("Biomassa (kg)")
    plt.title("Biomassa do tanque")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        "tilapia_03_biomassa.png",
        dpi=300
    )
    plt.show()

    plt.figure(figsize=(14, 5))
    plt.plot(
        results["date"],
        results["feed_kg_day"]
    )
    plt.xlabel("Data")
    plt.ylabel("Ração (kg/dia)")
    plt.title("Consumo diário de ração")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        "tilapia_04_racao.png",
        dpi=300
    )
    plt.show()


def main():

    temperature_data = (
        load_temperature_from_thermal_model()
    )

    cfg = ModelConfig()

    model = TilapiaDigitalTwinV21(
        temperature_data=temperature_data,
        config=cfg,
        do_mg_L=6.0,
        ph=7.5,
        ammonia_mg_L=0.02,
        nitrite_mg_L=0.10
    )

    results = model.simulate()

    print_summary(results)

    results.to_csv(
        "tilapia_growth_results_v2_1.csv",
        index=False,
        decimal=",",
        sep=";"
    )

    plot_results(results)


if __name__ == "__main__":
    main()
