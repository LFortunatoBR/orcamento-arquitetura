import streamlit as st
import pandas as pd

# 1. Configuração da página deve ser o primeiro comando Streamlit
st.set_page_config(page_title="Gerador de Orçamentos de Arquitetura", layout="wide")

# 2. Função de bloqueio por senha
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["senha_acesso"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Limpa a senha por segurança
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
    st.stop()  # Trava a execução do restante do código aqui

# ==========================================
# O RESTO DO SEU CÓDIGO COMEÇA AQUI
# ==========================================
st.title("Calculadora de Orçamentos e Projetos")
st.write("Insira as áreas do imóvel, selecione o escopo técnico e calcule a proposta com descontos progressivos.")
# 1. Metragens
st.header("1. Metragens do Projeto")
col1, col2 = st.columns(2)
with col1:
    area_seca = st.number_input("Área Seca Total (m²)", min_value=0.0, value=50.0, step=1.0)
with col2:
    area_molhada = st.number_input("Área Molhada Total (m²)", min_value=0.0, value=15.0, step=1.0)

area_total = area_seca + area_molhada

# 2. Tabela de Preços Base (Painel Lateral)
st.sidebar.header("Tabela de Preços (R$/un ou m²)")
p_lev_seca = st.sidebar.number_input("Levantamento - Seca", value=5.0)
p_lev_molhada = st.sidebar.number_input("Levantamento - Molhada", value=10.0)
p_cad = st.sidebar.number_input("Desenho CAD (m²)", value=10.0)
p_cortes = st.sidebar.number_input("Cortes", value=10.0)
p_fachadas = st.sidebar.number_input("Fachadas", value=10.0)
p_arq = st.sidebar.number_input("Projeto de Arquitetura (m²)", value=20.0)
p_exec = st.sidebar.number_input("Projeto Executivo (m²)", value=75.0)
p_maq = st.sidebar.number_input("Maquete Gráfica (m²)", value=30.0)
p_ele = st.sidebar.number_input("Proj. Elétrica/Ilum. (m²)", value=25.0)
p_hidro = st.sidebar.number_input("Proj. Hidrossanitário (m² Área Molhada)", value=45.0)
p_render_img = st.sidebar.number_input("Render Imagem (un)", value=100.0)
p_render_vid = st.sidebar.number_input("Render Vídeo (un)", value=600.0)

# 3. Seleção de Escopo
st.header("2. Escopo do Orçamento")
servicos = st.multiselect(
    "Quais serviços compõem esta proposta?",
    [
        "Levantamento Técnico", "Desenho CAD", "Cortes", "Fachadas", "Projeto de Arquitetura", "Projeto Executivo", 
        "Maquete Gráfica", "Proj. Elétrica e Iluminação", 
        "Proj. Hidrossanitário", "Renderização de Imagens", "Renderização de Vídeo"
    ],
    default=["Levantamento Técnico", "Desenho CAD"]
)

qtd_img = st.number_input("Qtd. de Imagens", min_value=1, value=4) if "Renderização de Imagens" in servicos else 0
qtd_vid = st.number_input("Qtd. de Vídeos", min_value=1, value=1) if "Renderização de Vídeo" in servicos else 0

# 4. Cálculo
detalhamento = []
subtotal = 0.0

if "Levantamento Técnico" in servicos:
    val = (area_seca * p_lev_seca) + (area_molhada * p_lev_molhada)
    subtotal += val
    detalhamento.append({"Produto": "Levantamento Técnico", "Base": "Mista", "Valor (R$)": val})
if "Desenho CAD" in servicos:
    val = area_total * p_cad
    subtotal += val
    detalhamento.append({"Produto": "Desenho CAD", "Base": f"{area_total} m²", "Valor (R$)": val})
if "Cortes" in servicos:
    val = area_total * p_cortes
    subtotal += val
    detalhamento.append({"Produto": "Cortes, "Base": f"{area_total}", "Valor (R$)": val})
if "Fachadas" in servicos:
    val = area_total * p_fachadas
    subtotal += val
    detalhamento.append({"Produto": "Fachadas", "Base": f"{area_total}", "Valor (R$)": val})
if "Projeto de Arquitetura" in servicos:
    val = area_total * p_arq
    subtotal += val
    detalhamento.append({"Produto": "Projeto de Arquitetura", "Base": f"{area_total} m²", "Valor (R$)": val})
if "Projeto Executivo" in servicos:
    val = area_total * p_exec
    subtotal += val
    detalhamento.append({"Produto": "Projeto Executivo", "Base": f"{area_total} m²", "Valor (R$)": val})
if "Maquete Gráfica" in servicos:
    val = area_total * p_maq
    subtotal += val
    detalhamento.append({"Produto": "Maquete Gráfica 3D", "Base": f"{area_total} m²", "Valor (R$)": val})
if "Proj. Elétrica e Iluminação" in servicos:
    val = area_total * p_ele
    subtotal += val
    detalhamento.append({"Produto": "Proj. Elétrica e Iluminação", "Base": f"{area_total} m²", "Valor (R$)": val})
if "Proj. Hidrossanitário" in servicos:
    val = area_molhada * p_hidro  # Restrito à área molhada
    subtotal += val
    detalhamento.append({"Produto": "Proj. Hidrossanitário", "Base": f"{area_molhada} m²", "Valor (R$)": val})
if "Renderização de Imagens" in servicos:
    val = qtd_img * p_render_img
    subtotal += val
    detalhamento.append({"Produto": f"Renders de Imagem ({qtd_img}x)", "Base": "Unidade", "Valor (R$)": val})
if "Renderização de Vídeo" in servicos:
    val = qtd_vid * p_render_vid
    subtotal += val
    detalhamento.append({"Produto": f"Render de Vídeo ({qtd_vid}x)", "Base": "Unidade", "Valor (R$)": val})

# 5. Aplicação de Descontos
st.header("3. Fechamento de Valores")
qnt_servicos = len(servicos)
desconto_perc = 0.0

if qnt_servicos >= 6:
    desconto_perc = 0.15  # 15% para propostas executivas completas
elif qnt_servicos >= 4:
    desconto_perc = 0.10  # 10% para pacotes intermediários
elif qnt_servicos >= 2:
    desconto_perc = 0.05  # 5% para junções básicas

valor_desconto = subtotal * desconto_perc
valor_final = subtotal - valor_desconto

if detalhamento:
    st.dataframe(pd.DataFrame(detalhamento), use_container_width=True)

col3, col4, col5 = st.columns(3)
col3.metric("Subtotal", f"R$ {subtotal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric(f"Desconto ({int(desconto_perc * 100)}%)", f"- R$ {valor_desconto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col5.metric("Valor Final", f"R$ {valor_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
