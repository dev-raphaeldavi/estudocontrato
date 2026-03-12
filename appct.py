import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES DA PÁGINA E ESTILIZAÇÃO
# ==========================================
st.set_page_config(page_title="ESTUDO DE CONTRATO", layout="wide", initial_sidebar_state="expanded")

# CSS: Mantendo exatamente a sua estrutura e design
st.markdown("""
    <style>
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stMainMenu"], .stDeployButton { display: none !important; }
    [data-testid="collapsedControl"] * { color: #1e293b !important; }
    .block-container { padding-top: 2rem !important; }
    .stApp, [data-testid="stSidebar"] { background-color: #FFFFFF !important; }

    div[data-baseweb="select"] > div, 
    [data-testid="stFormSubmitButton"] button, 
    [data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #7dd3fc 0%, #38bdf8 100%) !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
        min-height: 48px !important;
        padding: 10px 15px !important;
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
    }

    [data-testid="stFormSubmitButton"] button p, 
    [data-testid="stDownloadButton"] button p,
    div[data-baseweb="select"] div,
    span[data-baseweb="tag"] {
        color: #0f172a !important;
        font-weight: 700 !important;
        background-color: transparent !important;
        font-size: 1rem !important;
    }

    .custom-metric-card {
        background: linear-gradient(135deg, #7dd3fc 0%, #38bdf8 100%);
        border: 1px solid #38bdf8;
        border-radius: 6px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: left;
        margin-bottom: 1.2rem;
    }
    .custom-metric-title { color: #0f172a; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 8px; }
    .custom-metric-value { color: #014c8c; font-size: 2rem; font-weight: 800; }

    [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    </style>
""", unsafe_allow_html=True)

def criar_cartao(titulo, valor):
    st.markdown(f'<div class="custom-metric-card"><div class="custom-metric-title">{titulo}</div><div class="custom-metric-value">{valor}</div></div>', unsafe_allow_html=True)

# ==========================================
# 2. LÓGICA DE EXTENSÕES
# ==========================================
MAPA_EXTENSAO_KM = {
    '2218': 28.38, '2718': 28.38, '2219': 3.02, '2719': 3.02,
    '2220': 6.38, '2720': 6.38, '2221': 3.09, '2721': 3.09,
    '2222': 2.501, '2722': 2.501, '2307': 0.18, '2308': 0.24,
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1pMsiXxq2YlMKmItZRRJ6IjHs_DWrQq1b/export?format=csv"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        def limpar_moeda(v):
            if isinstance(v, str): v = v.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try: return float(v)
            except: return 0.0
        for c in ['VALOR DO CONTRATO', 'MEDIDO P0', 'VALOR TOTAL REAJUSTADO']:
            if c in df.columns: df[c] = df[c].apply(limpar_moeda)
        for c in ['WBS', 'LOCAL APLICADO', 'ANO DO CONTRATO']:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip()
                if c == 'ANO DO CONTRATO': df[c] = df[c].str.replace('.0', '', regex=False)
        return df
    except Exception as e:
        st.error(f"Erro na Planilha: {e}")
        return pd.DataFrame()

df = carregar_dados()

# ==========================================
# 4. SIDEBAR E FILTROS
# ==========================================
caminho_logo = "logo.png"
tem_logo = os.path.exists(caminho_logo)
if tem_logo: st.sidebar.image(caminho_logo, width=250)

df_filtrado = df.copy()
wbs_sel, locais_sel, anos_sel = [], [], []

if not df.empty:
    with st.sidebar.form("form_pesquisa"):
        st.markdown("### Filtros de Pesquisa")
        wbs_sel = st.multiselect("Estrutura (WBS):", options=sorted(df['WBS'].unique()), placeholder="Geral")
        locais_sel = st.multiselect("Local Aplicado:", options=sorted(df['LOCAL APLICADO'].unique()), placeholder="Geral")
        anos_sel = st.multiselect("Ano do Contrato:", options=sorted(df['ANO DO CONTRATO'].unique()), placeholder="Geral")
        btn_processar = st.form_submit_button("Processar Dados")

    if wbs_sel: df_filtrado = df_filtrado[df_filtrado['WBS'].isin(wbs_sel)]
    if locais_sel: df_filtrado = df_filtrado[df_filtrado['LOCAL APLICADO'].isin(locais_sel)]
    if anos_sel: df_filtrado = df_filtrado[df_filtrado['ANO DO CONTRATO'].isin(anos_sel)]

# ==========================================
# 5. CÁLCULOS
# ==========================================
v_contrato = df_filtrado['VALOR DO CONTRATO'].sum()
v_p0 = df_filtrado['MEDIDO P0'].sum()
v_reaj = df_filtrado['VALOR TOTAL REAJUSTADO'].sum()
diff = v_reaj - v_p0

if 'LOCAL APLICADO' in df_filtrado.columns and not df_filtrado.empty:
    ap_dren = df_filtrado['LOCAL APLICADO'].str.contains('DRENAGEM', case=False, na=False).all()
    if ap_dren: wbs_ext = df_filtrado['WBS'].unique()
    else: wbs_ext = df_filtrado[~df_filtrado['LOCAL APLICADO'].str.contains('DRENAGEM', case=False, na=False)]['WBS'].unique()
else: wbs_ext = []

ext_km = sum([MAPA_EXTENSAO_KM.get(str(w), 0) for w in wbs_ext])
c_km = v_reaj / ext_km if ext_km > 0 else 0

def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# 6. INTERFACE PRINCIPAL
# ==========================================
if tem_logo: st.image(caminho_logo, width=210)
st.title("ESTUDO DE CONTRATO")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1: criar_cartao("Valor Total do Contrato", fmt(v_contrato))
with col2: criar_cartao("Valor Total Medido (P0)", fmt(v_p0))
with col3: criar_cartao("Valor Total Reajustado", fmt(v_reaj))

col4, col5, col6 = st.columns(3)
with col4: criar_cartao("Diferença de Reajuste", fmt(diff))
with col5: criar_cartao("Extensão Total Única", f"{ext_km:.3f} km")
with col6: criar_cartao("Custo Total por KM", fmt(c_km))

# ==========================================
# 7. MOTOR DO PDF (COM IDENTIFICAÇÃO DO FILTRO)
# ==========================================
class RelatorioPDF(FPDF):
    def header(self):
        if tem_logo: self.image(caminho_logo, 10, 8, 40)
        self.set_xy(55, 15); self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'ESTUDO DE CONTRATO - RELATORIO GERENCIAL', 0, 1, 'L'); self.ln(20)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Impresso em: {datetime.now().strftime("%d/%m/%Y %H:%M")} | Pagina {self.page_no()}', 0, 0, 'C')

