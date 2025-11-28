# Adicione estes imports no topo do seu arquivo, junto com os outros:
import os
import replicate

# ... (restante dos imports) ...

# --- FUNÇÃO MÁGICA DE IA (Replicate) ---
@st.cache_data(show_spinner=False)
def transformar_sorriso(image_file, tom):
    """
    Função atualizada para usar a API real do Replicate (IA Generativa).
    """
    
    # 1. OBTER CHAVE SECRETA DE FORMA SEGURA
    # st.secrets lê automaticamente o arquivo secrets.toml
    try:
        api_key = st.secrets["REPLICATE_API_TOKEN"]
        os.environ["REPLICATE_API_TOKEN"] = api_key # Configura a chave no ambiente
    except KeyError:
        return None, "ERRO DE CHAVE: API Key não configurada no secrets.toml."

    # 2. PREPARAR INPUT
    # Converte o arquivo de upload para um URL ou bytes, dependendo da API
    input_bytes = image_file.getvalue()
    
    # O MODELO da IA (Exemplo de um modelo poderoso que faz Inpainting/Restauração)
    # ATENÇÃO: Se for usar um modelo EXCLUSIVO para dentes, substitua este ID
    MODEL_ID = "stability-ai/stable-diffusion:27f2754605151523457a4199c72e2d9369d120a10c9c37562143b81109968847"

    st.info(f"⏳ IA Ativada! Enviando foto para processamento: {tom}...")
    
    try:
        # --- CHAMADA REAL À API ---
        with st.spinner(f"Processando imagem com IA Generativa... Tom: {tom}"):
            output = replicate.run(
                MODEL_ID,
                input={
                    "image": input_bytes,
                    "prompt": f"Close-up of a human smile, apply highly realistic, perfect porcelain veneers, natural tone {tom}. Keeping original mouth shape.",
                    "negative_prompt": "low quality, cartoon, unnatural lighting, fake texture, blurry, artifacts"
                }
            )
            
            # O output geralmente é uma lista de URLs. Pegamos a primeira
            if output and isinstance(output, list) and output[0]:
                response = requests.get(output[0])
                img_tratada = Image.open(BytesIO(response.content))
                return img_tratada, "Sucesso: Simulação Gerada pela IA!"
            
            return None, "A IA não conseguiu gerar a imagem. Verifique o modelo e a foto."

    except Exception as e:
        st.error(f"❌ Erro na comunicação com a API (Replicate): {e}")
        return None, "Erro na API da IA"
