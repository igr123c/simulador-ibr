import streamlit as st
import replicate
import requests
from PIL import Image
from io import BytesIO
import os

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
def transformar_sorriso(image_file, tom):
    """
    Envia a foto para a IA (Replicate) e retorna o sorriso novo.
    """
    # 1. Validação da Chave
    try:
        api_key = st.secrets["REPLICATE_API_TOKEN"]
        os.environ["REPLICATE_API_TOKEN"] = api_key
    except:
        return None, "ERRO: A Chave da IA não foi configurada nos 'Secrets' do App."

    # 2. Prepara a imagem (CORREÇÃO AQUI: "Engarrafa" os bytes como arquivo)
    input_bytes = image_file.getvalue()
    arquivo_formatado = BytesIO(input_bytes)
    
    # Modelo de IA (Stable Diffusion - Edit/Inpainting)
    # Usando um modelo específico para edições realistas
    MODEL_ID = "stability-ai/stable-diffusion:27f2754605151523457a4199c72e2d9369d120a10c9c37562143b81109968847"

    try:
        output = replicate.run(
            MODEL_ID,
            input={
                "image": arquivo_formatado, # Agora enviamos o arquivo formatado
                "prompt": f"Close-up of a human smile, apply highly realistic, perfect porcelain veneers, natural tone {tom}. Keeping original mouth shape. High resolution, dental photography.",
                "negative_prompt": "low quality, cartoon, unnatural lighting, fake texture, blurry, artifacts, deformed teeth, missing teeth, extra teeth, metal braces",
                "prompt_strength": 0.8 # Força da IA (0 a 1)
            }
        )
        
        # Baixa a imagem gerada pela IA
        if output and isinstance(output, list) and output[0]:
            response = requests.get(output[0])
            img_tratada = Image.open(BytesIO(response.content))
            return img_tratada, "Sucesso!"
        
        return None, "A IA processou mas não retornou imagem válida."

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
                    # Passa o arquivo original para a função
                    resultado, msg = transformar_sorriso(uploaded_file, tom_lente)
                    
                    if resultado:
                        st.session_state['resultado_atual'] = resultado
                        st.session_state['foto_original'] = Image.open(uploaded_file)
                        st.success("Pronto!")
                    else:
                        st.error(msg)

    with col2:
        st.
