import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from PIL import Image
from fpdf import FPDF

# 1. Configuração da página
st.set_page_config(page_title="Gerador de Orçamentos de Arquitetura", layout="wide")

# 2. Função de bloqueio por senha
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["senha_acesso"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Digite a senha para acessar:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Digite a senha para acessar:", type="password", on_change=password_entered, key="password")
        st.error("Senha incorreta.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 3. PERSISTÊNCIA DA TABELA DE PREÇOS
# ==========================================
ARQUIVO_PRECOS = "config_precos.json"

PRECOS_PADRAO = {
    "p_lev_seca": 5.0,
    "p_lev_molhada": 10.0,
    "p_cad": 7.0,
    "p_cortes": 10.0,
    "p_fachadas": 10.0,
    "p_arq": 20.0,
    "p_exec": 75.0,
    "p_maq": 30.0,
    "p_ele": 25.0,
    "p_hidro": 45.0,
    "p_render_img": 100.0,
    "p_render_vid": 600.0
}

def carregar_precos():
    if os.path.exists(ARQUIVO_PRECOS):
        try:
            with open(ARQUIVO_PRECOS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return {**PRECOS_PADRAO, **dados}
        except Exception:
            return PRECOS_PADRAO.copy()
    return PRECOS_PADRAO.copy()

def salvar_precos(novos_precos):
    with open(ARQUIVO_PRECOS, "w", encoding="utf-8") as f:
        json.dump(novos_precos, f, indent=4, ensure_ascii=False)

precos_atuais = carregar_precos()

# ==========================================
# 4. BARRA LATERAL (COM SALVAMENTO PERMANENTE)
# ==========================================
st.sidebar.header("Tabela de Preços (R$/un ou m²)")

p_lev_seca = st.sidebar.number_input("Levantamento - Seca (m²)", value=float(precos_atuais["p_lev_seca"]), step=1.0)
p_lev_molhada = st.sidebar.number_input("Levantamento - Molhada (m²)", value=float(precos_atuais["p_lev_molhada"]), step=1.0)
p_cad = st.sidebar.number_input("Desenho Levantamento CAD (m²)", value=float(precos_atuais["p_cad"]), step=1.0)
p_cortes = st.sidebar.number_input("Cortes Avulsos (m²)", value=float(precos_atuais["p_cortes"]), step=1.0)
p_fachadas = st.sidebar.number_input("Fachadas Avulsas (m²)", value=float(precos_atuais["p_fachadas"]), step=1.0)
p_arq = st.sidebar.number_input("Projeto de Arquitetura (m²)", value=float(precos_atuais["p_arq"]), step=1.0)
p_exec = st.sidebar.number_input("Projeto Executivo Completo (m²)", value=float(precos_atuais["p_exec"]), step=1.0)
p_maq = st.sidebar.number_input("Maquete Gráfica 3D (m²)", value=float(precos_atuais["p_maq"]), step=1.0)
p_ele = st.sidebar.number_input("Proj. Elétrica/Ilum. Avulso (m²)", value=float(precos_atuais["p_ele"]), step=1.0)
p_hidro = st.sidebar.number_input("Proj. Hidrossanitário Avulso (m² Molhada)", value=float(precos_atuais["p_hidro"]), step=1.0)
p_render_img = st.sidebar.number_input("Render Imagem (un)", value=float(precos_atuais["p_render_img"]), step=10.0)
p_render_vid = st.sidebar.number_input("Render Vídeo (un)", value=float(precos_atuais["p_render_vid"]), step=50.0)

if st.sidebar.button("💾 Salvar Preços como Padrão", use_container_width=True):
    novos_dados = {
        "p_lev_seca": p_lev_seca,
        "p_lev_molhada": p_lev_molhada,
        "p_cad": p_cad,
        "p_cortes": p_cortes,
        "p_fachadas": p_fachadas,
        "p_arq": p_arq,
        "p_exec": p_exec,
        "p_maq": p_maq,
        "p_ele": p_ele,
        "p_hidro": p_hidro,
        "p_render_img": p_render_img,
        "p_render_vid": p_render_vid
    }
    salvar_precos(novos_dados)
    st.sidebar.success("Tabela de preços salva com sucesso!")

# ==========================================
# 5. INTERFACE PRINCIPAL E METRAGENS
# ==========================================
st.title("Calculadora de Orçamentos e Propostas Técnicas")
st.write("Configure o escopo do projeto, aplique descontos progressivos e exporte a proposta comercial em PDF.")

st.header("1. Identificação e Metragens do Projeto")
col_id1, col_id2, col_id3 = st.columns(3)
with col_id1:
    nome_cliente = st.text_input("Nome do Cliente", value="Cliente")
with col_id2:
    titulo_projeto = st.text_input("Identificação do Projeto / Imóvel", value="Residência Unifamiliar")
with col_id3:
    validade_proposta = st.text_input("Validade da Proposta", value="15 dias")

col1, col2 = st.columns(2)
with col1:
    area_seca = st.number_input("Área Seca Total (m²)", min_value=0.0, value=50.0, step=1.0)
with col2:
    area_molhada = st.number_input("Área Molhada Total (m²)", min_value=0.0, value=15.0, step=1.0)

area_total = area_seca + area_molhada

# ==========================================
# 6. SELEÇÃO DE ESCOPO E REGRAS DE NEGÓCIO
# ==========================================
st.header("2. Escopo do Orçamento")
servicos = st.multiselect(
    "Quais serviços compõem esta proposta?",
    [
        "Levantamento Técnico", "Desenho Levantamento CAD", "Cortes", "Fachadas", 
        "Projeto de Arquitetura", "Projeto Executivo", 
        "Maquete Gráfica", "Proj. Elétrica e Iluminação", 
        "Proj. Hidrossanitário", "Renderização de Imagens", "Renderização de Vídeo"
    ],
    default=["Levantamento Técnico", "Desenho CAD"]
)

executivo_ativo = "Projeto Executivo" in servicos
arq_ativo = "Projeto de Arquitetura" in servicos

if executivo_ativo:
    st.info(
        "ℹ️ **Projeto Executivo Selecionado:** Os projetos de **Elétrica/Iluminação** e **Hidrossanitário** "
        "já estão englobados neste pacote (sem cobrança duplicada) e contam como **3 serviços** no gatilho de desconto. "
        "O **Projeto de Arquitetura** permanece independente."
    )

# Tratamento de sobreposição opcional para Cortes e Fachadas quando Arquitetura está ativo
cobrar_cortes_fachadas = True
if arq_ativo and ("Cortes" in servicos or "Fachadas" in servicos):
    cobrar_cortes_fachadas = st.checkbox(
        "Cobrar Cortes/Fachadas separadamente do Projeto de Arquitetura? (Desmarque se já estiverem inclusos na Arquitetura)",
        value=False
    )

col_q1, col_q2 = st.columns(2)
with col_q1:
    qtd_img = st.number_input("Qtd. de Imagens Renderizadas", min_value=1, value=4) if "Renderização de Imagens" in servicos else 0
with col_q2:
    qtd_vid = st.number_input("Qtd. de Vídeos Renderizados", min_value=1, value=1) if "Renderização de Vídeo" in servicos else 0

# ==========================================
# 7. CÁLCULO FINANCEIRO E PESO DE DESCONTO
# ==========================================
detalhamento = []
subtotal = 0.0
pontos_desconto = 0.0

if "Levantamento Técnico" in servicos:
    val = (area_seca * p_lev_seca) + (area_molhada * p_lev_molhada)
    subtotal += val
    pontos_desconto += 1.0
    detalhamento.append({"Produto": "Levantamento Técnico", "Base": f"{area_seca}m² Seca + {area_molhada}m² Molhada", "Valor (R$)": val, "Status": "Cobrado"})

if "Desenho Levantamento CAD" in servicos:
    val = area_total * p_cad
    subtotal += val
    pontos_desconto += 1.0
    detalhamento.append({"Produto": "Desenho CAD (Digitalização)", "Base": f"{area_total} m²", "Valor (R$)": val, "Status": "Cobrado"})

if "Cortes" in servicos:
    if arq_ativo and not cobrar_cortes_fachadas:
        detalhamento.append({"Produto": "Cortes Técnicos", "Base": f"{area_total} m²", "Valor (R$)": 0.0, "Status": "Incluso no Proj. Arquitetura"})
    else:
        val = area_total * p_cortes
        subtotal += val
        pontos_desconto += 0.5
        detalhamento.append({"Produto": "Cortes Técnicos", "Base": f"{area_total} m²", "Valor (R$)": val, "Status": "Cobrado"})

if "Fachadas" in servicos:
    if arq_ativo and not cobrar_cortes_fachadas:
        detalhamento.append({"Produto": "Fachadas", "Base": f"{area_total} m²", "Valor (R$)": 0.0, "Status": "Incluso no Proj. Arquitetura"})
    else:
        val = area_total * p_fachadas
        subtotal += val
        pontos_desconto += 0.5
        detalhamento.append({"Produto": "Fachadas", "Base": f"{area_total} m²", "Valor (R$)": val, "Status": "Cobrado"})

if "Projeto de Arquitetura" in servicos:
    val = area_total * p_arq
    subtotal += val
    pontos_desconto += 1.0
    detalhamento.append({"Produto": "Projeto de Arquitetura", "Base": f"{area_total} m²", "Valor (R$)": val, "Status": "Cobrado"})

if "Projeto Executivo" in servicos:
    val = area_total * p_exec
    subtotal += val
    pontos_desconto += 3.0  # Engloba Detalhamento Executivo + Elétrica/Iluminação + Hidrossanitário
    detalhamento.append({
        "Produto": "Projeto Executivo Completo", 
        "Base": f"{area_total} m²", 
        "Valor (R$)": val, 
        "Status": "Inclui Detalhamento, Elétrica e Hidrossanitário"
    })
    detalhamento.append({
        "Produto": "↳ Proj. Elétrica e Iluminação", 
        "Base": f"{area_total} m²", 
        "Valor (R$)": 0.0, 
        "Status": "Incluso no Projeto Executivo"
    })
    detalhamento.append({
        "Produto": "↳ Proj. Hidrossanitário", 
        "Base": f"{area_molhada} m² (Área Molhada)", 
        "Valor (R$)": 0.0, 
        "Status": "Incluso no Projeto Executivo"
    })
else:
    if "Proj. Elétrica e Iluminação" in servicos:
        val = area_total * p_ele
        subtotal += val
        pontos_desconto += 1.0
        detalhamento.append({"Produto": "Proj. Elétrica e Iluminação", "Base": f"{area_total} m²", "Valor (R$)": val, "Status": "Cobrado"})

    if "Proj. Hidrossanitário" in servicos:
        val = area_molhada * p_hidro
        subtotal += val
        pontos_desconto += 1.0
        detalhamento.append({"Produto": "Proj. Hidrossanitário", "Base": f"{area_molhada} m² (Área Molhada)", "Valor (R$)": val, "Status": "Cobrado"})

if "Maquete Gráfica" in servicos:
    val = area_total * p_maq
    subtotal += val
    pontos_desconto += 1.0
    detalhamento.append({"Produto": "Maquete Gráfica 3D", "Base": f"{area_total} m²", "Valor (R$)": val, "Status": "Cobrado"})

if "Renderização de Imagens" in servicos:
    val = qtd_img * p_render_img
    subtotal += val
    pontos_desconto += 1.0
    detalhamento.append({"Produto": f"Renderização de Imagens ({qtd_img} un.)", "Base": f"{qtd_img} un.", "Valor (R$)": val, "Status": "Cobrado"})

if "Renderização de Vídeo" in servicos:
    val = qtd_vid * p_render_vid
    subtotal += val
    pontos_desconto += 1.0
    detalhamento.append({"Produto": f"Renderização de Vídeo ({qtd_vid} un.)", "Base": f"{qtd_vid} un.", "Valor (R$)": val, "Status": "Cobrado"})

# ==========================================
# 8. FECHAMENTO, DESCONTOS E INFLAÇÃO
# ==========================================
st.header("3. Fechamento de Valores")

if pontos_desconto >= 6.0:
    desconto_sugerido = 15.0
elif pontos_desconto >= 4.0:
    desconto_sugerido = 10.0
elif pontos_desconto >= 2.0:
    desconto_sugerido = 5.0
else:
    desconto_sugerido = 0.0

if detalhamento:
    st.dataframe(pd.DataFrame(detalhamento), use_container_width=True, hide_index=True)

col_d1, col_d2 = st.columns(2)
with col_d1:
    st.caption(f"Pontuação técnica do pacote: **{pontos_desconto:g} pts** (Desconto automático sugerido: **{desconto_sugerido:.0f}%**)")
    usar_desc_manual = st.checkbox("Personalizar percentual de desconto manualmente?", value=False)
    if usar_desc_manual:
        perc_desconto_final = st.number_input("Desconto aplicado (%)", min_value=0.0, max_value=50.0, value=desconto_sugerido, step=1.0)
    else:
        perc_desconto_final = desconto_sugerido

with col_d2:
    aplicar_inflacao = st.checkbox("Aplicar correção inflacionária anual (IPCA / INCC / IGP-M)?", value=False)
    inflacao_anual = st.number_input(
        "Índice acumulado do ano anterior (%)", 
        min_value=0.0, max_value=100.0, value=4.50, step=0.10,
        disabled=not aplicar_inflacao
    )

valor_desconto = subtotal * (perc_desconto_final / 100.0)
valor_com_desconto = subtotal - valor_desconto
acrescimo_inflacao = valor_com_desconto * (inflacao_anual / 100.0) if aplicar_inflacao else 0.0
valor_final_reajustado = valor_com_desconto + acrescimo_inflacao

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

col3, col4, col5, col6 = st.columns(4)
col3.metric("Subtotal", formatar_moeda(subtotal))
col4.metric(f"Desconto ({perc_desconto_final:.0f}%)", f"- {formatar_moeda(valor_desconto)}")
col5.metric(
    f"Inflação ({inflacao_anual:.2f}%)" if aplicar_inflacao else "Inflação (0%)", 
    f"+ {formatar_moeda(acrescimo_inflacao)}"
)
col6.metric("Valor Final", formatar_moeda(valor_final_reajustado))

condicoes_pagto = st.text_area(
    "Condições de Pagamento e Observações da Proposta (Sairão no PDF):",
    value="• 30% de sinal na assinatura do contrato e saldo parcelado conforme entregas técnicas.\n• Prazo de início imediato após confirmação e levantamento métrico."
)

# ==========================================
# 9. GERADOR DE PDF PROFISSIONAL COM MARCA D'ÁGUA
# ==========================================
def localizar_logo():
    nomes_possiveis = ["arq.png", "logo arq.jpg", "logo_arq.png", "logo_arq.jpg", "logo.png", "logo.jpg"]
    arquivos_pasta = os.listdir(".")
    for arq in arquivos_pasta:
        if arq.lower() in nomes_possiveis:
            return arq
    return None

def preparar_imagens_logo(caminho_logo):
    """Cria uma versão limpa da logo para o cabeçalho e uma marca d'água com 10% de opacidade."""
    img = Image.open(caminho_logo).convert("RGBA")
    dados = img.getdata()

    dados_cabecalho = []
    dados_marca_dagua = []

    for r, g, b, a in dados:
        # Remove o fundo branco (pixels claros > 240) deixando transparente
        if r > 240 and g > 240 and b > 240:
            dados_cabecalho.append((255, 255, 255, 0))
            dados_marca_dagua.append((255, 255, 255, 0))
        else:
            dados_cabecalho.append((r, g, b, a))
            # Aplica exatamente 10% de opacidade nos pixels da logo
            dados_marca_dagua.append((r, g, b, int(a * 0.10)))

    img_cab = Image.new("RGBA", img.size)
    img_cab.putdata(dados_cabecalho)
    caminho_cab = "_temp_logo_header.png"
    img_cab.save(caminho_cab, "PNG")

    img_wm = Image.new("RGBA", img.size)
    img_wm.putdata(dados_marca_dagua)
    caminho_wm = "_temp_logo_watermark.png"
    img_wm.save(caminho_wm, "PNG")

    return caminho_cab, caminho_wm

def limpar_texto_pdf(texto):
    """Garante compatibilidade com fontes padrão Latin-1 do FPDF."""
    substituicoes = {"↳": "->", "•": "-", "—": "-", "–": "-"}
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)
    return texto.encode("latin-1", "replace").decode("latin-1")

class PropostaPDF(FPDF):
    def __init__(self, logo_header=None, logo_watermark=None):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.logo_header = logo_header
        self.logo_watermark = logo_watermark
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # 1. Marca d'água centralizada em todas as páginas (10% opacidade)
        if self.logo_watermark and os.path.exists(self.logo_watermark):
            self.image(self.logo_watermark, x=35, y=78, w=140)

        # 2. Faixa superior institucional (Verde Petróleo da Logo #006863)
        self.set_fill_color(0, 104, 99)
        self.rect(0, 0, 210, 6, style="F")

        # 3. Logo nítida no cabeçalho
        if self.logo_header and os.path.exists(self.logo_header):
            self.image(self.logo_header, x=14, y=11, w=24)
            self_x_titulo = 42
        else:
            self_x_titulo = 14

        self.set_xy(self_x_titulo, 13)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0, 74, 70)  # Verde Petróleo Escuro (#004A46)
        self.cell(0, 8, limpar_texto_pdf("PROPOSTA TÉCNICA E COMERCIAL"), new_x="LMARGIN", new_y="NEXT")

        self.set_x(self_x_titulo)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(90, 100, 100)
        self.cell(0, 5, limpar_texto_pdf("Arquitetura, Engenharia Complementar e Modelagem 3D"), new_x="LMARGIN", new_y="NEXT")

        # Linha divisória fina
        self.set_draw_color(0, 104, 99)
        self.set_line_width(0.4)
        self.line(14, 36, 196, 36)
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(0, 104, 99)
        self.set_line_width(0.3)
        self.line(14, 282, 196, 282)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 110, 110)
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 10, limpar_texto_pdf(f"Proposta gerada em {data_hoje} | Página {self.page_no()}"), align="R")

