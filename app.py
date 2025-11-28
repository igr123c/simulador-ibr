import streamlit as st
import replicate
import requests
from PIL import Image, ImageOps # Adicionado ImageOps para corrigir rotação
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

# --- FUNÇÃO MÁGICA DE IA (InstructPix2Pix) ---
def transformar_sorriso(image_file, tom):
    # 1. Autenticação
    try:
        if "REPLICATE_API_TOKEN" in st.secrets:
             os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]
    except:
        pass
    
    if not os.environ.get("REPLICATE_API_TOKEN"):
        return None, "ERRO: Chave da API não encontrada."

    # 2. PREPARAÇÃO DA IMAGEM (Anti-Rotação e Redimensionamento)
    img = Image.open(image_file)
    
    # --- CORREÇÃO DE ROTAÇÃO (O segredo para iPhone/Android) ---
    try:
        img = ImageOps.exif_transpose(img)
    except:
        pass # Se não tiver dados de rotação, segue normal

    # Redimensiona para HD (evita travar a memória, mas mantém qualidade)
    img.thumbnail((1024, 1024))
    
    # Salva em memória
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    arquivo_formatado = BytesIO(buffer.getvalue())
    
    # 3. NOVO MODELO: InstructPix2Pix (O Editor)
    # Esse modelo não recria a pessoa, ele EDITA a foto existente.
    MODEL_ID = "timothybrooks/instruct-pix2pix:30c1d0b916a6f8efce20493f5d61ee27491ab2a60437c13c588468b9810ec23f"

    # Define a intensidade do branco baseada na escolha
    desc_cor = "white"
    if "BL1" in tom: desc_cor = "extremely white bright"
    elif "BL2" in tom: desc_cor = "natural white"
    elif "BL4" in tom: desc_cor = "natural yellowish"

    try:
        output = replicate.run(
            MODEL_ID,
            input={
                "image": arquivo_formatado,
                # A ORDEM DIRETA PARA A IA:
                "prompt": f"make the teeth look like perfect {desc_cor} porcelain veneers, dental photography",
                # O quanto a IA pode "viajar" (Image Guidance). 
                # Alto = Fica igual a original. Baixo = Muda muito.
                "image_guidance_scale": 1.5, 
                "num_inference_steps": 20
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
    st.caption("Motor: InstructPix2Pix (Edição)")

if menu == "Simulador (Paciente)":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Simulação Estética")
        st.write("Faça upload de uma foto do sorriso.")
        uploaded_file = st.file_uploader("Arquivo de Imagem", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("### Planejamento")
        tom_lente = st.select_slider("Cor da Lente", options=["BL1 (Branco Absoluto)", "BL2 (Branco Natural)", "BL3 (Natural)", "BL4 (Sutil)"])
        
        if uploaded_file:
            if st.button("✨ Gerar Sorriso Novo"):
                with st.spinner('Aplicando lentes digitais (Mantendo o rosto original)...'):
                    resultado, msg = transformar_sorriso(uploaded_file, tom_lente)
                    if resultado:
                        st.session_state['res'] = resultado
                        st.session_state['org'] = Image.open(uploaded_file)
                        # Aplica a rotação na visualização do original também
                        st.session_state['org'] = ImageOps.exif_transpose(st.session_state['org'])
                        st.success("Concluído!")
                    else:
                        st.error(msg)

    with col2:
        if 'res' in st.session_state:
            st.markdown("### Resultado")
            # Slider de Comparação (Streamlit Componente Nativo)
            st.image(st.session_state['res'], caption="Simulação", use_column_width=True)
            with st.expander("Ver Original"):
                st.image(st.session_state['org'], use_column_width=True)
        else:
            st.info("O resultado aparecerá aqui.")

elif menu == "Dashboard (Dr. Igor)":
    st.title("Painel Administrativo")
    st.info("Área restrita.")
