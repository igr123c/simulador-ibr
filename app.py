import streamlit as st
from PIL import Image, ImageOps
from io import BytesIO
import os
import json
import requests
from google.cloud import aiplatform 

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

# --- FUNÇÃO DE AUTENTICAÇÃO ROBUSTA (Com a Correção de Sequência) ---

def autenticar_google():
    # --- FIX: INICIALIZAÇÃO DA VARIÁVEL (Resolve o UnboundLocalError) ---
    temp_file_name = None 
    
    if "GCP_SA_KEY" not in st.secrets:
        st.error("ERRO: Chave do Google Cloud (GCP_SA_KEY) não configurada nos Secrets.")
        return None

    try:
        # 1. Carrega o JSON da string multi-linha nos Secrets
        sa_key_json_string = st.secrets["GCP_SA_KEY"]
        credentials_dict = json.loads(sa_key_json_string)
        project_id = credentials_dict.get('project_id')
        
        # 2. ESCREVER O ARQUIVO JSON TEMPORARIAMENTE NO SERVIDOR
        temp_file_name = f"gcp_credentials_{project_id}.json"
        
        with open(temp_file_name, "w") as f:
            f.write(sa_key_json_string)
        
        # 3. SETAR A VARIÁVEL DE AMBIENTE (Obrigatório para o Google)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_name

        # 4. Inicializa o Vertex AI
        aiplatform.init(
            project=project_id, 
            location="us-central1"
        )
        return project_id
    except Exception as e:
        # 5. GARANTIA DE LIMPEZA
        # Agora só tenta remover se a variável foi definida E se o arquivo existe
        if temp_file_name is not None and os.path.exists(temp_file_name):
            os.remove(temp_file_name)
        st.error(f"ERRO DE AUTENTICAÇÃO: Falha ao inicializar o Google Cloud com o JSON. Detalhe: {e}")
        return None

# --- FUNÇÃO PRINCIPAL: EDIÇÃO IMAGEN (GOOGLE) ---

def transformar_sorriso_imagen(image_file, tom):
    """Executa a chamada ao modelo Imagen no Vertex AI para edição de imagem."""
    
    # 1. PREPARAÇÃO DA IMAGEM (Anti-Rotação e Redimensionamento)
    img = Image.open(image_file)
    try:
        img = ImageOps.exif_transpose(img)
    except:
        pass
    img.thumbnail((1024, 1024))
    
    # Converte para bytes (base64) para enviar para a API
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    img_bytes = buffer.getvalue()
    
    # 2. PROMPT DE EDIÇÃO
    desc_cor = "natural white"
    if "BL1" in tom: desc_cor = "extremely white bright"
    elif "BL2" in tom: desc_cor = "natural white"
    elif "BL4" in tom: desc_cor = "warm natural white"

    edit_prompt = f"Change the teeth to perfect {desc_cor} porcelain veneers. The final image must be of professional dental photography quality. Keep the face and lips identical."

    # 3. CHAMADA À API (Google Imagen)
    try:
        model = aiplatform.ImageGenerationModel.from_pretrained('imagegeneration') 
        
        result = model.edit_image(
            prompt=edit_prompt,
            image_bytes=img_bytes,
            config=dict(
                number_of_images=1,
                person_generation="do not generate people" 
            )
        )

        if result.generated_images:
            img_data = result.generated_images[0].image.image_bytes
            img_tratada = Image.open(BytesIO(img_data))
            return img_tratada, "Sucesso: Editado pelo Google Imagen 3!"
        
        return None, "O Google Imagen não retornou uma imagem editada."

    except Exception as e:
        return None, f"Erro na API do Google Cloud: {e}"

# --- INTERFACE DO APP ---
with st.sidebar:
    st.title("IBR Clinic")
    project_id = autenticar_google()
    if project_id:
        st.success(f"Motor Google OK ({project_id})")
    else:
        st.warning("Aguardando ativação do faturamento e JSON correto.")
    menu = st.radio("Navegação", ["Simulador (Paciente)", "Dashboard (Dr. Igor)"])
    st.markdown("---")
    st.caption("Motor IA: Google Imagen 3")

if menu == "Simulador (Paciente)":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Simulação Estética")
        st.write("Faça upload de uma foto frontal do sorriso.")
        uploaded_file = st.file_uploader("Arquivo de Imagem", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("### Planejamento")
        tom_lente = st.select_slider("Cor da Lente", options=["BL1 (Branco Absoluto)", "BL2 (Branco Natural)", "BL3 (Natural)", "BL4 (Sutil)"])
        
        if uploaded_file and project_id:
            if st.button("✨ Gerar Sorriso Novo (IMAGEN 3)"):
                with st.spinner('Processando... (O Google Imagen está trabalhando...)'):
                    resultado, msg = transformar_sorriso_imagen(uploaded_file, tom_lente)
                    if resultado:
                        st.session_state['res'] = resultado
                        st.session_state['org'] = ImageOps.exif_transpose(Image.open(uploaded_file))
                        st.success("Concluído!")
                    else:
                        st.error(msg)
        elif uploaded_file and not project_id:
            st.error("Por favor, resolva o erro de autenticação do Google Cloud (Secrets).")

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
