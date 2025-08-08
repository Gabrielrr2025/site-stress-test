import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl
import plotly.express as px
import plotly.graph_objects as go

# ===============================================
# CONFIGURAÇÃO DA PÁGINA E CSS CUSTOMIZADO
# ===============================================

st.set_page_config(
    page_title="VaR Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para design moderno
st.markdown("""
<style>
    /* Importar fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset e configurações gerais */
    .main {
        padding: 2rem 3rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header personalizado */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid #334155;
    }
    
    .header-title {
        color: #f1f5f9;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Cards personalizados */
    .custom-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    .card-title {
        color: #f1f5f9;
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Métricas estilizadas */
    .metric-container {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        border-color: #0ea5e9;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(14, 165, 233, 0.15);
    }
    
    .metric-value {
        color: #0ea5e9;
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }
    
    /* Status badges */
    .status-success {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10b981;
        color: #10b981;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid #f59e0b;
        color: #f59e0b;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-error {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        color: #ef4444;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    /* Sidebar personalizada */
    .css-1d391kg {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid #334155;
    }
    
    /* Botões customizados */
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(14, 165, 233, 0.3);
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===============================================
# SIDEBAR - CONFIGURAÇÕES E NAVEGAÇÃO
# ===============================================

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Configurações de VaR
    st.markdown("**VaR Parameters**")
    horizonte_dias = st.selectbox("Time Horizon", [1, 10, 21], index=2)
    conf_level_label = st.selectbox("Confidence Level", ["95%", "99%"])
    metodo_var = st.selectbox("Methodology", [
        "Parametric (Delta-Normal)",
        "Parametric + Correlations"
    ], index=1)
    
    st.markdown("---")
    st.markdown("**Data Sources**")
    fonte_dados = st.selectbox("Volatility Source", [
        "Fixed Data (Default)",
        "Real-time + Backup"
    ])

# ===============================================
# HEADER PRINCIPAL
# ===============================================

st.markdown("""
<div class="main-header">
    <div class="header-title">📊 VaR Calculator</div>
    <div class="header-subtitle">Advanced portfolio risk analysis with multiple methodologies</div>
</div>
""", unsafe_allow_html=True)

# ===============================================
# DADOS DO FUNDO
# ===============================================

st.markdown("""
<div class="custom-card">
    <div class="card-title">🏢 Fund Information</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    cnpj = st.text_input("CNPJ *", placeholder="00.000.000/0001-00")

with col2:
    nome_fundo = st.text_input("Fund Name *", placeholder="Portfolio name")

with col3:
    data_referencia = st.date_input("Reference Date *")

with col4:
    pl = st.number_input("Net Worth (BRL) *", min_value=0.0, format="%.2f", value=1000000.0)

# Validação de campos obrigatórios
campos_obrigatorios_preenchidos = bool(cnpj.strip() and nome_fundo.strip() and pl > 0)

# ===============================================
# CONFIGURAÇÕES VaR (VISUAL)
# ===============================================

conf_level, z_score = (0.95, 1.65) if conf_level_label == "95%" else (0.99, 2.33)

# ===============================================
# ALOCAÇÃO DA CARTEIRA
# ===============================================

st.markdown("""
<div class="custom-card">
    <div class="card-title">📊 Portfolio Allocation</div>
</div>
""", unsafe_allow_html=True)

# Volatilidades e correlações FIXAS
volatilidades_padrao = {
    "Ações (Ibovespa)": 0.25,
    "Juros-Pré": 0.08,
    "Câmbio (Dólar)": 0.15,
    "Cupom Cambial": 0.12,
    "Crédito Privado": 0.05,
    "Multimercado": 0.18,
    "Outros": 0.10
}

correlacoes = pd.DataFrame({
    "Ações (Ibovespa)": [1.00, 0.15, 0.60, 0.45, 0.20, 0.70, 0.30],
    "Juros-Pré": [0.15, 1.00, -0.20, 0.80, 0.40, 0.10, 0.25],
    "Câmbio (Dólar)": [0.60, -0.20, 1.00, 0.30, 0.10, 0.50, 0.20],
    "Cupom Cambial": [0.45, 0.80, 0.30, 1.00, 0.35, 0.40, 0.30],
    "Crédito Privado": [0.20, 0.40, 0.10, 0.35, 1.00, 0.25, 0.60],
    "Multimercado": [0.70, 0.10, 0.50, 0.40, 0.25, 1.00, 0.45],
    "Outros": [0.30, 0.25, 0.20, 0.30, 0.60, 0.45, 1.00]
}, index=list(volatilidades_padrao.keys()))

# Grid de alocação
cols = st.columns(3)
carteira = []

for i, (classe, vol) in enumerate(volatilidades_padrao.items()):
    with cols[i % 3]:
        perc = st.number_input(
            f"{classe}",
            min_value=0.0, 
            max_value=100.0, 
            value=0.0, 
            step=1.0,
            help=f"Annual volatility: {vol:.0%}"
        )
        if perc > 0:
            carteira.append({
                "classe": classe,
                "%PL": perc,
                "vol_anual": vol
            })

# Progress bar da alocação
total_alocacao = sum(item['%PL'] for item in carteira)
progress_value = min(total_alocacao / 100, 1.0)

st.progress(progress_value)

# Status da alocação
if total_alocacao == 100:
    st.markdown('<div class="status-success">✅ Total Allocation: 100% - Perfect!</div>', unsafe_allow_html=True)
    pode_calcular = True
elif total_alocacao > 100:
    st.markdown(f'<div class="status-error">❌ Total Allocation: {total_alocacao:.1f}% - Exceeds 100%</div>', unsafe_allow_html=True)
    pode_calcular = False
elif total_alocacao > 0:
    st.markdown(f'<div class="status-warning">⚠️ Total Allocation: {total_alocacao:.1f}% - Remaining: {100-total_alocacao:.1f}%</div>', unsafe_allow_html=True)
    pode_calcular = True
else:
    st.markdown('<div class="status-warning">⚠️ Please allocate your portfolio</div>', unsafe_allow_html=True)
    pode_calcular = False

# ===============================================
# CÁLCULO VaR
# ===============================================

def calcular_var_com_correlacoes(carteira, correlacoes, horizonte_dias, z_score, pl):
    """VaR Paramétrico considerando correlações"""
    if not carteira:
        return carteira, 0, 0
    
    classes = [item['classe'] for item in carteira]
    pesos = np.array([item['%PL']/100 for item in carteira])
    vols = np.array([item['vol_anual']/np.sqrt(252) for item in carteira])
    
    # Submatriz de correlação apenas para classes presentes
    corr_matrix = correlacoes.loc[classes, classes].values
    
    # Calcular volatilidade do portfólio
    vol_portfolio_diaria = np.sqrt(np.dot(pesos, np.dot(corr_matrix * np.outer(vols, vols), pesos)))
    vol_portfolio_periodo = vol_portfolio_diaria * np.sqrt(horizonte_dias)
    
    # VaR do portfólio total
    var_portfolio_perc = z_score * vol_portfolio_periodo
    var_portfolio_reais = pl * var_portfolio_perc
    
    # VaR marginal por classe (contribuição aproximada)
    for item in carteira:
        contribuicao_vol = (item['%PL']/100) * (item['vol_anual']/np.sqrt(252)) / vol_portfolio_diaria
        var_marginal_perc = var_portfolio_perc * contribuicao_vol
        var_marginal_reais = pl * var_marginal_perc
        item.update({
            "VaR_%": round(var_marginal_perc * 100, 4),
            "VaR_R$": round(var_marginal_reais, 2)
        })
    
    return carteira, var_portfolio_perc, var_portfolio_reais

# ===============================================
# BOTÃO DE CÁLCULO E RESULTADOS
# ===============================================

if st.button("🚀 Calculate VaR", disabled=not (campos_obrigatorios_preenchidos and total_alocacao > 0 and pode_calcular)):
    with st.spinner("Calculating portfolio risk..."):
        
        # Aplicar método selecionado
        if metodo_var == "Parametric + Correlations":
            carteira_resultado, var_portfolio_perc, var_portfolio_reais = calcular_var_com_correlacoes(
                carteira.copy(), correlacoes, horizonte_dias, z_score, pl)
        else:
            # Método simples (fallback)
            carteira_resultado = carteira.copy()
            for item in carteira_resultado:
                vol_diaria = item['vol_anual'] / np.sqrt(252)
                var_percentual = z_score * vol_diaria * np.sqrt(horizonte_dias)
                var_reais = pl * (item['%PL'] / 100) * var_percentual
                item.update({
                    "VaR_%": round(var_percentual * 100, 4),
                    "VaR_R$": round(var_reais, 2)
                })
            var_portfolio_reais = sum(item["VaR_R$"] for item in carteira_resultado)
            var_portfolio_perc = var_portfolio_reais / pl
        
        # ===============================================
        # MÉTRICAS PRINCIPAIS
        # ===============================================
        
        st.markdown("""
        <div class="custom-card">
            <div class="card-title">📈 Risk Metrics</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Calcular VaR sem correlações para comparação
        var_simples = sum(
            pl * (item['%PL'] / 100) * z_score * (item['vol_anual'] / np.sqrt(252)) * np.sqrt(horizonte_dias)
            for item in carteira_resultado
        )
        beneficio_diversificacao = var_simples - var_portfolio_reais
        reducao_perc = (beneficio_diversificacao / var_simples * 100) if var_simples > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">R$ {var_portfolio_reais:,.0f}</div>
                <div class="metric-label">Portfolio VaR</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{var_portfolio_perc*100:.2f}%</div>
                <div class="metric-label">VaR (% of NAV)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">R$ {beneficio_diversificacao:,.0f}</div>
                <div class="metric-label">Diversification Benefit</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{reducao_perc:.1f}%</div>
                <div class="metric-label">Risk Reduction</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ===============================================
        # TABELA DE RESULTADOS
        # ===============================================
        
        st.markdown("""
        <div class="custom-card">
            <div class="card-title">📊 Detailed Results</div>
        </div>
        """, unsafe_allow_html=True)
        
        df_var = pd.DataFrame(carteira_resultado)
        df_var['Exposure (BRL)'] = df_var['%PL'] * pl / 100
        df_var['Contribution (%)'] = (df_var['VaR_R$'] / var_portfolio_reais * 100).round(1)
        
        # Reformatar para exibição
        df_display = df_var[['classe', '%PL', 'Exposure (BRL)', 'VaR_%', 'VaR_R$', 'Contribution (%)']].copy()
        df_display.columns = ['Asset Class', 'Allocation (%)', 'Exposure (BRL)', 'VaR (%)', 'VaR (BRL)', 'Contribution (%)']
        
        # Formatação
        df_display['Allocation (%)'] = df_display['Allocation (%)'].apply(lambda x: f"{x:.1f}%")
        df_display['Exposure (BRL)'] = df_display['Exposure (BRL)'].apply(lambda x: f"R$ {x:,.0f}")
        df_display['VaR (%)'] = df_display['VaR (%)'].apply(lambda x: f"{x:.2f}%")
        df_display['VaR (BRL)'] = df_display['VaR (BRL)'].apply(lambda x: f"R$ {x:,.0f}")
        df_display['Contribution (%)'] = df_display['Contribution (%)'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_display, use_container_width=True)
        
        # ===============================================
        # GRÁFICOS INTERATIVOS
        # ===============================================
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza da alocação
            fig_pie = px.pie(
                values=df_var['%PL'], 
                names=df_var['classe'],
                title="Portfolio Allocation",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Gráfico de barras do VaR
            fig_bar = px.bar(
                x=df_var['VaR_R$'], 
                y=df_var['classe'],
                orientation='h',
                title="VaR by Asset Class",
                labels={'x': 'VaR (BRL)', 'y': 'Asset Class'}
            )
            fig_bar.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # ===============================================
        # MATRIZ DE CORRELAÇÃO
        # ===============================================
        
        if metodo_var == "Parametric + Correlations":
            with st.expander("🔗 Correlation Matrix"):
                classes_carteira = [item['classe'] for item in carteira_resultado]
                corr_subset = correlacoes.loc[classes_carteira, classes_carteira]
                
                fig_corr = px.imshow(
                    corr_subset,
                    text_auto=True,
                    color_continuous_scale='RdBu',
                    title="Asset Correlation Matrix"
                )
                fig_corr.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig_corr, use_container_width=True)
        
        # ===============================================
        # CENÁRIOS DE ESTRESSE
        # ===============================================
        
        st.markdown("""
        <div class="custom-card">
            <div class="card-title">⚠️ Stress Test Results</div>
        </div>
        """, unsafe_allow_html=True)
        
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
            for item in carteira_resultado:
                if fator.lower() in item['classe'].lower():
                    impacto = choque * (item['%PL'] / 100)
                    impacto_total += impacto
            resultados_estresse.append({
                "Risk Factor": fator,
                "Impact (% of NAV)": round(impacto_total * 100, 4),
                "Impact (BRL)": round(pl * impacto_total, 0)
            })

        df_estresse = pd.DataFrame(resultados_estresse)
        st.dataframe(df_estresse, use_container_width=True)
        
        # ===============================================
        # DOWNLOADS
        # ===============================================
        
        st.markdown("""
        <div class="custom-card">
            <div class="card-title">📥 Export Reports</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Preparar dados para relatório CVM/B3
        choque_fixos = {
            "Ibovespa": -0.01,
            "Juros-Pré": -0.01,
            "Dólar": -0.01
        }

        resposta_ibov = sum(
            item['%PL'] / 100 * choque_fixos["Ibovespa"]
            for item in carteira_resultado if "ibovespa" in item["classe"].lower()
        ) * 100

        resposta_juros = sum(
            item['%PL'] / 100 * choque_fixos["Juros-Pré"]
            for item in carteira_resultado if "juros" in item["classe"].lower()
        ) * 100

        resposta_dolar = sum(
            item['%PL'] / 100 * choque_fixos["Dólar"]
            for item in carteira_resultado if "câmbio" in item["classe"].lower() or "dólar" in item["classe"].lower()
        ) * 100

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
                f"{var_portfolio_perc*100:.4f}%",
                metodo_var,
                "Cenário 1: Queda de 15% no IBOVESPA",
                "Cenário 2: Alta de 200 bps na taxa de juros",
                "Cenário 3: Queda de 1% no cupom cambial",
                "Cenário 4: Queda de 5% no dólar",
                "Cenário 5: Queda de 3% em outros ativos",
                f"{df_var['VaR_%'].mean():.4f}%",
                f"{df_estresse['Impact (% of NAV)'].min():.4f}%",
                f"{resposta_juros:.4f}%",
                f"{resposta_dolar:.4f}%",
                f"{resposta_ibov:.4f}%"
            ]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Excel do resultado
            excel_output = BytesIO()
            with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
                df_display.to_excel(writer, sheet_name='VaR Results', index=False)
                df_estresse.to_excel(writer, sheet_name='Stress Test', index=False)
                df_respostas.to_excel(writer, sheet_name='CVM Responses', index=False)
            excel_output.seek(0)
            
            st.download_button(
                label="📊 Download Complete Report",
                data=excel_output,
                file_name=f"var_report_{nome_fundo.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # Excel apenas respostas CVM
            excel_cvm = BytesIO()
            df_respostas.to_excel(excel_cvm, index=False, engine='openpyxl')
            excel_cvm.seek(0)
            
            st.download_button(
                label="📋 Download CVM Template",
                data=excel_cvm,
                file_name=f"cvm_template_{nome_fundo.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ===============================================
# VALIDAÇÕES E AVISOS
# ===============================================

if not campos_obrigatorios_preenchidos:
    st.info("⚠️ **Required fields (*):** CNPJ, Fund Name, Reference Date and Net Worth must be filled to perform calculations.")
