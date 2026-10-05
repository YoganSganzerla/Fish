# ==============================================================
# DIGITAL TWIN TÉRMICO DE UM TANQUE - PALOTINA/PR
# ==============================================================
#
# Modelo:
# - Tanque: 150 x 16 x 2 m
# - Volume: 4.800 m³
# - Renovação: 10%/dia
# - Passo de integração: 1 hora
# - Simulação: 5 anos para estabilização térmica
# - Resultados e gráficos: último ano estabilizado
# - 6 camadas verticais
# - Chuva DESCONSIDERADA
# - Temperatura do córrego = senoide anual
#
# Bibliotecas:
# numpy
# pandas
# matplotlib
#
# Instalação:
# pip install numpy pandas matplotlib
#
# ==============================================================
#
# IMPORTANTE:
# Os parâmetros meteorológicos utilizados neste primeiro modelo
# são aproximações sintéticas. O modelo foi estruturado para que
# posteriormente possam ser substituídos por dados horários reais.
#
# ==============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# ==============================================================
# 1. PARÂMETROS GEOMÉTRICOS DO TANQUE
# ==============================================================

COMPRIMENTO = 150.0  # m
LARGURA = 16.0       # m
PROFUNDIDADE = 2.0   # m

AREA_SUPERFICIAL = COMPRIMENTO * LARGURA
VOLUME = COMPRIMENTO * LARGURA * PROFUNDIDADE

print("\n================ TANQUE ================")
print(f"Área superficial : {AREA_SUPERFICIAL:.0f} m²")
print(f"Volume           : {VOLUME:.0f} m³")


# ==============================================================
# 2. PROPRIEDADES DA ÁGUA
# ==============================================================

RHO_AGUA = 998.0      # kg/m³
CP_AGUA = 4186.0      # J/(kg K)
K_AGUA = 0.60         # W/(m K)

# Calor latente de vaporização
L_V = 2.45e6          # J/kg

# Emissividade aproximada da água
EMISSIVIDADE = 0.96

# Constante de Stefan-Boltzmann
SIGMA = 5.670374419e-8  # W/(m² K⁴)


# ==============================================================
# 3. RENOVAÇÃO DE ÁGUA
# ==============================================================

FRAC_RENOVACAO_DIA = 0.10

V_RENOVACAO_DIA = VOLUME * FRAC_RENOVACAO_DIA

V_RENOVACAO_HORA = V_RENOVACAO_DIA / 24.0

VAZAO_M3_H = V_RENOVACAO_HORA

VAZAO_M3_S = VAZAO_M3_H / 3600.0

MASSA_ENTRADA_H = V_RENOVACAO_HORA * RHO_AGUA

print("\n============= RENOVAÇÃO ===============")
print(f"Renovação diária : {V_RENOVACAO_DIA:.1f} m³/dia")
print(f"Renovação horária: {V_RENOVACAO_HORA:.2f} m³/h")
print(f"Vazão            : {VAZAO_M3_S:.6f} m³/s")
print(f"Tempo renovação  : {VOLUME / V_RENOVACAO_DIA:.1f} dias")


# ==============================================================
# 4. DISCRETIZAÇÃO VERTICAL
# ==============================================================

N_CAMADAS = 6

DZ = PROFUNDIDADE / N_CAMADAS

V_CAMADA = AREA_SUPERFICIAL * DZ

M_CAMADA = RHO_AGUA * V_CAMADA

PROFUNDIDADES = (
    np.arange(N_CAMADAS) * DZ
    + DZ / 2.0
)

print("\n============= CAMADAS =================")
for i, z in enumerate(PROFUNDIDADES):
    print(f"Camada {i+1}: profundidade média = {z:.3f} m")


# ==============================================================
# 5. SIMULAÇÃO TEMPORAL
# ==============================================================

DT = 3600.0  # 1 hora em segundos

# Simulamos vários anos para eliminar o efeito da
# condição inicial artificial e atingir regime periódico.
ANOS_SIMULACAO = 5
DIAS_ANO = 365
HORAS_DIA = 24

