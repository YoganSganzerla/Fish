# ==============================================================
# DIGITAL TWIN - MODELO DE CRESCIMENTO DA TILÁPIA - V1
# ==============================================================
#
# Integração com:
#   digital_twin_termico_Palotina_v3_CORRIGIDO.py
#
# Premissas V1:
# - Tilápia do Nilo (Oreochromis niloticus)
# - Peso inicial: 30 g
# - Peso de abate: 1.000 g
# - Ração disponível em quantidade suficiente
# - A temperatura influencia o apetite/crescimento
# - A ração NÃO é fator limitante
# - Passo do crescimento: 1 dia
# - Temperatura diária: média da temperatura horária do tanque
# - Sem mortalidade nesta V1
# - Sem limitação por oxigênio/amônia/densidade nesta V1
#
# IMPORTANTE:
# Os parâmetros de crescimento são parâmetros iniciais de modelagem
# e DEVEM ser calibrados posteriormente com dados reais da criação.
#
# Referências usadas para parametrização inicial:
# - FAO/AFFRIS: tabelas de alimentação para tilápia
# - Azaza et al. (2008): efeito da temperatura sobre crescimento
# - Qiang et al. (2012): temperatura/proteína e SGR de juvenis
#
# ============================================================== 

import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==============================================================
# 1. CONFIGURAÇÃO DO MODELO
# ==============================================================

# Arquivo do modelo térmico
ARQUIVO_TERMICO = Path(__file__).resolve().parent / "thermal_tank_model.py"

# -------------------------
# Peixes
# -------------------------
PESO_INICIAL_G = 30.0
PESO_ABATE_G = 1000.0

# ATENÇÃO: substituir pelo número real de peixes do tanque.
# O crescimento individual independe desse número na V1,
# mas a biomassa e a quantidade de ração dependem dele.
N_PEIXES = 10_000

# -------------------------
# Crescimento
# -------------------------
# SGR de referência no intervalo térmico ótimo.
# É um parâmetro calibrável, não uma constante universal.
SGR_BASE_OTIMO = 2.20       # %/dia

# Redução progressiva do SGR conforme o peixe aumenta de tamanho.
# 0 = nenhuma redução; valores maiores = maior redução.
EXPONENTE_TAMANHO = 0.12

# Temperatura de referência para o máximo crescimento.
T_OTIMO_MIN = 26.0
T_OTIMO_MAX = 30.0

# ==============================================================
# 2. TABELA DE RAÇÃO
# ==============================================================
#
# Valores iniciais baseados na tabela FAO/AFFRIS para sistemas
# intensivos. O modelo calcula a oferta diária em função da
# biomassa. Como a ração é considerada NÃO LIMITANTE, esta
# quantidade representa a oferta recomendada, e não uma restrição.
#
# Faixas usadas na V1:
# 20-100 g   -> 4 a 3 % BW/dia
# 100-250 g  -> 3 a 2 % BW/dia
# >250 g     -> 2 a 1,5 % BW/dia
#
# Dentro de cada faixa fazemos interpolação linear.
#
# Fonte: FAO/AFFRIS - Table 25, intensive tilapia farming.
# ============================================================== 

def taxa_racao_percentual(peso_g):
    """Retorna a taxa de alimentação (% da biomassa/dia)."""

    peso_g = float(peso_g)

    if peso_g < 20:
        # Não é relevante para o nosso povoamento de 30 g,
        # mas mantém a função robusta.
        return 5.0

    if peso_g <= 100:
        # 20 g -> 4%; 100 g -> 3%
        return np.interp(peso_g, [20, 100], [4.0, 3.0])

    if peso_g <= 250:
        # 100 g -> 3%; 250 g -> 2%
        return np.interp(peso_g, [100, 250], [3.0, 2.0])

    # 250 g -> 2%; 1000 g -> 1.5%
    return np.interp(peso_g, [250, 1000], [2.0, 1.5])


# ==============================================================
# 3. EFEITO DA TEMPERATURA
# ==============================================================

