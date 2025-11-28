import streamlit as st
from PIL import Image, ImageOps
from io import BytesIO
import os
import json
import requests
# --- CORREÇÃO FINAL: IMPORTAÇÕES ROBUSTAS DO GOOGLE CLOUD ---
from google.cloud import aiplatform
# Importa o serviço de predição, que é o que fará a chamada direta à IA
from google.cloud.aiplatform.services import PredictionServiceClient
from google.cloud.aiplatform_v1.types.predict_service import PredictRequest

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

# --- FUNÇÃO DE AUTENTICAÇÃO E INICIALIZAÇÃO ---

def autenticar_google():
    temp_file_name = None 
    if "GCP_SA_KEY" not in st.secrets:
        st.error("ERRO: Chave do Google Cloud (GCP_SA_KEY) não configurada nos Secrets.")
        return None

    try:
        sa_key_json_string = st.secrets["GCP_SA_KEY"]
        credentials_dict = json.loads(sa_key_json_string)
        project_id = credentials_dict.get('project_id')
        
        # 1. Escreve o JSON temporário
        temp_file_name = f"gcp_credentials_{project_id}.json"
        with open(temp_file_name, "w") as f:
            f.write(sa_key_json_string)
        
        # 2. Seta a variável de ambiente
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_name

        # 3. Inicializa o Vertex AI (agora deve funcionar)
        aiplatform.init(
            project=project_id, 
            location="us-central1"
        )
        return project_id
    except Exception as e:
        if temp_file_name is not None and os.path.exists(temp_file_name):
            os.remove(temp_file_name)
        st.error(f"ERRO DE AUTENTICAÇÃO: Falha ao inicializar o Google Cloud com o JSON. Detalhe: {e}")
        return None

# --- FUNÇÃO PRINCIPAL: EDIÇÃO IMAGEN (GOOGLE) ---

def transformar_sorriso_imagen(image_file, tom):
    """Executa a chamada ao modelo Imagen no Vertex AI usando PredictionServiceClient."""
    
    # ... (Preparações da Imagem) ...
    img = Image.open(image_file)
    try:
        img = ImageOps.exif_transpose(img)
    except:
        pass
    img.thumbnail((1024, 1024))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    img_bytes = buffer.getvalue()
    
    # Codifica a imagem para Base64 (Obrigatório para a maioria das APIs REST/GAPIC)
    import base64
    encoded_image = base64.b64encode(img_bytes).decode('utf-8')
    
    # 2. PROMPT DE EDIÇÃO
    edit_prompt = f"Change the teeth to perfect {tom} porcelain veneers. Professional dental photography."

    # 3. CHAMADA À API (USANDO O CLIENTE GARANTIDO)
    try:
        # Parâmetros de Entrada para a API
        instance = {
            "prompt": edit_prompt,
            "image": {"image_bytes": encoded_image},
            "sample_count": 1,
            "edit_mode": "inpainting", # O MODO DE EDIÇÃO É POR AQUI
            "aspect_ratio": "1:1" # Para garantir estabilidade
        }

        # Cria a requisição de predição
        endpoint = f"projects/{st.session_state['project_id']}/locations/us-central1/endpoints/imagen-edit@002"
        
        # Inicializa o cliente de serviço
        client = PredictionServiceClient(client_options={"api_endpoint": "us-central1-aiplatform.googleapis.com"})
        
        # Cria a requisição (o corpo da chamada)
        request = PredictRequest(
            endpoint=endpoint,
            instances=[instance] # Envia o payload
        )

        # 4. EXECUTA A CHAMADA
        response = client.predict(request=request)
        
        if response.predictions:
            # A resposta contém a imagem em Base64
            img_base64_data = response.predictions[0]["image"]
            img_data = base64.b64decode(img_base64_data)
            img_tratada = Image.open(BytesIO(img_data))
            return img_tratada, "Sucesso: Editado pelo Google Imagen 3!"
        
        return None, "O Google Imagen não retornou uma imagem editada."

    except Exception as e:
        return None, f"Erro na API do Google Cloud: {e}"

# --- INTERFACE DO APP ---
with st.sidebar:
    st.title("IBR Clinic")
    project_id = autenticar_google()
    st.session_state['project_id'] = project_id # Salva o ID do projeto no estado
    if project_id:
        st.success(f"Motor Google OK ({project_id})")
    else:
        st.warning("Aguardando ativação do faturamento e JSON correto.")
    menu = st.radio("Navegação", ["Simulador (Paciente)", "Dashboard (Dr. Igor)"])
    st.markdown("---")
    st.caption("Motor IA: Google Imagen 3")

if menu == "Simulador (Paciente)":
    # ... (Restante da Interface) ...
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