DIAS = ANOS_SIMULACAO * DIAS_ANO
N_PASSOS = DIAS * HORAS_DIA

tempo_h = np.arange(N_PASSOS) * DT / 3600.0
dia_global = tempo_h / 24.0

# Dia dentro do ciclo anual.
# Mantém a meteorologia exatamente periódica a cada 365 dias.
dia_ano = np.mod(dia_global, DIAS_ANO)

data_inicio = pd.Timestamp("2025-01-01")

datas = (
    data_inicio
    + pd.to_timedelta(tempo_h, unit="h")
)


# ==============================================================
# 6. TEMPERATURA DO CÓRREGO
# ==============================================================

# Temperatura média anual
T_CORREGO_MEDIA = 21.85

# Amplitude anual
T_CORREGO_AMPLITUDE = 4.05

# Fase da senoide
FASE_CORREGO = 289.0


def temperatura_corrego(dia):
    """
    Temperatura do córrego em função do dia do ano.

    Retorna:
        temperatura em °C
    """
    return (
        T_CORREGO_MEDIA
        + T_CORREGO_AMPLITUDE
        * np.sin(
            2.0 * np.pi
            * (dia - FASE_CORREGO)
            / 365.0
        )
    )


T_CORREGO = temperatura_corrego(dia_ano)


# ==============================================================
# 7. MODELO METEOROLÓGICO SINTÉTICO
# ==============================================================

def temperatura_ar(dia, hora):
    """
    Temperatura do ar:
    - componente anual
    - componente diária
    """
    media_anual = 21.85
    amplitude_anual = 4.5

    # Fase ajustada para Palotina/PR (hemisfério sul).
    # Máximo aproximadamente em meados de janeiro.
    FASE_AR = 289.0

    componente_anual = (
        amplitude_anual
        * np.sin(
            2 * np.pi
            * (dia - FASE_AR)
            / 365
        )
    )

    # ciclo diário
    amplitude_diaria = 4.5

    componente_diaria = (
        amplitude_diaria
        * np.sin(
            2 * np.pi
            * (hora - 9)
            / 24
        )
    )

    return (
        media_anual
        + componente_anual
        + componente_diaria
    )


def umidade_relativa(dia, hora):
    """
    Modelo simplificado de umidade relativa.
    """
    UR_media = 70.0

    variacao = (
        10.0
        * np.sin(
            2 * np.pi
            * (hora - 15)
            / 24
        )
    )

    return np.clip(
        UR_media + variacao,
        35,
        95
    )


def velocidade_vento(dia, hora):
    """
    Velocidade média do vento em m/s.
    """
    vento = (
        2.0
        + 0.8
        * np.sin(
            2 * np.pi
            * (hora - 13)
            / 24
        )
    )

    return max(0.2, vento)


def radiacao_solar(dia, hora):
    """
    Modelo simplificado da radiação solar.

    Zero durante a noite e máximo ao redor do meio-dia.
    """
    # duração aproximada do dia
    hora_nascer = 6.0
    hora_por = 18.0

    if hora < hora_nascer or hora > hora_por:
        return 0.0

    # Fator sazonal ajustado para Palotina/PR.
    # Máximo aproximadamente em janeiro.
    FASE_SOLAR = 289.0

    fator_sazonal = (
        0.75
        + 0.25
        * np.sin(
            2 * np.pi
            * (dia - FASE_SOLAR)
            / 365
        )
    )

    angulo = (
        np.pi
        * (hora - hora_nascer)
        / (hora_por - hora_nascer)
    )

    irradiancia_max = 850.0

    return max(
        0.0,
        irradiancia_max
        * np.sin(angulo)
        * fator_sazonal
    )


# ==============================================================
# 8. FUNÇÕES DE TRANSFERÊNCIA DE CALOR
# ==============================================================

def coeficiente_conveccao(vento):
    """
    Aproximação para o coeficiente de convecção.
    """
    return 5.0 + 4.0 * vento