def fator_temperatura_crescimento(T):
    """
    Fator adimensional de efeito da temperatura sobre o crescimento.

    1.0 = condição ótima.
    Valores menores = redução do crescimento.

    A função é propositalmente suave e configurável.
    A literatura indica melhor crescimento aproximadamente em
    26-30 °C e redução importante em temperaturas mais baixas.
    """

    T = float(T)

    # Muito abaixo da faixa produtiva.
    if T <= 16.0:
        return 0.02

    if T < 20.0:
        return np.interp(T, [16.0, 20.0], [0.02, 0.12])

    if T < 22.0:
        return np.interp(T, [20.0, 22.0], [0.12, 0.35])

    if T < 24.0:
        return np.interp(T, [22.0, 24.0], [0.35, 0.60])

    if T < 26.0:
        return np.interp(T, [24.0, 26.0], [0.60, 0.85])

    if T <= 30.0:
        return 1.00

    if T < 32.0:
        return np.interp(T, [30.0, 32.0], [1.00, 0.75])

    if T < 34.0:
        return np.interp(T, [32.0, 34.0], [0.75, 0.30])

    return 0.10


# ==============================================================
# 4. EFEITO DO TAMANHO
# ==============================================================

def fator_tamanho(peso_g):
    """
    Reduz progressivamente o SGR à medida que o peixe aumenta.

    A forma é:
        f_W = (W / W_inicial)^(-expoente)

    Assim, o peixe cresce rapidamente quando pequeno e
    desacelera progressivamente próximo ao peso de abate.
    """

    peso_g = max(float(peso_g), PESO_INICIAL_G)

    return (peso_g / PESO_INICIAL_G) ** (-EXPONENTE_TAMANHO)


# ==============================================================
# 5. SGR E CRESCIMENTO DIÁRIO
# ==============================================================

def sgr_percentual_dia(peso_g, temperatura_C):
    """SGR instantâneo aproximado em %/dia."""

    f_T = fator_temperatura_crescimento(temperatura_C)
    f_W = fator_tamanho(peso_g)

    return SGR_BASE_OTIMO * f_T * f_W


def crescimento_diario(peso_g, temperatura_C):
    """
    Calcula o novo peso após um dia.

    Usamos a forma exponencial do SGR:

        W(t+1) = W(t) * exp(SGR/100)
    """

    sgr = sgr_percentual_dia(peso_g, temperatura_C)

    peso_novo = peso_g * np.exp(sgr / 100.0)

    ganho = peso_novo - peso_g

    return peso_novo, ganho, sgr


# ==============================================================
# 6. IMPORTAÇÃO DO MODELO TÉRMICO
# ==============================================================

def carregar_modelo_termico():
    """
    Executa o modelo térmico e recupera o último ano estabilizado.

    O arquivo térmico já contém:
      datas_analise
      T_MEDIA_analise
      T_SUPERFICIE_analise
      T_FUNDO_analise
    """

    if not os.path.exists(ARQUIVO_TERMICO):
        raise FileNotFoundError(
            f"Não encontrei '{ARQUIVO_TERMICO}'. "
            "Coloque este arquivo na mesma pasta do modelo de crescimento."
        )

    print("\n==============================================")
    print(" CARREGANDO MODELO TÉRMICO")
    print("==============================================")

    namespace = {}

    with open(ARQUIVO_TERMICO, "r", encoding="utf-8") as f:
        codigo = f.read()

    # O modelo térmico original possui plt.show().
    # Em execução normal isso pode abrir várias janelas.
    # Para V1 usamos o namespace diretamente após a execução.
    exec(compile(codigo, str(ARQUIVO_TERMICO), "exec"), namespace)

    return namespace


# ==============================================================
# 7. PREPARAÇÃO DA TEMPERATURA DIÁRIA
# ==============================================================

def preparar_temperatura_diaria(namespace):
    """Converte a série horária do último ano em média diária."""

    datas = pd.DatetimeIndex(namespace["datas_analise"])
    temperatura = np.asarray(namespace["T_MEDIA_analise"], dtype=float)

    df = pd.DataFrame({
        "data": datas,
        "T_media_C": temperatura,
    })

    diario = (
        df.set_index("data")
        .resample("D")
        .agg(T_media_C=("T_media_C", "mean"))
        .reset_index()
    )

    diario["dia_ano"] = diario["data"].dt.dayofyear

    return diario


# ==============================================================
# 8. SIMULAÇÃO DE UM LOTE
# ==============================================================

