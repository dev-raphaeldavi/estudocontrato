import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES DA PÁGINA E ESTILIZAÇÃO
# ==========================================
st.set_page_config(page_title="ESTUDO DE CONTRATO", layout="wide", initial_sidebar_state="expanded")

# CSS: Correção do botão da barra lateral e design dos cartões
st.markdown("""
    <style>
    /* ========================================================
       AJUSTE DO CABEÇALHO (Manter o botão da barra lateral visível)
       ======================================================== */
    /* Deixa o cabeçalho transparente em vez de ocultar tudo */
    [data-testid="stHeader"] { background-color: transparent !important; }
    
    /* Oculta apenas o Menu do Streamlit e o botão de Deploy */
    [data-testid="stMainMenu"], .stDeployButton { display: none !important; }
    
    /* Garante que o botão de reabrir a barra lateral fique escuro e visível */
    [data-testid="collapsedControl"] * { color: #1e293b !important; }

    .block-container { padding-top: 2rem !important; }

    /* Força fundo branco GERAL */
    .stApp, [data-testid="stSidebar"] { background-color: #FFFFFF !important; }
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp span, .stApp label, .stMarkdown {
        color: #1e293b !important;
    }

    /* ========================================================
       DESIGN UNIFICADO: FILTROS, PROCESSAR DADOS E BAIXAR PDF
       ======================================================== */
    div[data-baseweb="select"] > div, 
    [data-testid="stFormSubmitButton"] button, 
    [data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #7dd3fc 0%, #38bdf8 100%) !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        min-height: 42px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    div[data-baseweb="select"] > div:hover, 
    [data-testid="stFormSubmitButton"] button:hover, 
    [data-testid="stDownloadButton"] button:hover {
        background: linear-gradient(135deg, #bae6fd 0%, #7dd3fc 100%) !important;
        border-color: #7dd3fc !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.12) !important;
    }

    /* Manter texto escuro e sem fundo extra dentro dos botões */
    div[data-baseweb="select"] > div *, 
    [data-testid="stFormSubmitButton"] button *, 
    [data-testid="stDownloadButton"] button *,
    [data-testid="stFormSubmitButton"] button p, 
    [data-testid="stDownloadButton"] button p {
        background-color: transparent !important;
        color: #0f172a !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }

    /* Tirar bordas extras do Formulário do Streamlit */
    [data-testid="stForm"] { border: none !important; padding: 0 !important; }

    /* ========================================================
       CARTÕES DE MÉTRICAS (VISUAL APRESENTATIVO)
       ======================================================== */
    .custom-metric-card {
        background: linear-gradient(135deg, #7dd3fc 0%, #38bdf8 100%);
        border: 1px solid #38bdf8;
        border-radius: 6px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        text-align: left;
        margin-bottom: 1rem;
    }
    .custom-metric-card:hover {
        background: linear-gradient(135deg, #bae6fd 0%, #7dd3fc 100%);
        border-color: #7dd3fc;
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
    }
    .custom-metric-title {
        color: #0f172a;
        font-weight: 700;
        font-size: 0.95rem;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .custom-metric-value {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 800;
    }
    
    /* Dropdown Menus */
    ul[data-baseweb="menu"] { background-color: #ffffff !important; border: 1px solid #7dd3fc !important; }
    li[data-baseweb="menu-item"] { color: #0f172a !important; }
    li[data-baseweb="menu-item"]:hover { background-color: #e0f2fe !important; }
    span[data-baseweb="tag"] { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #38bdf8 !important; }
    </style>
""", unsafe_allow_html=True)