def pressao_vapor_saturacao(T):
    """
    Pressão de vapor de saturação em Pa.
    Fórmula de Tetens.
    """
    return (
        610.78
        * np.exp(
            (17.27 * T)
            / (T + 237.3)
        )
    )


def fluxo_evaporativo(T_agua, T_ar, UR, vento):
    """
    Fluxo aproximado de evaporação.

    Retorna kg/(m² s).
    """
    es_agua = pressao_vapor_saturacao(T_agua)
    es_ar = pressao_vapor_saturacao(T_ar)
    ea_ar = es_ar * UR / 100.0

    deficit = max(
        0.0,
        es_agua - ea_ar
    )

    # coeficiente empírico
    coef = (
        1.0e-8
        * (1.0 + 0.3 * vento)
    )

    return coef * deficit


def temperatura_celeste(T_ar, UR):
    """
    Temperatura efetiva do céu.
    """
    T_kelvin = T_ar + 273.15

    # aproximação baseada na umidade
    emissividade_ceu = 0.72 + 0.005 * UR

    emissividade_ceu = np.clip(
        emissividade_ceu,
        0.72,
        0.98
    )

    T_celeste = T_kelvin * emissividade_ceu ** 0.25

    return T_celeste - 273.15


# ==============================================================
# 9. ABSORÇÃO SOLAR PELA ÁGUA
# ==============================================================

ABSORCAO_SOLAR = 0.93

# Coeficiente de extinção da luz na água
COEF_EXTINCAO = 0.7  # 1/m


# ==============================================================
# 10. MISTURA VERTICAL
# ==============================================================

# Coeficiente efetivo de difusão térmica vertical.
#
# Este valor será aumentado pelo vento.
#
# Unidade aproximada: m²/s

K_VERTICAL_BASE = 1.0e-6


def coeficiente_mistura(vento):
    """
    Coeficiente vertical efetivo.

    Quanto maior o vento, maior a mistura.
    """
    return (
        K_VERTICAL_BASE
        * (1.0 + 3.0 * vento)
    )


# ==============================================================
# 11. CONDIÇÃO INICIAL
# ==============================================================

T_INICIAL = 21.85

temperatura = np.ones(N_CAMADAS) * T_INICIAL


# ==============================================================
# 12. ARRAYS PARA ARMAZENAMENTO
# ==============================================================

T_HIST = np.zeros((N_PASSOS, N_CAMADAS))

T_MEDIA_HIST = np.zeros(N_PASSOS)
T_SUPERFICIE_HIST = np.zeros(N_PASSOS)
T_FUNDO_HIST = np.zeros(N_PASSOS)

T_AR_HIST = np.zeros(N_PASSOS)
UR_HIST = np.zeros(N_PASSOS)
VENTO_HIST = np.zeros(N_PASSOS)
RAD_HIST = np.zeros(N_PASSOS)

Q_SOLAR_HIST = np.zeros(N_PASSOS)
Q_EVAP_HIST = np.zeros(N_PASSOS)
Q_CONV_HIST = np.zeros(N_PASSOS)
Q_RAD_HIST = np.zeros(N_PASSOS)
Q_CORREGO_HIST = np.zeros(N_PASSOS)
Q_MISTURA_HIST = np.zeros(N_PASSOS)


# ==============================================================
# 13. LOOP PRINCIPAL DA SIMULAÇÃO
# ==============================================================

print("\n=========== INICIANDO SIMULAÇÃO ==========")