def simular_lote(data_povoamento, temperatura_diaria):
    """
    Simula um lote de tilápia até atingir 1 kg.

    data_povoamento: pd.Timestamp ou string YYYY-MM-DD
    """

    data_povoamento = pd.Timestamp(data_povoamento)

    # Repetimos o ciclo anual de temperatura quando necessário.
    temp_ref = temperatura_diaria.copy()
    temp_ref["dia_ano"] = temp_ref["data"].dt.dayofyear

    mapa_temperatura = (
        temp_ref.groupby("dia_ano")["T_media_C"]
        .mean()
        .to_dict()
    )

    data = data_povoamento
    peso = PESO_INICIAL_G
    dias = 0
    racao_total_kg = 0.0
    ganho_total_kg = 0.0

    registros = []

    while peso < PESO_ABATE_G and dias < 1000:

        dia_ano = data.dayofyear
        T = float(mapa_temperatura.get(dia_ano, np.mean(list(mapa_temperatura.values()))))

        # Biomassa antes da alimentação do dia.
        biomassa_kg = N_PEIXES * peso / 1000.0

        # Oferta recomendada de ração.
        taxa_racao = taxa_racao_percentual(peso)
        racao_dia_kg = biomassa_kg * taxa_racao / 100.0

        peso_anterior = peso

        peso, ganho_g, sgr = crescimento_diario(peso, T)

        ganho_total_kg += N_PEIXES * ganho_g / 1000.0
        racao_total_kg += racao_dia_kg

        registros.append({
            "data": data,
            "dia_ciclo": dias,
            "peso_medio_g": peso,
            "peso_anterior_g": peso_anterior,
            "ganho_g_dia": ganho_g,
            "SGR_percent_dia": sgr,
            "temperatura_C": T,
            "fator_temperatura": fator_temperatura_crescimento(T),
            "fator_tamanho": fator_tamanho(peso_anterior),
            "biomassa_kg": N_PEIXES * peso / 1000.0,
            "taxa_racao_percent_BW": taxa_racao,
            "racao_kg_dia": racao_dia_kg,
        })

        dias += 1
        data += pd.Timedelta(days=1)

    resultado = pd.DataFrame(registros)

    atingiu_abate = peso >= PESO_ABATE_G

    resumo = {
        "data_povoamento": data_povoamento,
        "data_abate": resultado["data"].iloc[-1] if len(resultado) else pd.NaT,
        "dias_ciclo": len(resultado),
        "peso_inicial_g": PESO_INICIAL_G,
        "peso_final_g": peso,
        "biomassa_inicial_kg": N_PEIXES * PESO_INICIAL_G / 1000.0,
        "biomassa_final_kg": N_PEIXES * peso / 1000.0,
        "racao_total_kg": racao_total_kg,
        "ganho_biomassa_kg": ganho_total_kg,
        "FCR_teorico": (
            racao_total_kg / ganho_total_kg
            if ganho_total_kg > 0 else np.nan
        ),
        "atingiu_1kg": atingiu_abate,
    }

    return resultado, resumo


# ==============================================================
# 9. SIMULAÇÃO DE TODAS AS DATAS DE POVOAMENTO
# ==============================================================

def simular_datas_povoamento(temperatura_diaria, intervalo_dias=15):
    """
    Simula povoamentos a cada N dias ao longo do ano.
    """

    primeira_data = pd.Timestamp("2025-01-01")

    resultados_resumo = []
    simulacoes = {}

    for offset in range(0, 365, intervalo_dias):

        data_povoamento = primeira_data + pd.Timedelta(days=offset)

        serie, resumo = simular_lote(
            data_povoamento,
            temperatura_diaria
        )

        resultados_resumo.append(resumo)
        simulacoes[data_povoamento] = serie

    resumo_df = pd.DataFrame(resultados_resumo)

    resumo_df["mes_povoamento"] = resumo_df["data_povoamento"].dt.month
    resumo_df["nome_mes"] = resumo_df["data_povoamento"].dt.strftime("%b")

    return resumo_df, simulacoes


# ==============================================================
# 10. GRÁFICOS
# ==============================================================