# Função para desenhar os cartões
def criar_cartao(titulo, valor):
    html = f"""
    <div class="custom-metric-card">
        <div class="custom-metric-title">{titulo}</div>
        <div class="custom-metric-value">{valor}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 2. DEFINIÇÃO DA LÓGICA DE EXTENSÕES
# ==========================================
MAPA_EXTENSAO_KM = {
    '2218': 28.38, '2718': 28.38, '2219': 3.02,  '2719': 3.02,
    '2220': 6.38,  '2720': 6.38,  '2221': 3.09,  '2721': 3.09,
    '2222': 2.501, '2722': 2.501,
    '2307': 0.18,  '2308': 0.24,
}

# ==========================================
# 3. CARREGAMENTO E TRATAMENTO DOS DADOS
# ==========================================
@st.cache_data
def carregar_dados():
    url_planilha = "https://docs.google.com/spreadsheets/d/1pMsiXxq2YlMKmItZRRJ6IjHs_DWrQq1b/export?format=csv"
    try:
        df = pd.read_csv(url_planilha)
        df.columns = df.columns.str.strip() 
        
        def limpar_moeda(valor):
            if isinstance(valor, str): valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try: return float(valor)
            except ValueError: return 0.0

        colunas_financeiras = ['VALOR DO CONTRATO', 'MEDIDO P0', 'VALOR TOTAL REAJUSTADO']
        for col in colunas_financeiras:
            if col in df.columns: df[col] = df[col].apply(limpar_moeda)
                
        colunas_texto = ['WBS', 'LOCAL APLICADO', 'ANO DO CONTRATO']
        for col in colunas_texto:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                if col == 'ANO DO CONTRATO': df[col] = df[col].str.replace('.0', '', regex=False)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

df = carregar_dados()

# ==========================================
# 4. BARRA LATERAL (LOGO E FORMULÁRIO DE FILTRO)
# ==========================================
caminho_logo = "logo.png"
tem_logo = os.path.exists(caminho_logo)

if tem_logo: st.sidebar.image(caminho_logo, width=250)
else: st.sidebar.warning("⚠️ Arquivo 'logo.png' não encontrado.")

df_filtrado = df.copy()

wbs_selecionadas, locais_selecionados, anos_selecionados = [], [], []

if not df.empty:
    texto_placeholder = "Deixe em branco p/ geral"
    
    with st.sidebar.form("form_pesquisa"):
        st.markdown("### Filtros de Pesquisa")
        
        if 'WBS' in df.columns:
            wbs_disponiveis = sorted(df['WBS'].unique())
            wbs_selecionadas = st.multiselect("Estrutura (WBS):", options=wbs_disponiveis, default=[], placeholder=texto_placeholder)
            
        if 'LOCAL APLICADO' in df.columns:
            locais = sorted(df['LOCAL APLICADO'].unique())
            locais_selecionados = st.multiselect("Local Aplicado:", options=locais, default=[], placeholder=texto_placeholder)
            
        if 'ANO DO CONTRATO' in df.columns:
            anos = sorted(df['ANO DO CONTRATO'].unique())
            anos_selecionados = st.multiselect("Ano do Contrato:", options=anos, default=[], placeholder=texto_placeholder)
            
        btn_processar = st.form_submit_button("Processar Dados")

    # Aplicação dos Filtros
    if wbs_selecionadas: df_filtrado = df_filtrado[df_filtrado['WBS'].isin(wbs_selecionadas)]
    if locais_selecionados: df_filtrado = df_filtrado[df_filtrado['LOCAL APLICADO'].isin(locais_selecionados)]
    if anos_selecionados: df_filtrado = df_filtrado[df_filtrado['ANO DO CONTRATO'].isin(anos_selecionados)]

# ==========================================
# 5. HEADER PRINCIPAL
# ==========================================
if tem_logo: st.image(caminho_logo, width=210)
st.title("ESTUDO DE CONTRATO")
st.markdown("Visão Gerencial Físico-Financeira")
st.markdown("---")

# ==========================================
# 6. CÁLCULOS DAS MÉTRICAS (SOMATÓRIAS CONDICIONAIS)
# ==========================================
valor_total_contrato = df_filtrado['VALOR DO CONTRATO'].sum() if 'VALOR DO CONTRATO' in df_filtrado else 0
valor_total_medido_p0 = df_filtrado['MEDIDO P0'].sum() if 'MEDIDO P0' in df_filtrado else 0
valor_total_reajustado = df_filtrado['VALOR TOTAL REAJUSTADO'].sum() if 'VALOR TOTAL REAJUSTADO' in df_filtrado else 0
diferenca_reajuste = valor_total_reajustado - valor_total_medido_p0

# Regra Inteligente de Extensão (Exclusão de Drenagem no cômputo geral)
wbs_para_extensao = []
if 'LOCAL APLICADO' in df_filtrado.columns and not df_filtrado.empty:
    # Verifica se os dados atuais são EXCLUSIVAMENTE de drenagem
    apenas_drenagem = df_filtrado['LOCAL APLICADO'].str.contains('DRENAGEM', case=False, na=False).all()
    
    if apenas_drenagem:
        # Se for análise individualizada de drenagem, pega as WBS atreladas a ela
        wbs_para_extensao = df_filtrado['WBS'].unique()
    else:
        # Se for visão geral ou mista, remove a drenagem da lista antes de buscar as WBS únicas
        df_sem_drenagem = df_filtrado[~df_filtrado['LOCAL APLICADO'].str.contains('DRENAGEM', case=False, na=False)]
        wbs_para_extensao = df_sem_drenagem['WBS'].unique()
else:
    wbs_para_extensao = df_filtrado['WBS'].unique() if 'WBS' in df_filtrado else []

extensao_total_km = sum([MAPA_EXTENSAO_KM.get(str(w), 0) for w in wbs_para_extensao])

# Regra de Custo por KM baseada na nova extensão inteligente
custo_total_por_km = valor_total_reajustado / extensao_total_km if extensao_total_km > 0 else 0

def format_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Exibição dos Cartões Personalizados
st.markdown("### Painel de Métricas Consolidadas")

col1, col2, col3 = st.columns(3)
with col1: criar_cartao("Valor Total do Contrato", format_moeda(valor_total_contrato))
with col2: criar_cartao("Valor Total Medido (P0)", format_moeda(valor_total_medido_p0))
with col3: criar_cartao("Valor Total Reajustado", format_moeda(valor_total_reajustado))

col4, col5, col6 = st.columns(3)
with col4: criar_cartao("Diferença de Reajuste", format_moeda(diferenca_reajuste))
with col5: criar_cartao("Extensão Total Única", f"{extensao_total_km:.3f} km")
with col6: criar_cartao("Custo Total por KM", format_moeda(custo_total_por_km))

st.markdown("---")

# ==========================================
# 7. GERAÇÃO DO RELATÓRIO PDF AVANÇADO
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 Relatórios")

class RelatorioPDF(FPDF):
    def header(self):
        if tem_logo:
            self.image(caminho_logo, 10, 8, 40) 
        self.set_xy(55, 15) 
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'ESTUDO DE CONTRATO - RELATORIO GERENCIAL', 0, 1, 'L')
        self.ln(20) 

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f'Impresso em: {agora} | Pagina {self.page_no()}/{{nb}}', 0, 0, 'C')

def gerar_pdf():
    pdf = RelatorioPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("Arial", 'I', 10)
    filtros_ativos = []
    if wbs_selecionadas: filtros_ativos.append(f"WBS: {', '.join(wbs_selecionadas)}")
    if locais_selecionados: filtros_ativos.append(f"Local: {', '.join(locais_selecionados)}")
    if anos_selecionados: filtros_ativos.append(f"Ano: {', '.join(anos_selecionados)}")
    
    if filtros_ativos:
        pdf.multi_cell(0, 6, "Filtros Aplicados: " + " | ".join(filtros_ativos))
    else:
        pdf.cell(0, 6, "Filtros Aplicados: Visao Geral (Todos os dados)", 0, 1)
    
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "RESUMO FINANCEIRO E METRICAS", 0, 1, 'L', fill=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, "Indicador", 1)
    pdf.cell(130, 10, "Valor", 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 10)
    dados_metricas = [
        ("Valor Total do Contrato", format_moeda(valor_total_contrato)),
        ("Valor Total Medido (P0)", format_moeda(valor_total_medido_p0)),
        ("Diferenca de Reajuste", format_moeda(diferenca_reajuste)),
        ("Valor Total Reajustado", format_moeda(valor_total_reajustado)),
        ("Extensao Total Considerada", f"{extensao_total_km:.3f} km"),
        ("Custo Medio por KM", format_moeda(custo_total_por_km))
    ]
    
    for nome, valor in dados_metricas:
        pdf.cell(60, 10, nome, 1)
        pdf.cell(130, 10, str(valor), 1)
        pdf.ln()

    return pdf.output(dest="S").encode("latin-1")

pdf_bytes = gerar_pdf()
st.sidebar.download_button(
    label="Baixar Relatório em PDF",
    data=pdf_bytes,
    file_name="estudo_de_contrato.pdf",
    mime="application/pdf",
    use_container_width=True
)