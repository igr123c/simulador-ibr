import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import time
import os
import replicate

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IBR Clinic System", layout="wide", page_icon="🦷")

# --- CSS PARA DEIXAR COM CARA DE APP PROFISSIONAL ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    h1 { color: #1e3a8a; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #2563eb; color: white; }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO MÁGICA DE IA (Replicate) ---
# (A linha de erro foi removida daqui)
def transformar_sorriso(image_file, tom):
    """
    Envia a foto para a IA (Replicate) e retorna o sorriso novo.
    """
    
    # Tenta pegar a chave dos Segredos do Streamlit
    try:
        api_key = st.secrets["REPLICATE_API_TOKEN"]
        os.environ["REPLICATE_API_TOKEN"] = api_key
    except:
        return None, "ERRO: A Chave da IA não foi configurada nos 'Secrets' do App."

    # Prepara a imagem
    input_bytes = image_file.getvalue()
    
    # Modelo de IA (Stable Diffusion Inpainting ou similar)
    MODEL_ID = "stability-ai/stable-diffusion:27f2754605151523457a4199c72e2d9369d120a10c9c37562143b81109968847"

    try:
        # Chama a API da Replicate
        output = replicate.run(
            MODEL_ID,
            input={
                "image": input_bytes,
                "prompt": f"Close-up of a human smile, apply highly realistic, perfect porcelain veneers, natural tone {tom}. Keeping original mouth shape.",
                "negative_prompt": "low quality, cartoon, unnatural lighting, fake texture, blurry, artifacts, deformed teeth"
            }
        )
        
        # Baixa a imagem gerada
        if output and isinstance(output, list) and output[0]:
            response = requests.get(output[0])
            img_tratada = Image.open(BytesIO(response.content))
            return img_tratada, "Sucesso: Simulação Gerada pela IA!"
        
        return None, "A IA não conseguiu gerar a imagem."

    except Exception as e:
        return None, f"Erro na API: {e}"

# --- BARRA LATERAL (MENU) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=50)
    st.title("IBR Clinic")
    menu = st.radio("Navegação", ["Simulador (Paciente)", "Dashboard (Dr. Igor)"])
    st.markdown("---")
    st.caption("Status: 🟢 Online")

# --- TELA 1: SIMULADOR (VISÃO DO PACIENTE) ---
if menu == "Simulador (Paciente)":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Seu Novo Sorriso")
        st.write("Faça o upload da sua foto para visualizar suas lentes de contato.")
        
        uploaded_file = st.file_uploader("Escolha uma foto (Rosto de frente)", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("### Personalização")
        tom_lente = st.select_slider("Selecione a Tonalidade", options=["BL1 (Extra Branco)", "BL2 (Branco Natural)", "BL3 (Natural)", "BL4 (Sutil)"])
        
        if uploaded_file is not None:
            if st.button("✨ Gerar Simulação"):
                with st.spinner('A Inteligência Artificial está desenhando seu sorriso...'):
                    resultado, msg = transformar_sorriso(uploaded_file, tom_lente)
                    
                    if resultado:
                        st.session_state['resultado_atual'] = resultado
                        st.session_state['foto_original'] = Image.open(uploaded_file)
                        st.success("Pronto!")
                    else:
                        st.error(msg)

    with col2:
        st.markdown("### Resultado")
        if 'resultado_atual' in st.session_state:
            col_a, col_b = st.columns(2)
            with col_a:
                st.image(st.session_state['foto_original'], caption="Antes", use_column_width=True)
            with col_b:
                st.image(st.session_state['resultado_atual'], caption=f"Simulação ({tom_lente})", use_column_width=True)
                
            st.info("Gostou? Clique abaixo para agendar.")
            st.button("📅 Agendar Avaliação")
        else:
            st.info("Aguardando upload da foto...")

# --- TELA 2: DASHBOARD (VISÃO DO DENTISTA) ---
elif menu == "Dashboard (Dr. Igor)":
    st.title("Painel Administrativo")
    st.write("Aqui ficarão salvas as simulações dos pacientes.")
    # (Código simplificado para focar no erro)
