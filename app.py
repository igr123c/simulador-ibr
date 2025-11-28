import streamlit as st
import replicate
import requests
from PIL import Image, ImageOps
from io import BytesIO
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IBR Clinic System", layout="wide", page_icon="🦷")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    h1 { color: #1e3a8a; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #2563eb; color: white; }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO MÁGICA DE IA (Stable Diffusion XL - Edição Otimizada) ---
# Usamos esta, pois a complexidade do Google Cloud é inviável neste ambiente
def transformar_sorriso_replicate(image_file, tom):
    
    # 1. AUTENTICAÇÃO
    if "REPLICATE_API_TOKEN" not in st.secrets:
        return None, "ERRO: Chave da Replicate não encontrada nos Secrets."
    
    os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]

    # 2. PREPARAÇÃO DA IMAGEM (Anti-Rotação e Redimensionamento)
    img = Image.open(image_file)
    try:
        img = ImageOps.exif_transpose(img)
    except:
        pass
    img.thumbnail((1024, 1024))
    
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    arquivo_formatado = BytesIO(buffer.getvalue())
    
    # 3. MODELO SDXL (Otimizado para manter o rosto)
    # Usando o SDXL Inpainting para uma edição mais focada
    MODEL_ID = "stability-ai/stable-diffusion-xl-1.0-inpainting:d54109e25d4be489e2467d0200871d36d4cf39e74d5389813a079237072f6a91"

    edit_prompt = f"Macro dental photography, perfect {tom} porcelain veneers, healthy pink gums, glossy finish, realistic teeth texture."
    
    try:
        output = replicate.run(
            MODEL_ID,
            input={
                "image": arquivo_formatado,
                "prompt": edit_prompt,
                "negative_prompt": "ugly, deformed, unrealistic, cartoon, artifacts, metal, braces",
                "prompt_strength": 0.8 # Alta força para garantir o resultado
            }
        )
        
        if output and isinstance(output, list) and output[0]:
            response = requests.get(output[0])
            img_tratada = Image.open(BytesIO(response.content))
            return img_tratada, "Sucesso: Edição Replicate SDXL!"
        
        return None, "A IA não retornou imagem válida."

    except Exception as e:
        return None, f"Erro na API da Replicate: {e}"

# --- INTERFACE DO APP ---
with st.sidebar:
    st.title("IBR Clinic")
    if "REPLICATE_API_TOKEN" in st.secrets:
        st.success("Motor Replicate OK")
    else:
        st.error("Chave Replicate Ausente.")
    menu = st.radio("Navegação", ["Simulador (Paciente)", "Dashboard (Dr. Igor)"])
    st.markdown("---")
    st.caption("Motor IA: SDXL Inpainting (Estável)")

if menu == "Simulador (Paciente)":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Simulação Estética")
        st.write("Faça upload de uma foto frontal do sorriso.")
        uploaded_file = st.file_uploader("Arquivo de Imagem", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("### Planejamento")
        tom_lente = st.select_slider("Cor da Lente", options=["BL1 (Branco Absoluto)", "BL2 (Branco Natural)", "BL3 (Natural)", "BL4 (Sutil)"])
        
        if uploaded_file:
            if st.button("✨ Gerar Sorriso Novo"):
                with st.spinner('Processando...'):
                    # Tenta rodar a função com a chave da Replicate
                    resultado, msg = transformar_sorriso_replicate(uploaded_file, tom_lente)
                    if resultado:
                        st.session_state['res'] = resultado
                        st.session_state['org'] = ImageOps.exif_transpose(Image.open(uploaded_file))
                        st.success("Concluído!")
                    else:
                        st.error(msg)
    # ... (Restante da Interface) ...