for n in range(N_PASSOS):
    dia = dia_ano[n]
    hora = datas[n].hour

    # ----------------------------------------------------------
    # Meteorologia
    # ----------------------------------------------------------
    T_ar = temperatura_ar(dia, hora)
    UR = umidade_relativa(dia, hora)
    vento = velocidade_vento(dia, hora)
    rad = radiacao_solar(dia, hora)
    T_c = T_CORREGO[n]

    # ----------------------------------------------------------
    # Temperatura atual
    # ----------------------------------------------------------
    T_superficie = temperatura[0]
    T_media = np.mean(temperatura)
    T_fundo = temperatura[-1]

    # ----------------------------------------------------------
    # BALANÇO DE ENERGIA
    # ----------------------------------------------------------
    Q_total = np.zeros(N_CAMADAS)

    # ==========================================================
    # RADIAÇÃO SOLAR
    # ==========================================================
    Qsolar_total = 0.0

    for i in range(N_CAMADAS):
        profundidade = PROFUNDIDADES[i]

        # fração de radiação que chega à camada
        transmissao = np.exp(
            -COEF_EXTINCAO * profundidade
        )

        # absorção diferencial aproximada
        if i == 0:
            fracao = (
                1
                - np.exp(-COEF_EXTINCAO * DZ)
            )
        else:
            fracao = (
                np.exp(-COEF_EXTINCAO * (i * DZ))
                - np.exp(-COEF_EXTINCAO * ((i + 1) * DZ))
            )

        Qsolar = (
            rad
            * AREA_SUPERFICIAL
            * ABSORCAO_SOLAR
            * fracao
        )

        Q_total[i] += Qsolar
        Qsolar_total += Qsolar

    # ==========================================================
    # CONVECÇÃO - SUPERFÍCIE
    # ==========================================================
    h = coeficiente_conveccao(vento)

    Qconv = (
        h
        * AREA_SUPERFICIAL
        * (T_superficie - T_ar)
    )

    # Qconv > 0 significa perda do tanque
    Q_total[0] -= Qconv

    # ==========================================================
    # EVAPORAÇÃO
    # ==========================================================
    fluxo_evap = fluxo_evaporativo(
        T_superficie,
        T_ar,
        UR,
        vento
    )

    massa_evaporada = fluxo_evap * AREA_SUPERFICIAL

    Qevap = massa_evaporada * L_V

    Q_total[0] -= Qevap

    # ==========================================================
    # RADIAÇÃO DE ONDA LONGA
    # ==========================================================
    T_ceu = temperatura_celeste(T_ar, UR)

    T_superficie_K = T_superficie + 273.15
    T_ceu_K = T_ceu + 273.15

    Qrad = (
        EMISSIVIDADE
        * SIGMA
        * AREA_SUPERFICIAL
        * (
            T_superficie_K ** 4
            - T_ceu_K ** 4
        )
    )

    Q_total[0] -= Qrad

    # ==========================================================
    # TROCA COM O CÓRREGO
    # ==========================================================
    # A água de entrada é considerada incorporada
    # à camada superficial.
    #
    # O termo representa a substituição de água.
    Qcorrego = (
        MASSA_ENTRADA_H
        * CP_AGUA
        * (T_c - T_media)
        / 3600.0
    )

    # Distribuição na camada superficial
    Q_total[0] += Qcorrego

    # ==========================================================
    # MISTURA VERTICAL
    # ==========================================================
    K_vertical = coeficiente_mistura(vento)

    Qmistura_total = 0.0

    for i in range(N_CAMADAS - 1):
        dT = temperatura[i] - temperatura[i + 1]

        # fluxo térmico aproximado
        Qmix = (
            RHO_AGUA
            * CP_AGUA
            * K_vertical
            * AREA_SUPERFICIAL
            * dT
            / DZ
        )

        # limite para estabilidade numérica
        Qmix = np.clip(Qmix, -1.0e9, 1.0e9)

        Q_total[i] -= Qmix
        Q_total[i + 1] += Qmix

        Qmistura_total += abs(Qmix)

    # ==========================================================
    # ATUALIZAÇÃO DA TEMPERATURA
    # ==========================================================
    dT = (
        Q_total
        * DT
        / (M_CAMADA * CP_AGUA)
    )

    temperatura = temperatura + dT

    # ==========================================================
    # SALVAMENTO
    # ==========================================================
    T_HIST[n, :] = temperatura

    T_MEDIA_HIST[n] = np.mean(temperatura)
    T_SUPERFICIE_HIST[n] = temperatura[0]
    T_FUNDO_HIST[n] = temperatura[-1]

    T_AR_HIST[n] = T_ar
    UR_HIST[n] = UR
    VENTO_HIST[n] = vento
    RAD_HIST[n] = rad

    Q_SOLAR_HIST[n] = Qsolar_total
    Q_EVAP_HIST[n] = Qevap
    Q_CONV_HIST[n] = Qconv
    Q_RAD_HIST[n] = Qrad
    Q_CORREGO_HIST[n] = Qcorrego
    Q_MISTURA_HIST[n] = Qmistura_total


