import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl

# Configuração da página
st.set_page_config(page_title="Cálculo de VaR e Estresse", layout="wide")

# Estilo customizado
st.markdown("""
    <style>
    body {
        background-color: #f8fafc;
    }
    .stApp {
        background-color: #f0f4f8;
        font-family: 'Segoe UI', sans-serif;
    }
    footer {
        visibility: visible;
    }
    footer:after {
        content: "Feito com ❤️ Finhealth";
        display: block;
        text-align: center;
        color: #475569;
        padding: 1rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Volatilidades padrão
volatilidades_padrao = {
    "Ações (Ibovespa)": 0.25,
    "Juros-Pré": 0.08,
    "Câmbio (Dólar)": 0.15,
    "Cupom Cambial": 0.12,
    "Crédito Privado": 0.05,
    "Multimercado": 0.18,
    "Outros": 0.10
}

# Entradas principais
st.title("📊 Cálculo de VaR e Estresse")

col1, col2, col3 = st.columns(3)
with col1:
    cnpj = st.text_input("CNPJ do Fundo")
with col2:
    nome_fundo = st.text_input("Nome do Fundo")
with col3:
    data_referencia = st.date_input("Data de Referência")

pl = st.number_input("Digite o Patrimônio Líquido (R$)", min_value=0.0, format="%.2f")

# Metodologia com explicação
tooltip_text = {
    "Paramétrico - Delta Normal": "Usa média e variância sob distribuição normal",
    "Histórico": "Baseado na série histórica de retornos",
    "Simulação de Monte Carlo": "Usa simulações aleatórias para estimar riscos"
}

metodologia = st.selectbox(
    "Metodologia de VaR",
    options=list(tooltip_text.keys()),
    format_func=lambda x: f"{x} (ℹ️ clique para detalhes)"
)

st.caption(f"ℹ️ {tooltip_text[metodologia]}")

# Nível de confiança e horizonte
col1, col2 = st.columns(2)
with col1:
    horizonte_dias = st.selectbox("Horizonte de VaR (dias)", [1, 10, 21])
with col2:
    conf_level_label = st.selectbox("Nível de confiança", ["95%", "99%"])
conf_level, z_score = (0.95, 1.65) if conf_level_label == "95%" else (0.99, 2.33)

# Alocação da Carteira
st.markdown("### Alocação da Carteira")
carteira = []
for classe, vol in volatilidades_padrao.items():
    perc = st.number_input(f"{classe} (% do PL)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
    if perc > 0:
        carteira.append({
            "classe": classe,
            "%PL": perc,
            "vol_anual": vol
        })

# Botão de cálculo
if st.button("Calcular"):
    for item in carteira:
        vol_diaria = item['vol_anual'] / np.sqrt(252)
        var_percentual = z_score * vol_diaria * np.sqrt(horizonte_dias)
        var_reais = pl * (item['%PL'] / 100) * var_percentual
        item.update({
            "VaR_%": round(var_percentual * 100, 4),
            "VaR_R$": round(var_reais, 2)
        })

    df_var = pd.DataFrame(carteira)

    st.markdown("### Resultado - VaR por Classe")
    st.dataframe(df_var)

    var_total = df_var["VaR_R$"].sum()
    st.markdown(f"**VaR Total ({conf_level_label} em {horizonte_dias} dias): R$ {var_total:,.2f} "
                f"({(var_total/pl)*100:.4f}% do PL)**")
    st.markdown(f"*Metodologia utilizada: {metodologia}*")

    # Estresse com explicação
    cenarios_estresse = [
        {"Fator de Risco": "Ibovespa", "Descrição": "Queda de 15% no IBOVESPA", "Choque": -0.15},
        {"Fator de Risco": "Juros-Pré", "Descrição": "Alta de 200 bps na taxa de juros", "Choque": 0.02},
        {"Fator de Risco": "Cupom Cambial", "Descrição": "Queda de 100 bps no cupom cambial", "Choque": -0.01},
        {"Fator de Risco": "Dólar", "Descrição": "Queda de 5% no dólar", "Choque": -0.05},
        {"Fator de Risco": "Outros", "Descrição": "Queda genérica de 3%", "Choque": -0.03},
    ]

    resultados_estresse = []
    for cenario in cenarios_estresse:
        impacto_total = 0
        for item in carteira:
            if cenario["Fator de Risco"].lower() in item['classe'].lower():
                impacto = cenario["Choque"] * (item['%PL'] / 100)
                impacto_total += impacto
        resultados_estresse.append({
            "Fator de Risco": cenario["Fator de Risco"],
            "Descrição": cenario["Descrição"],
            "Impacto (% do PL)": round(impacto_total * 100, 4),
            "Impacto (R$)": round(impacto_total * pl, 2)
        })

    df_estresse = pd.DataFrame(resultados_estresse)

    st.markdown("### Resultado - Estresse por Fator de Risco")
    st.dataframe(df_estresse)

    # Tabela de respostas
    perguntas = [
        "Qual é o VAR (Valor de risco) de um dia como percentual do PL calculado para 21 dias úteis e 95% de confiança?",
        "Qual classe de modelos foi utilizada para o cálculo do VAR reportado na questão anterior?",
        "Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) IBOVESPA que gere o pior resultado para o fundo, indique o cenário utilizado.",
        "Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Juros-Pré que gere o pior resultado para o fundo, indique o cenário utilizado.",
        "Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Cupom Cambial que gere o pior resultado para o fundo, indique o cenário utilizado.",
        "Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Dólar que gere o pior resultado para o fundo, indique o cenário utilizado.",
        "Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Outros que gere o pior resultado para o fundo, indique o cenário utilizado.",
        "Qual a variação diária percentual esperada para o valor da cota?",
        "Qual a variação diária percentual esperada para o valor da cota do fundo no pior cenário de estresse definido pelo seu administrador?",
        "Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% na taxa anual de juros (pré)?",
        "Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% na taxa de câmbio (US$/Real)?",
        "Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% no preço das ações (IBOVESPA)?",
        "CNPJ",
        "Portfolio"
    ]

    respostas = [
        f"{round(var_total / pl * 100, 4)}%",
        metodologia,
        "Queda de 15% no IBOVESPA",
        "Alta de 200 bps na taxa de juros",
        "Queda de 100 bps no cupom cambial",
        "Queda de 5% no dólar",
        "Queda genérica de 3%",
        f"{round(var_total / pl * 100, 4)}%",
        "-1.5%",
        "0.6%",
        "0.23%",
        "0.78%",
        cnpj,
        nome_fundo
    ]

    df_respostas = pd.DataFrame({"Pergunta": perguntas, "Resposta": respostas})

    excel_output = BytesIO()
    df_respostas.to_excel(excel_output, index=False, engine='openpyxl')
    excel_output.seek(0)

    st.download_button(
        label="📥 Baixar Respostas em Excel",
        data=excel_output,
        file_name="respostas_var_estresse.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Download do template gerado
    with open("template_perfil_mensal.xlsx", "rb") as file:
        st.download_button(
            label="📥 Download Manager Template",
            data=file,
            file_name="manager_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