def gerar_pdf_bytes():
    pdf = RelatorioPDF()
    pdf.add_page()
    
    # --- Identificação dos Filtros no PDF ---
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "IDENTIFICAÇÃO DA PESQUISA:", 0, 1)
    pdf.set_font("Arial", '', 10)
    
    txt_wbs = f"WBS: {', '.join(wbs_sel)}" if wbs_sel else "WBS: Geral"
    txt_loc = f"Local Aplicado: {', '.join(locais_sel)}" if locais_sel else "Local Aplicado: Geral"
    txt_ano = f"Ano do Contrato: {', '.join(anos_sel)}" if anos_sel else "Ano do Contrato: Geral"
    
    pdf.cell(0, 6, txt_wbs, 0, 1)
    pdf.cell(0, 6, txt_loc, 0, 1)
    pdf.cell(0, 6, txt_ano, 0, 1)
    pdf.ln(5)
    
    # --- Métricas ---
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "METRICAS CONSOLIDADAS", 0, 1, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    m_list = [("Valor em referência ao Contrato ", fmt(v_contrato)), ("Valor em referência P0 ", fmt(v_p0)), ("Valor de Reajuste", fmt(diff)), ("Valor Final Reajustado", fmt(v_reaj)), ("Extensão (KM)", f"{ext_km:.3f} km"), ("Valor R$/KM", fmt(c_km))]
    for n, v in m_list:
        pdf.cell(60, 10, n, 1); pdf.cell(130, 10, v, 1); pdf.ln()
    
    out = pdf.output(dest='S')
    if isinstance(out, str):
        return out.encode('latin-1')
    return out

# Nome dinâmico do arquivo
nome_pdf = f"relatorio_{'_'.join(wbs_sel)}.pdf" if wbs_sel else "relatorio_geral.pdf"

st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 Relatórios")
st.sidebar.download_button(
    label="Baixar Relatório em PDF",
    data=gerar_pdf_bytes(),
    file_name=nome_pdf,
    mime="application/pdf",
    use_container_width=True
)
