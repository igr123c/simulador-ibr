import streamlit as st
from PIL import Image, ImageOps
from io import BytesIO
import os
import json
import requests
# Importações do Google Cloud
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

# --- FUNÇÃO DE AUTENTICAÇÃO ROBUSTA (Correção Final) ---

def autenticar_google():
    """Lê a chave JSON dos Segredos, salva temporariamente e autentica o Google Cloud."""
    if "GCP_SA_KEY" not in st.secrets:
        st.error("ERRO: Chave do Google Cloud (GCP_SA_KEY) não configurada nos Secrets.")
        return None

    try:
        # 1. Carrega o JSON da string multi-linha nos Secrets
        sa_key_json_string = st.secrets["GCP_SA_KEY"]
        credentials_dict = json.loads(sa_key_json_string)
        project_id = credentials_dict.get('project_id')
        
        # 2. ESCREVER O ARQUIVO JSON TEMPORARIAMENTE NO SERVIDOR
        # Isso corrige o ImportError ao fornecer o arquivo JSON de credenciais
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
        # Se houver um erro, apaga o arquivo temporário para evitar lixo.
        if os.path.exists(temp_file_name):
            os.remove(temp_file_name)
        st.error(f"ERRO DE AUTENTICAÇÃO: Falha ao inicializar o Google Cloud com o JSON. Det