print("Simulação concluída.")

# ==============================================================
# 13.1. SELEÇÃO DO ÚLTIMO ANO
# ==============================================================

PASSOS_POR_ANO = DIAS_ANO * HORAS_DIA

INICIO_ULTIMO_ANO = (ANOS_SIMULACAO - 1) * PASSOS_POR_ANO
FIM_ULTIMO_ANO = ANOS_SIMULACAO * PASSOS_POR_ANO

# Somente o último ano será usado nos gráficos e resultados.
datas_analise = datas[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]

dia_ano_analise = np.arange(PASSOS_POR_ANO) / HORAS_DIA

T_CORREGO_analise = T_CORREGO[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
T_HIST_analise = T_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO, :]
T_MEDIA_analise = T_MEDIA_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
T_SUPERFICIE_analise = T_SUPERFICIE_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
T_FUNDO_analise = T_FUNDO_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]

T_AR_analise = T_AR_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
UR_analise = UR_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
VENTO_analise = VENTO_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
RAD_analise = RAD_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]

Q_SOLAR_analise = Q_SOLAR_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
Q_EVAP_analise = Q_EVAP_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
Q_CONV_analise = Q_CONV_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
Q_RAD_analise = Q_RAD_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
Q_CORREGO_analise = Q_CORREGO_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]
Q_MISTURA_analise = Q_MISTURA_HIST[INICIO_ULTIMO_ANO:FIM_ULTIMO_ANO]

# Verificação de estabilização:
# comparamos o início do último ciclo com o mesmo instante
# do ciclo anual anterior.
ERRO_ENTRE_CICLOS = abs(
    T_MEDIA_HIST[INICIO_ULTIMO_ANO]
    - T_MEDIA_HIST[INICIO_ULTIMO_ANO - PASSOS_POR_ANO]
)

ERRO_PRIMEIRO_ULTIMO_PONTO = abs(
    T_MEDIA_analise[0]
    - T_MEDIA_analise[-1]
)

print("\n=========== FECHAMENTO DO CICLO ===========")
print(f"Temperatura início do último ano : {T_MEDIA_analise[0]:.3f} °C")
print(f"Temperatura final do último ano  : {T_MEDIA_analise[-1]:.3f} °C")
print(f"Diferença primeiro/último ponto  : {ERRO_PRIMEIRO_ULTIMO_PONTO:.4f} °C")
print(f"Diferença entre ciclos anuais    : {ERRO_ENTRE_CICLOS:.4f} °C")

if ERRO_ENTRE_CICLOS < 0.01:
    print("STATUS: ciclo térmico altamente estabilizado.")
elif ERRO_ENTRE_CICLOS < 0.05:
    print("STATUS: ciclo térmico bem estabilizado.")
elif ERRO_ENTRE_CICLOS < 0.10:
    print("STATUS: ciclo térmico próximo da estabilização.")
else:
    print("STATUS: ainda existe diferença significativa entre os ciclos.")


# ==============================================================
# 14. DATAFRAME DE RESULTADOS
# ==============================================================

resultados = pd.DataFrame({
    "data": datas_analise,
    "dia_ano": dia_ano_analise,
    "T_corrego_C": T_CORREGO_analise,
    "T_ar_C": T_AR_analise,
    "UR_percent": UR_analise,
    "vento_m_s": VENTO_analise,
    "radiacao_W_m2": RAD_analise,
    "T_superficie_C": T_SUPERFICIE_analise,
    "T_media_C": T_MEDIA_analise,
    "T_fundo_C": T_FUNDO_analise
})