def gerar_pdf_orcamento():
    caminho_logo = localizar_logo()
    logo_cab, logo_wm = (None, None)
    if caminho_logo:
        try:
            logo_cab, logo_wm = preparar_imagens_logo(caminho_logo)
        except Exception:
            pass

    pdf = PropostaPDF(logo_header=logo_cab, logo_watermark=logo_wm)
    pdf.add_page()

    # --- Bloco 1: Dados do Cliente e Metragens ---
    pdf.set_fill_color(234, 244, 243)  # Verde Água Suave (#EAF4F3)
    pdf.set_draw_color(0, 104, 99)
    pdf.rect(14, 40, 182, 24, style="DF")

    pdf.set_xy(18, 43)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 74, 70)
    pdf.cell(90, 6, limpar_texto_pdf(f"Cliente: {nome_cliente}"))
    pdf.cell(85, 6, limpar_texto_pdf(f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y')}"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(18)
    pdf.cell(90, 6, limpar_texto_pdf(f"Projeto: {titulo_projeto}"))
    pdf.cell(85, 6, limpar_texto_pdf(f"Validade da Proposta: {validade_proposta}"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(43, 48, 48)
    pdf.cell(
        175, 6, 
        limpar_texto_pdf(f"Quadro de Áreas: Área Seca: {area_seca:.2f} m²  |  Área Molhada: {area_molhada:.2f} m²  |  Área Total: {area_total:.2f} m²"),
        new_x="LMARGIN", new_y="NEXT"
    )

    pdf.ln(8)

    # --- Bloco 2: Tabela de Escopo ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 74, 70)
    pdf.cell(0, 8, limpar_texto_pdf("1. Detalhamento do Escopo Técnico e Investimento"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # Cabeçalho da Tabela
    pdf.set_fill_color(0, 104, 99)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(78, 8, limpar_texto_pdf("  Serviço / Disciplina"), border=0, fill=True)
    pdf.cell(42, 8, limpar_texto_pdf("Base de Cálculo"), border=0, fill=True, align="C")
    pdf.cell(32, 8, limpar_texto_pdf("Condição"), border=0, fill=True, align="C")
    pdf.cell(30, 8, limpar_texto_pdf("Valor (R$)  "), border=0, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    # Linhas da Tabela
    pdf.set_font("Helvetica", "", 9)
    for i, item in enumerate(detalhamento):
        if i % 2 == 0:
            pdf.set_fill_color(246, 250, 250)
        else:
            pdf.set_fill_color(234, 244, 243)

        incluso = item["Valor (R$)"] == 0.0
        if incluso:
            pdf.set_text_color(0, 104, 99)
            pdf.set_font("Helvetica", "I", 8.5)
            texto_valor = "Incluso  "
            status_curto = "Incluso no Pacote"
        else:
            pdf.set_text_color(43, 48, 48)
            pdf.set_font("Helvetica", "", 9)
            texto_valor = f"{formatar_moeda(item['Valor (R$)'])}  "
            status_curto = "Incluso + Compl." if "Inclui" in item["Status"] else "Escopo Ativo"

        pdf.cell(78, 7.5, limpar_texto_pdf(f"  {item['Produto']}"), border=0, fill=True)
        pdf.cell(42, 7.5, limpar_texto_pdf(str(item["Base"])), border=0, fill=True, align="C")
        pdf.cell(32, 7.5, limpar_texto_pdf(status_curto), border=0, fill=True, align="C")
        pdf.cell(30, 7.5, limpar_texto_pdf(texto_valor), border=0, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # --- Bloco 3: Resumo Financeiro ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 74, 70)
    pdf.cell(0, 8, limpar_texto_pdf("2. Resumo Financeiro da Proposta"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(43, 48, 48)
    pdf.cell(140, 7, limpar_texto_pdf("Subtotal Bruto dos Serviços:"), align="R")
    pdf.cell(42, 7, limpar_texto_pdf(formatar_moeda(subtotal)), align="R", new_x="LMARGIN", new_y="NEXT")

    if valor_desconto > 0:
        pdf.set_text_color(0, 104, 99)
        pdf.cell(140, 7, limpar_texto_pdf(f"Desconto Progressivo de Pacote ({perc_desconto_final:.0f}%):"), align="R")
        pdf.cell(42, 7, limpar_texto_pdf(f"- {formatar_moeda(valor_desconto)}"), align="R", new_x="LMARGIN", new_y="NEXT")

    if aplicar_inflacao and acrescimo_inflacao > 0:
        pdf.set_text_color(90, 100, 100)
        pdf.cell(140, 7, limpar_texto_pdf(f"Correção Inflacionária Anual ({inflacao_anual:.2f}%):"), align="R")
        pdf.cell(42, 7, limpar_texto_pdf(f"+ {formatar_moeda(acrescimo_inflacao)}"), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    # Faixa de Valor Final
    pdf.set_fill_color(0, 104, 99)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(130, 10, limpar_texto_pdf("  VALOR TOTAL DO INVESTIMENTO"), fill=True)
    pdf.cell(52, 10, limpar_texto_pdf(f"{formatar_moeda(valor_final_reajustado)}  "), fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # --- Bloco 4: Condições Comerciais ---
    if condicoes_pagto.strip():
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 74, 70)
        pdf.cell(0, 7, limpar_texto_pdf("3. Condições Comerciais e Observações"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(43, 48, 48)
        pdf.multi_cell(182, 5.5, limpar_texto_pdf(condicoes_pagto))

    return bytes(pdf.output())

st.header("4. Exportação Comercial")
if detalhamento:
    bytes_pdf = gerar_pdf_orcamento()
    nome_arq_pdf = f"Proposta_{nome_cliente.strip().replace(' ', '_')}.pdf"
    st.download_button(
        label="📄 Baixar Proposta Comercial em PDF (Com Marca d'Água)",
        data=bytes_pdf,
        file_name=nome_arq_pdf,
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.warning("Selecione pelo menos um serviço para habilitar a geração do PDF.")
