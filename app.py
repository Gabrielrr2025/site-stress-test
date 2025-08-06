import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl

st.markdown("<h1 style='text-align: center;'>📊 Cálculo de VaR e Estresse</h1>", unsafe_allow_html=True)
st.markdown("---")

# Campos iniciais
cnpj = st.text_input("CNPJ do Fundo")
nome_fundo = st.text_input("Nome do Fundo (Portfólio)")

pl = st.number_input("Digite o Patrimônio Líquido (R$)", min_value=0.0, format="%.2f")
horizonte_dias = st.selectbox("Horizonte de VaR (dias)", [1, 10, 21])
conf_level_label = st.selectbox("Nível de confiança", ["95%", "99%"])
conf_level, z_score = (0.95, 1.65) if conf_level_label == "95%" else (0.99, 2.33)

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
    st.success(f"📉 VaR Total ({conf_level_label} em {horizonte_dias} dias): R$ {var_total:,.2f} "
               f"({(var_total/pl)*100:.4f}% do PL)")
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

    # Respostas CVM/B3
    resposta_ibov = df_estresse[df_estresse['Fator de Risco'] == 'Ibovespa']['Impacto % do PL'].values[0]
    resposta_juros = df_estresse[df_estresse['Fator de Risco'] == 'Juros-Pré']['Impacto % do PL'].values[0]
    resposta_dolar = df_estresse[df_estresse['Fator de Risco'] == 'Dólar']['Impacto % do PL'].values[0]

    df_respostas = pd.DataFrame({
        "Pergunta": [
            "CNPJ do Fundo",
            "Portfolio",
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
            "Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% no preço das ações (IBOVESPA)?"
        ],
        "Resposta": [
            cnpj,
            nome_fundo,
            f"{(var_total/pl)*100:.4f}%",
            "Paramétrico - Delta Normal",
            "Cenário 1: Queda de 15% no IBOVESPA",
            "Cenário 2: Alta de 200 bps na taxa de juros",
            "Cenário 3: Queda de 1% no cupom cambial",
            "Cenário 4: Queda de 5% no dólar",
            "Cenário 5: Queda de 3% em outros ativos",
            f"{df_var['VaR_%'].mean():.4f}%",
            f"{df_estresse['Impacto % do PL'].min():.4f}%",
            f"{resposta_juros:.4f}%",
            f"{resposta_dolar:.4f}%",
            f"{resposta_ibov:.4f}%"
        ]
    })

    # Gerar Excel de respostas simples
    excel_output = BytesIO()
    df_respostas.to_excel(excel_output, index=False, engine='openpyxl')
    excel_output.seek(0)

    st.download_button(
        label="📥 Baixar Relatório de Respostas (XLSX)",
        data=excel_output,
        file_name="relatorio_respostas_var_estresse.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Gerar Excel formatado no padrão B3/CVM
    template_path = "Template - Informações Perfil Mensal.xlsx"
    output = BytesIO()
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    for col in range(3, ws.max_column + 1):
        pergunta_template = ws.cell(row=3, column=col).value
        if pergunta_template:
            for _, row in df_respostas.iterrows():
                if row["Pergunta"].strip()[:50] in pergunta_template.strip()[:50]:
                    ws.cell(row=6, column=col).value = row["Resposta"]
                    break

    wb.save(output)
    output.seek(0)

    st.download_button(
        label="📥 Baixar Relatório no Padrão da B3/CVM",
        data=output,
        file_name="relatorio_estresse_formatado_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