for i in range(N_CAMADAS):
    resultados[f"T_camada_{i+1}_C"] = T_HIST_analise[:, i]


# ==============================================================
# 15. ESTATÍSTICAS
# ==============================================================

print("\n==========================================")
print(" RESULTADOS DA SIMULAÇÃO")
print("==========================================")

print(f"Temperatura média do tanque: {T_MEDIA_analise.mean():.2f} °C")
print(f"Temperatura mínima do tanque: {T_MEDIA_analise.min():.2f} °C")
print(f"Temperatura máxima do tanque: {T_MEDIA_analise.max():.2f} °C")
print(f"Temperatura mínima do córrego: {T_CORREGO_analise.min():.2f} °C")
print(f"Temperatura máxima do córrego: {T_CORREGO_analise.max():.2f} °C")


# ==============================================================
# 16. GRÁFICO 1 - TEMPERATURA DO CÓRREGO
# ==============================================================

plt.figure(figsize=(14, 5))

plt.plot(
    datas_analise,
    T_CORREGO_analise,
    color="blue",
    linewidth=2
)

plt.title("Temperatura modelada da água do córrego")
plt.ylabel("Temperatura (°C)")
plt.xlabel("Data")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("01_temperatura_corrego.png", dpi=300)
plt.show()


# ==============================================================
# 17. GRÁFICO 2 - TEMPERATURA DO TANQUE
# ==============================================================

plt.figure(figsize=(14, 6))

plt.plot(datas_analise, T_CORREGO_analise, label="Córrego", color="blue", linewidth=1.5)
plt.plot(datas_analise, T_SUPERFICIE_analise, label="Superfície", color="red", linewidth=1.5)
plt.plot(datas_analise, T_MEDIA_analise, label="Média do tanque", color="black", linewidth=2)
plt.plot(datas_analise, T_FUNDO_analise, label="Fundo", color="green", linewidth=1.5)

plt.title("Evolução anual da temperatura do tanque")
plt.xlabel("Data")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("02_temperatura_tanque.png", dpi=300)
plt.show()


# ==============================================================
# 18. GRÁFICO 3 - TEMPERATURA DO AR x TANQUE
# ==============================================================

plt.figure(figsize=(14, 6))

plt.plot(datas_analise, T_AR_analise, label="Temperatura do ar", color="orange", alpha=0.7)
plt.plot(datas_analise, T_MEDIA_analise, label="Temperatura média do tanque", color="blue", linewidth=2)
plt.plot(datas_analise, T_CORREGO_analise, label="Temperatura do córrego", color="green", linewidth=1.5)

plt.title("Temperatura do ar, córrego e tanque")
plt.xlabel("Data")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("03_ar_corrego_tanque.png", dpi=300)
plt.show()


# ==============================================================
# 19. GRÁFICO 4 - MAPA DE CALOR
# ==============================================================

plt.figure(figsize=(15, 7))

im = plt.imshow(
    T_HIST_analise.T,
    aspect="auto",
    origin="upper",
    cmap="turbo",
    extent=[0, DIAS_ANO, PROFUNDIDADE, 0]
)

plt.colorbar(im, label="Temperatura (°C)")
plt.xlabel("Dia do ano")
plt.ylabel("Profundidade (m)")
plt.title("Mapa de calor da temperatura no tanque")
plt.tight_layout()

plt.savefig("04_mapa_calor_temperatura.png", dpi=300)
plt.show()


# ==============================================================
# 20. GRÁFICO 5 - PERFIL VERTICAL DE TEMPERATURA
# ==============================================================

# Seleciona quatro momentos do ano
dias_representativos = [30, 120, 210, 300]
nomes = ["Verão", "Outono", "Inverno", "Primavera"]

plt.figure(figsize=(9, 7))

