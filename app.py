# app.py
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl
import datetime

# =============================
# CONFIGURAÇÃO DO SITE E CSS
# =============================
st.set_page_config(page_title="VaR App Finhealth", layout="wide")

st.markdown("""
<style>
    body {
        background-color: #f1f5f9;
        font-family: 'Segoe UI', sans-serif;
    }
    .main {
        padding: 2rem;
    }
    .stButton > button {
        background-color: #004080;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #0066cc;
        color: #fff;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #004080;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# TÍTULO E INFORMAÇÕES INICIAIS
# =============================
st.title("📊 Calculadora de VaR - Finhealth")

col1, col2, col3 = st.columns(3)
with col1:
    cnpj = st.text_input("CNPJ do Fundo *")
with col2:
    nome_fundo = st.text_input("Nome do Fundo *")
with col3:
    data_referencia = st.date_input("Data de Referência *", datetime.date.today())

pl = st.number_input("Patrimônio Líquido (R$) *", min_value=0.0, value=1000000.0, step=1000.0)

# Validação de campos obrigatórios
campos_ok = bool(cnpj.strip() and nome_fundo.strip() and pl > 0)
if not campos_ok:
    st.warning("⚠️ Preencha todos os campos obrigatórios (*)")

# =============================
# CONFIGURAÇÕES DE VAR
# =============================
st.subheader("Configurações de VaR")

col1, col2, col3 = st.columns(3)
with col1:
    horizonte_dias = st.selectbox("Horizonte (dias)", [1, 10, 21])
with col2:
    nivel_confianca = st.selectbox("Nível de Confiança", ["95%", "99%"])
    z_score = 1.65 if nivel_confianca == "95%" else 2.33
with col3:
    metodo = st.selectbox("Metodologia", [
        "Paramétrico (Delta-Normal)",
        "Paramétrico + Correlações"
    ], help="Metodologia para cálculo do VaR")

# =============================
# ALOCAÇÃO DE ATIVOS
# =============================
st.subheader("Alocação da Carteira")

classes = {
    "Ações (Ibovespa)": 0.25,
    "Juros-Pré": 0.08,
    "Câmbio (Dólar)": 0.15,
    "Cupom Cambial": 0.12,
    "Crédito Privado": 0.05,
    "Multimercado": 0.18,
    "Outros": 0.10
}

# Matriz de correlações
correlacoes = pd.DataFrame({
    "Ações (Ibovespa)": [1.00, 0.15, 0.60, 0.45, 0.20, 0.70, 0.30],
    "Juros-Pré": [0.15, 1.00, -0.20, 0.80, 0.40, 0.10, 0.25],
    "Câmbio (Dólar)": [0.60, -0.20, 1.00, 0.30, 0.10, 0.50, 0.20],
    "Cupom Cambial": [0.45, 0.80, 0.30, 1.00, 0.35, 0.40, 0.30],
    "Crédito Privado": [0.20, 0.40, 0.10, 0.35, 1.00, 0.25, 0.60],
    "Multimercado": [0.70, 0.10, 0.50, 0.40, 0.25, 1.00, 0.45],
    "Outros": [0.30, 0.25, 0.20, 0.30, 0.60, 0.45, 1.00]
}, index=list(classes.keys()))

carteira = []
colunas = st.columns(3)
for i, (classe, vol) in enumerate(classes.items()):
    with colunas[i % 3]:
        perc = st.number_input(f"{classe} (% do PL)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        if perc > 0:
            carteira.append({
                "classe": classe,
                "%PL": perc,
                "vol_anual": vol
            })

total = sum(item["%PL"] for item in carteira)
st.progress(total / 100 if total <= 100 else 1.0)

# Status da alocação
if total == 100:
    st.success(f"✅ Alocação: {total:.1f}% - Perfeito!")
elif total > 100:
    st.error(f"❌ Alocação: {total:.1f}% - Excede 100%!")
elif total > 0:
    st.warning(f"⚠️ Alocação: {total:.1f}% - Restam {100-total:.1f}%")

# =============================
# CÁLCULO DO VAR
# =============================
def calcular_var_simples(carteira, z_score, dias, pl):
    resultados = []
    var_total = 0
    for item in carteira:
        vol_d = item['vol_anual'] / np.sqrt(252)
        var_pct = z_score * vol_d * np.sqrt(dias)
        var_rs = pl * (item['%PL']/100) * var_pct
        resultados.append({
            "classe": item['classe'],
            "%PL": item['%PL'],
            "VaR (%)": round(var_pct * 100, 4),
            "VaR (R$)": round(var_rs, 2)
        })
        var_total += var_rs
    return resultados, var_total

def calcular_var_com_correlacoes(carteira, correlacoes, z_score, dias, pl):
    if not carteira:
        return [], 0, 0
    
    classes_na_carteira = [item['classe'] for item in carteira]
    pesos = np.array([item['%PL']/100 for item in carteira])
    vols = np.array([item['vol_anual']/np.sqrt(252) for item in carteira])
    
    # Submatriz de correlação
    corr_matrix = correlacoes.loc[classes_na_carteira, classes_na_carteira].values
    
    # Volatilidade do portfólio
    vol_portfolio_diaria = np.sqrt(np.dot(pesos, np.dot(corr_matrix * np.outer(vols, vols), pesos)))
    vol_portfolio_periodo = vol_portfolio_diaria * np.sqrt(dias)
    
    # VaR do portfólio
    var_portfolio_perc = z_score * vol_portfolio_periodo
    var_portfolio_reais = pl * var_portfolio_perc
    
    # VaR marginal por classe
    resultados = []
    for item in carteira:
        contribuicao_vol = (item['%PL']/100) * (item['vol_anual']/np.sqrt(252)) / vol_portfolio_diaria
        var_marginal_perc = var_portfolio_perc * contribuicao_vol
        var_marginal_reais = pl * var_marginal_perc
        resultados.append({
            "classe": item['classe'],
            "%PL": item['%PL'],
            "VaR (%)": round(var_marginal_perc * 100, 4),
            "VaR (R$)": round(var_marginal_reais, 2)
        })
    
    return resultados, var_portfolio_reais, var_portfolio_perc

# =============================
# CENÁRIOS DE ESTRESSE
# =============================
def calcular_cenarios_estresse(carteira, pl):
    cenarios = {
        "Ibovespa": -0.15,
        "Juros-Pré": 0.02,
        "Cupom Cambial": -0.01,
        "Dólar": -0.05,
        "Outros": -0.03
    }
    
    resultados = []
    for fator, choque in cenarios.items():
        impacto_total = 0
        for item in carteira:
            if fator.lower() in item['classe'].lower():
                impacto = choque * (item['%PL'] / 100)
                impacto_total += impacto
        resultados.append({
            "Fator de Risco": fator,
            "Choque": f"{choque:+.1%}",
            "Impacto (% PL)": round(impacto_total * 100, 4),
            "Impacto (R$)": round(pl * impacto_total, 2)
        })
    
    return resultados

# =============================
# RESULTADOS
# =============================
if st.button("🚀 Calcular VaR", disabled=not (campos_ok and total > 0 and total <= 100)):
    if metodo == "Paramétrico + Correlações":
        resultados, var_total, var_perc = calcular_var_com_correlacoes(carteira, correlacoes, z_score, horizonte_dias, pl)
        # Calcular também VaR simples para comparação
        resultados_simples, var_simples = calcular_var_simples(carteira, z_score, horizonte_dias, pl)
        beneficio = var_simples - var_total
    else:
        resultados, var_total = calcular_var_simples(carteira, z_score, horizonte_dias, pl)
        var_simples = var_total
        beneficio = 0
    
    # Exibir resultados
    st.subheader("📊 Resultados do VaR")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("VaR Total", f"R$ {var_total:,.0f}")
    with col2:
        st.metric("VaR (% PL)", f"{(var_total/pl)*100:.2f}%")
    with col3:
        if beneficio > 0:
            st.metric("Benefício Diversificação", f"R$ {beneficio:,.0f}")
        else:
            st.metric("Metodologia", metodo.split()[0])
    with col4:
        st.metric("Confiança", f"{nivel_confianca} / {horizonte_dias}d")
    
    # Tabela detalhada
    df = pd.DataFrame(resultados)
    st.dataframe(df, use_container_width=True)
    
    # Cenários de estresse
    st.subheader("⚠️ Teste de Estresse")
    cenarios_estresse = calcular_cenarios_estresse(carteira, pl)
    df_estresse = pd.DataFrame(cenarios_estresse)
    st.dataframe(df_estresse, use_container_width=True)
    
    # =============================
    # RESPOSTAS CVM/B3
    # =============================
    
    # Choques específicos de -1%
    choque_1pct = {
        "Ibovespa": -0.01,
        "Juros-Pré": -0.01,
        "Dólar": -0.01
    }
    
    resposta_ibov = sum(
        item['%PL'] / 100 * choque_1pct["Ibovespa"]
        for item in carteira if "ibovespa" in item["classe"].lower()
    ) * 100
    
    resposta_juros = sum(
        item['%PL'] / 100 * choque_1pct["Juros-Pré"]
        for item in carteira if "juros" in item["classe"].lower()
    ) * 100
    
    resposta_dolar = sum(
        item['%PL'] / 100 * choque_1pct["Dólar"]
        for item in carteira if "câmbio" in item["classe"].lower() or "dólar" in item["classe"].lower()
    ) * 100
    
    # DataFrame das respostas
    df_respostas = pd.DataFrame({
        "Pergunta": [
            "CNPJ do Fundo",
            "Portfolio",
            "Data de Referência",
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
            data_referencia.strftime("%d/%m/%Y"),
            f"{(var_total/pl)*100:.4f}%",
            metodo,
            "Cenário 1: Queda de 15% no IBOVESPA",
            "Cenário 2: Alta de 200 bps na taxa de juros",
            "Cenário 3: Queda de 1% no cupom cambial",
            "Cenário 4: Queda de 5% no dólar",
            "Cenário 5: Queda de 3% em outros ativos",
            f"{df['VaR (%)'].mean():.4f}%",
            f"{min(c['Impacto (% PL)'] for c in cenarios_estresse):.4f}%",
            f"{resposta_juros:.4f}%",
            f"{resposta_dolar:.4f}%",
            f"{resposta_ibov:.4f}%"
        ]
    })
    
    # =============================
    # DOWNLOADS
    # =============================
    st.subheader("📥 Downloads")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel completo
        excel_output = BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df_respostas.to_excel(writer, sheet_name='Respostas CVM_B3', index=False)
            df.to_excel(writer, sheet_name='VaR por Classe', index=False)
            df_estresse.to_excel(writer, sheet_name='Teste de Estresse', index=False)
        excel_output.seek(0)
        
        st.download_button(
            "📊 Baixar Relatório Completo",
            data=excel_output,
            file_name=f"relatorio_var_{nome_fundo.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        # Template oficial (se existir)
        template_path = "Template  Informações Perfil Mensal.xlsx"
        
        try:
            output_template = BytesIO()
            wb = openpyxl.load_workbook(template_path)
            ws = wb.active
            
            # Preencher template
            for col in range(3, ws.max_column + 1):
                pergunta_template = ws.cell(row=3, column=col).value
                if pergunta_template:
                    for _, row in df_respostas.iterrows():
                        if row["Pergunta"].strip()[:50] in pergunta_template.strip()[:50]:
                            ws.cell(row=6, column=col).value = row["Resposta"]
                            break
            
            wb.save(output_template)
            output_template.seek(0)
            
            st.download_button(
                "🏛️ Baixar Template CVM/B3",
                data=output_template,
                file_name=f"template_cvm_b3_{nome_fundo.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except FileNotFoundError:
            st.warning("⚠️ Template oficial não encontrado. Use o relatório completo.")
        except Exception as e:
            st.error(f"❌ Erro ao processar template: {str(e)}")

# =============================
# RODAPÉ
# =============================
st.markdown("---")
st.markdown("""
<div style='text-align: center; margin-top: 30px; font-size: 16px; color: #666;'>
    Desenvolvido com ❤️ por <strong>Finhealth</strong>
</div>
""", unsafe_allow_html=True)


