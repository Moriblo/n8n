from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import os

app = Flask(__name__)

# Carrega o modelo local
model_path = os.path.join(os.path.dirname(__file__), "modelo")
model = SentenceTransformer(model_path)

# Função de chunking simples com sobreposição
def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# Rota para gerar embeddings
@app.route("/embed", methods=["POST"])
def embed_text():
    print("📦 request.data:", request.data)  # Diagnóstico bruto
    data = request.get_json()
    print("📥 Dados recebidos:", data)       # Diagnóstico interpretado

    text = data.get("file_data", "")
    file_name = data.get("file_name", "arquivo_sem_nome.txt")
    
    if not text.strip():
        return jsonify({"error": "Texto vazio"}), 400

    chunks = chunk_text(text)
    embeddings = model.encode(chunks, convert_to_numpy=True)
    embeddings_list = [emb.tolist() for emb in embeddings]

    return jsonify({
        "file_name": file_name,
        "chunks": chunks,
        "embeddings": embeddings_list
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)