def gerar_graficos(serie, resumo_df, data_povoamento):

    # ----------------------------------------------------------
    # Peso x tempo
    # ----------------------------------------------------------
    plt.figure(figsize=(13, 5))
    plt.plot(serie["data"], serie["peso_medio_g"], linewidth=2)
    plt.axhline(PESO_ABATE_G, linestyle="--", linewidth=1)
    plt.title(f"Crescimento da tilápia - povoamento {data_povoamento:%d/%m/%Y}")
    plt.xlabel("Data")
    plt.ylabel("Peso médio (g)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("tilapia_01_peso.png", dpi=300)
    plt.show()

    # ----------------------------------------------------------
    # Temperatura x peso
    # ----------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(13, 5))

    ax1.plot(
        serie["data"],
        serie["peso_medio_g"],
        linewidth=2,
        label="Peso médio"
    )
    ax1.set_xlabel("Data")
    ax1.set_ylabel("Peso médio (g)")

    ax2 = ax1.twinx()
    ax2.plot(
        serie["data"],
        serie["temperatura_C"],
        linewidth=1.5,
        linestyle="--",
        label="Temperatura"
    )
    ax2.set_ylabel("Temperatura média (°C)")

    plt.title("Relação entre temperatura e crescimento")
    ax1.grid(alpha=0.3)
    fig.tight_layout()
    plt.savefig("tilapia_02_temperatura_crescimento.png", dpi=300)
    plt.show()

    # ----------------------------------------------------------
    # Comparação das datas de povoamento
    # ----------------------------------------------------------
    plt.figure(figsize=(13, 5))
    plt.plot(
        resumo_df["data_povoamento"],
        resumo_df["dias_ciclo"],
        marker="o",
        linewidth=1.5
    )
    plt.title("Tempo estimado para chegar a 1 kg conforme a data de povoamento")
    plt.xlabel("Data de povoamento")
    plt.ylabel("Dias até 1 kg")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("tilapia_03_data_povoamento.png", dpi=300)
    plt.show()

    # ----------------------------------------------------------
    # Ração acumulada
    # ----------------------------------------------------------
    plt.figure(figsize=(13, 5))
    plt.plot(
        serie["data"],
        serie["racao_kg_dia"].cumsum(),
        linewidth=2
    )
    plt.title("Ração acumulada no ciclo")
    plt.xlabel("Data")
    plt.ylabel("Ração acumulada (kg)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("tilapia_04_racao_acumulada.png", dpi=300)
    plt.show()


# ==============================================================
# 11. EXECUÇÃO PRINCIPAL
# ==============================================================

if __name__ == "__main__":

    print("\n==============================================")
    print(" DIGITAL TWIN - TILÁPIA V1")
    print("==============================================")
    print(f"Peso inicial       : {PESO_INICIAL_G:.1f} g")
    print(f"Peso de abate      : {PESO_ABATE_G:.1f} g")
    print(f"Número de peixes   : {N_PEIXES:,}")
    print(f"SGR base            : {SGR_BASE_OTIMO:.2f} %/dia")
    print(f"Faixa ótima T       : {T_OTIMO_MIN:.1f} - {T_OTIMO_MAX:.1f} °C")

    namespace = carregar_modelo_termico()

    temperatura_diaria = preparar_temperatura_diaria(namespace)

    print("\nTemperatura diária preparada.")
    print(
        f"Temperatura mínima: {temperatura_diaria['T_media_C'].min():.2f} °C"
    )
    print(
        f"Temperatura máxima: {temperatura_diaria['T_media_C'].max():.2f} °C"
    )
    print(
        f"Temperatura média : {temperatura_diaria['T_media_C'].mean():.2f} °C"
    )

    # ----------------------------------------------------------
    # Cenário principal: povoamento em 01/janeiro
    # ----------------------------------------------------------
    data_principal = pd.Timestamp("2025-01-01")

    serie_principal, resumo_principal = simular_lote(
        data_principal,
        temperatura_diaria
    )

    print("\n============= CICLO PRINCIPAL =============")
    for chave, valor in resumo_principal.items():
        print(f"{chave:25s}: {valor}")

    # ----------------------------------------------------------
    # Todas as datas
    # ----------------------------------------------------------
    resumo_datas, simulacoes = simular_datas_povoamento(
        temperatura_diaria,
        intervalo_dias=15
    )

    print("\n============= MELHORES DATAS =============")

    melhores = resumo_datas.sort_values("dias_ciclo").head(10)

    print(
        melhores[
            ["data_povoamento", "data_abate", "dias_ciclo",
             "racao_total_kg", "FCR_teorico"]
        ].to_string(index=False)
    )

    # ----------------------------------------------------------
    # Exportações
    # ----------------------------------------------------------
    serie_principal.to_csv(
        "tilapia_ciclo_principal.csv",
        index=False,
        encoding="utf-8-sig"
    )

    resumo_datas.to_csv(
        "tilapia_comparacao_datas_povoamento.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # Gráficos
    gerar_graficos(
        serie_principal,
        resumo_datas,
        data_principal
    )

    print("\n==============================================")
    print(" SIMULAÇÃO CONCLUÍDA")
    print("==============================================")
    print("Arquivos gerados:")
    print(" - tilapia_ciclo_principal.csv")
    print(" - tilapia_comparacao_datas_povoamento.csv")
    print(" - tilapia_01_peso.png")
    print(" - tilapia_02_temperatura_crescimento.png")
    print(" - tilapia_03_data_povoamento.png")
    print(" - tilapia_04_racao_acumulada.png")
