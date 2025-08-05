import streamlit as st
import pandas as pd
import numpy as np

st.title("Cálculo de VaR e Estresse - Modo Web")

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

# Entradas do usuário
pl = st.number_input("Digite o Patrimônio Líquido (R$)", min_value=0.0, format="%.2f")

horizonte_dias = st.selectbox("Horizonte de VaR (dias)", [1, 10, 21])
conf_level_label = st.selectbox("Nível de confiança", ["95%", "99%"])
conf_level, z_score = (0.95, 1.65) if conf_level_label == "95%" else (0.99, 2.33)

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
    st.markdown("*Modelo utilizado: Paramétrico - Delta Normal*")

    # Estresse
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
            "Impacto % do PL": round(impacto_total * 100, 4)
        })

    df_estresse = pd.DataFrame(resultados_estresse)

    st.markdown("### Resultado - Estresse por Fator de Risco")
    st.dataframe(df_estresse)

    # Download dos arquivos
    csv_var = df_var.to_csv(index=False).encode('utf-8')
    csv_estresse = df_estresse.to_csv(index=False).encode('utf-8')

    st.download_button("Baixar CSV - VaR", csv_var, "resultado_var.csv", "text/csv")
    st.download_button("Baixar CSV - Estresse", csv_estresse, "resultado_estresse.csv", "text/csv")
    import pandas as pd
from io import BytesIO

# ... (após calcular os resultados)

# Criar o DataFrame de perguntas e respostas
df_respostas = pd.DataFrame({
    "Pergunta": [...],  # lista de perguntas
    "Resposta": [...]   # lista de respostas calculadas
})

# Gerar Excel em memória
excel_output = BytesIO()
df_respostas.to_excel(excel_output, index=False, engine='openpyxl')
excel_output.seek(0)

# Botão de download no app
st.download_button(
    label="Baixar Relatório de Respostas (XLSX)",
    data=excel_output,
    file_name="relatorio_respostas_var_estresse.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
