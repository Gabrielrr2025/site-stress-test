import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl
import plotly.express as px

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="VaR Calculator",
    page_icon="📊",
    layout="wide",
)

# CSS CUSTOMIZADO
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main {
        background-color: #f9fafb;
        padding: 2rem;
    }
    .metric-container {
        padding: 1.2rem;
        border-radius: 10px;
        background: #f1f5f9;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# VOLATILIDADES PADRÃO
volatilidades_padrao = {
    "Ações (Ibovespa)": 0.25,
    "Juros-Pré": 0.08,
    "Câmbio (Dólar)": 0.15,
    "Cupom Cambial": 0.12,
    "Crédito Privado": 0.05,
    "Multimercado": 0.18,
    "Outros": 0.10
}

# CAMPOS DO FUNDO
st.title("📊 Análise de Risco: VaR & Estresse")

col1, col2, col3 = st.columns(3)
with col1:
    cnpj = st.text_input("CNPJ do Fundo")
with col2:
    nome_fundo = st.text_input("Nome do Fundo")
with col3:
    data_referencia = st.date_input("Data de Referência")

# PATRIMÔNIO LÍQUIDO E PARÂMETROS
pl = st.number_input("Digite o Patrimônio Líquido (R$)", min_value=0.0, format="%.2f")
horizonte_dias = st.selectbox("Horizonte de VaR (dias)", [1, 10, 21])
conf_level_label = st.selectbox("Nível de confiança", ["95%", "99%"])
conf_level, z_score = (0.95, 1.65) if conf_level_label == "95%" else (0.99, 2.33)

# ALOCAÇÃO DA CARTEIRA
st.markdown("### Alocação da Carteira")
carteira = []
cols = st.columns(3)

for i, (classe, vol) in enumerate(volatilidades_padrao.items()):
    with cols[i % 3]:
        perc = st.number_input(f"{classe} (% do PL)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        if perc > 0:
            carteira.append({
                "classe": classe,
                "%PL": perc,
                "vol_anual": vol
            })

# CÁLCULO E RESULTADOS
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
    var_total = df_var["VaR_R$"].sum()

    st.markdown("### Resultado - VaR por Classe")
    st.dataframe(df_var)

    st.markdown(f"**VaR Total ({conf_level_label} em {horizonte_dias} dias): R$ {var_total:,.2f} "
                f"({(var_total/pl)*100:.4f}% do PL)**")
    st.markdown("*Modelo utilizado: Paramétrico - Delta Normal*")

    # CENÁRIOS DE ESTRESSE
    st.markdown("### Resultado - Estresse por Fator de Risco")
    cenarios_estresse = {
        "Ibovespa": -0.15,
        "Juros-Pré": 0.02,
        "Cupom Cambial": -0.01,
        "Dólar": -0.05,
        "Outros": -0.03
    }

    resultados_estresse = []
    for fator, choque in cenarios_estresse.items():
        impacto_total = 0
        for item in carteira:
            if fator.lower() in item['classe'].lower():
                impacto = choque * (item['%PL'] / 100)
                impacto_total += impacto
        resultados_estresse.append({
            "Fator de Risco": fator,
            "Impacto % do PL": round(impacto_total * 100, 4),
            "Cenário utilizado": f"Choque de {choque*100:.0f}%"
        })

    df_estresse = pd.DataFrame(resultados_estresse)
    st.dataframe(df_estresse)

    # DOWNLOADS
    csv_var = df_var.to_csv(index=False).encode('utf-8')
    csv_estresse = df_estresse.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar CSV - VaR", csv_var, "resultado_var.csv", "text/csv")
    st.download_button("📥 Baixar CSV - Estresse", csv_estresse, "resultado_estresse.csv", "text/csv")

    # Download do template preenchido
    with col2:
        with open("template_perfil_mensal.xlsx", "rb") as file:
            st.download_button(
                label="📥 Download Manager Template",
                data=file,
                file_name="manager_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

