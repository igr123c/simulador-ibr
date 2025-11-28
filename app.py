import streamlit as st
import replicate
import requests
from PIL import Image
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

# --- FUNÇÃO MÁGICA DE IA (Atualizada para SDXL) ---
def transformar_sorriso(image_file, tom):
    # 1. Autenticação
    try:
        # Tenta pegar dos segredos
        if "REPLICATE_API_TOKEN" in st.secrets:
             os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]
        # Se não tiver, tenta pegar do ambiente direto (caso tenha salvo antes)
    except:
        pass
    
    if not os.environ.get("REPLICATE_API_TOKEN"):
        return None, "ERRO: Chave da API não encontrada. Vá em Settings > Secrets."

    # 2. Prepara a imagem
    input_bytes = image_file.getvalue()
    arquivo_formatado = BytesIO(input_bytes)
    
    # 3. MODELO NOVO (SDXL - Alta Definição)
    # Este é o modelo mais moderno e estável atualmente
    MODEL_ID = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

    try:
        output = replicate.run(
            MODEL_ID,
            input={
                "image": arquivo_formatado,
                # Prompt Refinado para Estética Dental
                "prompt": f"Professional dental photography close-up, cosmetic dentistry, perfect {tom} porcelain veneers, natural teeth texture, highly detailed, 8k resolution, cinematic lighting, realistic mouth structure.",
                "negative_prompt": "cartoon, illustration, painting, drawing, fake, blur, ugly, deformed, cavity, metal, yellow teeth, missing teeth, extra fingers",
                "prompt_strength": 0.75, # Equilíbrio entre a foto original e a edição
                "mask_blur": 0
            }
        )
        
        if output and isinstance(output, list) and output[0]:
            response = requests.get(output[0])
            img_tratada = Image.open(BytesIO(response.content))
            return img_tratada, "Sucesso!"
        
        return None, "A IA processou mas não retornou imagem válida."

    except Exception as e:
        return None, f"Erro Técnico: {e}"

# --- INTERFACE ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=50)
    st.title("IBR Clinic")
    menu = st.radio("Navegação", ["Simulador (Paciente)", "Dashboard (Dr. Igor)"])
    st.markdown("---")
    st.caption("Motor IA: Stable Diffusion XL")

if menu == "Simulador (Paciente)":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Simulação Estética")
        st.write("Faça upload de uma foto frontal do sorriso.")
        uploaded_file = st.file_uploader("Arquivo de Imagem", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("### Planejamento")
        tom_lente = st.select_slider("Cor Desejada", options=["BL1 (Branco Absoluto)", "BL2 (Branco Natural)", "BL3 (Natural)", "BL4 (Sutil)"])
        
        if uploaded_file:
            if st.button("✨ Gerar Sorriso Novo"):
                with st.spinner('Processando imagem em Alta Definição (Isso leva uns 10s)...'):
                    resultado, msg = transformar_sorriso(uploaded_file, tom_lente)
                    if resultado:
                        st.session_state['res'] = resultado
                        st.session_state['org'] = Image.open(uploaded_file)
                        st.success("Concluído!")
                    else:
                        st.error(msg)

    with col2:
        if 'res' in st.session_state:
            st.image(st.session_state['res'], caption="Resultado da Simulação", use_column_width=True)
            with st.expander("Ver Foto Original"):
                st.image(st.session_state['org'], use_column_width=True)
        else:
            st.info("O resultado aparecerá aqui.")

elif menu == "Dashboard (Dr. Igor)":
    st.title("Painel Administrativo")
    st.info("Área restrita.")
