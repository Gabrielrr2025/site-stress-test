import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl
import plotly.express as px

st.set_page_config(page_title="VaR Calculator", layout="wide")

# ================== CSS MODERNO ==================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4 {
    color: #0f172a;
}
</style>
""", unsafe_allow_html=True)

# ================== ENTRADAS ==================
st.title("📊 VaR & Estresse de Carteira")

col1, col2, col3 = st.columns(3)
with col1:
    cnpj = st.text_input("CNPJ do Fundo", placeholder="00.000.000/0001-00")
with col2:
    nome_fundo = st.text_input("Nome do Fundo", placeholder="Fundo XPTO")
with col3:
    data_ref = st.date_input("Data de Referência")

pl = st.number_input("Digite o Patrimônio Líquido (R$)", min_value=0.0, format="%.2f")
horizonte_dias = st.selectbox("Horizonte de VaR (dias)", [1, 10, 21])
conf_label = st.selectbox("Nível de confiança", ["95%", "99%"])
conf, z = (0.95, 1.65) if conf_label == "95%" else (0.99, 2.33)

st.markdown("### Alocação da Carteira")
vols = {
    "Ações (Ibovespa)": 0.25,
    "Juros-Pré": 0.08,
    "Câmbio (Dólar)": 0.15,
    "Cupom Cambial": 0.12,
    "Crédito Privado": 0.05,
    "Multimercado": 0.18,
    "Outros": 0.10
}
carteira = []
cols = st.columns(3)
for i, (classe, vol) in enumerate(vols.items()):
    with cols[i % 3]:
        perc = st.number_input(f"{classe} (% do PL)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        if perc > 0:
            carteira.append({
                "classe": classe,
                "%PL": perc,
                "vol_anual": vol
            })

if st.button("Calcular"):
    for item in carteira:
        vol_d = item['vol_anual'] / np.sqrt(252)
        var_pct = z * vol_d * np.sqrt(horizonte_dias)
        var_rs = pl * (item['%PL'] / 100) * var_pct
        item.update({
            "VaR_%": round(var_pct * 100, 4),
            "VaR_R$": round(var_rs, 2)
        })
    df_var = pd.DataFrame(carteira)
    var_total = df_var["VaR_R$"].sum()

    st.subheader("📉 Resultado - VaR por Classe")
    st.dataframe(df_var)

    st.markdown(f"**VaR Total ({conf_label} em {horizonte_dias} dias): R$ {var_total:,.2f} "
                f"({(var_total/pl)*100:.4f}% do PL)**")
    st.markdown("*Modelo: Paramétrico - Delta Normal*")

    # Estresse
    choques = {
        "Ibovespa": -0.15,
        "Juros-Pré": 0.02,
        "Cupom Cambial": -0.01,
        "Dólar": -0.05,
        "Outros": -0.03
    }
    res_estresse = []
    for fator, choque in choques.items():
        impacto_total = sum(choque * (item['%PL']/100) for item in carteira if fator.lower() in item['classe'].lower())
        res_estresse.append({
            "Fator de Risco": fator,
            "Impacto % do PL": round(impacto_total * 100, 4)
        })
    df_estresse = pd.DataFrame(res_estresse)
    st.subheader("⚠️ Estresse por Fator de Risco")
    st.dataframe(df_estresse)

    # Perguntas/Respostas
    perguntas = [
        "CNPJ", "Portfolio", "Data de Referência",
        "Qual a variação diária percentual esperada para o valor da cota?",
        "Qual a variação diária percentual esperada para o valor da cota no pior cenário de estresse?",
        "Qual a variação diária percentual esperada para o patrimônio do fundo com -1% na taxa de juros (pré)?",
        "Qual a variação diária percentual esperada para o patrimônio do fundo com -1% na taxa de câmbio (US$/BRL)?"
    ]
    respostas = [
        cnpj, nome_fundo, str(data_ref),
        f"{(var_total/pl)*100:.4f}%",  # VaR
        f"{min(i['Impacto % do PL'] for i in res_estresse):.4f}%",  # Pior Estresse
        f"{next((i['Impacto % do PL'] for i in res_estresse if 'Juros' in i['Fator de Risco']), 0):.4f}%",
        f"{next((i['Impacto % do PL'] for i in res_estresse if 'Dólar' in i['Fator de Risco']), 0):.4f}%"
    ]
    df_resp = pd.DataFrame({"Pergunta": perguntas, "Resposta": respostas})

    # Gráficos
    fig = px.pie(df_var, values="%PL", names="classe", title="Distribuição da Carteira")
    st.plotly_chart(fig, use_container_width=True)

    # Downloads
    excel = BytesIO()
    df_resp.to_excel(excel, index=False, engine='openpyxl')
    excel.seek(0)
    st.download_button("📥 Baixar Relatório (XLSX)", data=excel, file_name="relatorio_var_estresse.xlsx")
