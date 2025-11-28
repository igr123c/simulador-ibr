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

# --- FUNÇÃO MÁGICA DE IA ---
def transformar_sorriso(image_file, tom):
    # 1. Autenticação Segura
    try:
        if "REPLICATE_API_TOKEN" in st.secrets:
             os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]
    except:
        pass
    
    if not os.environ.get("REPLICATE_API_TOKEN"):
        return None, "ERRO: Chave da API não encontrada. Vá em Settings > Secrets."

    # 2. PREPARAÇÃO DA IMAGEM (A Mágica Anti-Erro)
    # Abre a imagem original
    img = Image.open(image_file)
    
    # REDIMENSIONA para no máximo 1024px (Isso evita o erro de Memória/CUDA)
    # Mantém a proporção correta, só diminui se for gigante
    img.thumbnail((1024, 1024)) 
    
    # Converte de volta para bytes para enviar para a IA
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    arquivo_formatado = BytesIO(buffer.getvalue())
    
    # 3. MODELO SDXL (O Melhor para Realismo)
    MODEL_ID = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

    try:
        output = replicate.run(
            MODEL_ID,
            input={
                "image": arquivo_formatado,
                "prompt": f"Close-up photo of a smile, dentistry, fitting perfect {tom} porcelain veneers on teeth. Highly detailed texture, professional dental photography, natural lighting, 8k.",
                "negative_prompt": "cavities, yellow teeth, metal braces, rotten teeth, cartoon, drawing, illustration, blur, low quality, distorted",
                "prompt_strength": 0.65, # Ajuste fino para manter a identidade do paciente
                "num_inference_steps": 30
            }
        )
        
        if output and isinstance(output, list) and output[0]:
            response = requests.get(output[0])
            img_tratada = Image.open(BytesIO(response.content))
            return img_tratada, "Sucesso!"
        
        return None, "A IA processou mas não retornou imagem válida."

    except Exception as e:
        return None, f"Erro Técnico na IA: {e}"

# --- INTERFACE DO APP ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3004/3004458.png", width=50)
    st.title("IBR Clinic")
    menu = st.radio("Navegação", ["Simulador (Paciente)", "Dashboard (Dr. Igor)"])
    st.markdown("---")
    st.caption("Motor: SDXL High-Res")

if menu == "Simulador (Paciente)":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Simulação Estética")
        st.write("Faça upload de uma foto frontal do sorriso.")
        
        # Aceita JPG e PNG
        uploaded_file = st.file_uploader("Arquivo de Imagem", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("### Planejamento")
        tom_lente = st.select_slider("Cor da Lente", options=["BL1 (Branco Absoluto)", "BL2 (Branco Natural)", "BL3 (Natural)", "BL4 (Sutil)"])
        
        if uploaded_file:
            if st.button("✨ Gerar Sorriso Novo"):
                with st.spinner('Processando... (Isso leva uns 15 segundos)'):
                    resultado, msg = transformar_sorriso(uploaded_file, tom_lente)
                    if resultado:
                        st.session_state['res'] = resultado
                        st.session_state['org'] = Image.open(uploaded_file) # Salva original para comparar
                        st.success("Concluído!")
                    else:
                        st.error(msg)

    with col2:
        if 'res' in st.session_state:
            st.markdown("### Resultado da Simulação")
            st.image(st.session_state['res'], use_column_width=True)
            
            with st.expander("Comparar com Original"):
                st.image(st.session_state['org'], caption="Foto Original", use_column_width=True)
                
            st.button("📲 Enviar para WhatsApp da Clínica")
        else:
            st.info("O resultado aparecerá aqui.")

elif menu == "Dashboard (Dr. Igor)":
    st.title("Painel Administrativo")
    st.info("Área restrita.")