for dia, nome in zip(dias_representativos, nomes):
    indice = min(int(dia * 24), PASSOS_POR_ANO - 1)

    plt.plot(
        T_HIST_analise[indice, :],
        PROFUNDIDADES,
        marker="o",
        linewidth=2,
        label=nome
    )

plt.gca().invert_yaxis()
plt.xlabel("Temperatura (°C)")
plt.ylabel("Profundidade (m)")
plt.title("Perfil vertical de temperatura")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("05_perfil_vertical.png", dpi=300)
plt.show()


# ==============================================================
# 21. GRÁFICO 6 - BALANÇO DE ENERGIA
# ==============================================================

# Conversão para kW
plt.figure(figsize=(15, 7))

plt.plot(datas_analise, Q_SOLAR_analise / 1000, label="Solar", linewidth=1)
plt.plot(datas_analise, -Q_EVAP_analise / 1000, label="Evaporação", linewidth=1)
plt.plot(datas_analise, -Q_CONV_analise / 1000, label="Convecção", linewidth=1)
plt.plot(datas_analise, -Q_RAD_analise / 1000, label="Radiação", linewidth=1)
plt.plot(datas_analise, Q_CORREGO_analise / 1000, label="Córrego", linewidth=1)

plt.axhline(0, color="black", linewidth=0.8)
plt.xlabel("Data")
plt.ylabel("Potência térmica (kW)")
plt.title("Componentes do balanço térmico")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("06_balanco_termico.png", dpi=300)
plt.show()


# ==============================================================
# 22. GRÁFICO 7 - TEMPERATURA DIÁRIA
# ==============================================================

resultados_diarios = (
    resultados
    .set_index("data")
    .resample("D")
    .agg({
        "T_corrego_C": "mean",
        "T_ar_C": "mean",
        "T_superficie_C": "mean",
        "T_media_C": "mean",
        "T_fundo_C": "mean"
    })
)

# Para visualização de um ciclo anual fechado, adicionamos
# o primeiro ponto novamente ao final, exatamente 365 dias depois.
# Isso não altera os dados físicos nem o CSV; apenas fecha visualmente
# a periodicidade do ciclo no gráfico.

data_grafico = resultados_diarios.index.append(
    pd.DatetimeIndex([
        resultados_diarios.index[0] + pd.Timedelta(days=365)
    ])
)

T_corrego_grafico = np.append(
    resultados_diarios["T_corrego_C"].values,
    resultados_diarios["T_corrego_C"].iloc[0]
)

T_media_grafico = np.append(
    resultados_diarios["T_media_C"].values,
    resultados_diarios["T_media_C"].iloc[0]
)

T_ar_grafico = np.append(
    resultados_diarios["T_ar_C"].values,
    resultados_diarios["T_ar_C"].iloc[0]
)

plt.figure(figsize=(14, 6))

plt.plot(data_grafico, T_corrego_grafico, label="Córrego", linewidth=2)
plt.plot(data_grafico, T_media_grafico, label="Tanque", linewidth=2)
plt.plot(data_grafico, T_ar_grafico, label="Ar", alpha=0.6)

plt.xlabel("Data")
plt.ylabel("Temperatura média diária (°C)")
plt.title("Temperatura média diária")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("07_temperatura_diaria.png", dpi=300)
plt.show()


# ==============================================================
# 23. EXPORTAÇÃO DOS RESULTADOS
# ==============================================================

resultados.to_csv(
    "resultados_digital_twin.csv",
    index=False,
    decimal=",",
    sep=";"
)

print("\n==========================================")
print("ARQUIVOS GERADOS")
print("==========================================")

print("""
01_temperatura_corrego.png
02_temperatura_tanque.png
03_ar_corrego_tanque.png
04_mapa_calor_temperatura.png
05_perfil_vertical.png
06_balanco_termico.png
07_temperatura_diaria.png
resultados_digital_twin.csv
""")

print("==========================================")
print("FIM DA SIMULAÇÃO")
print("==========================================")