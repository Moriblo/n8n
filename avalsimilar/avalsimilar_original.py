from flask import Flask, request, jsonify
import psycopg2
from collections import defaultdict
from transformers import pipeline

app = Flask(__name__)

# Inicializa o modelo de sumarização da Hugging Face
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Função para resumir trechos longos usando NLP
def resumir_texto_nlp(texto, max_length=130, min_length=30):
    try:
        resumo = summarizer(texto, max_length=max_length, min_length=min_length, do_sample=False)
        return resumo[0]['summary_text']
    except Exception as e:
        print(f"⚠️ Erro ao resumir trecho: {e}")
        return texto[:300] + "..."  # fallback simples

# Função principal que busca projetos similares com base em um vetor de embedding
def buscar_similares_por_projeto(embedding_input, limite_distancia=0.5):
    try:
        embedding_str = "[" + ",".join(str(x) for x in embedding_input) + "]"

        conn = psycopg2.connect(
            dbname="embeddings",
            user="n8n",
            password="n8npass",
            host="postgres",
            port="5432"
        )
        cur = conn.cursor()

        cur.execute("SET ivfflat.probes = 10;")

        cur.execute("""
            SELECT file_name, original_text, embedding <=> %s AS distancia
            FROM embeddings
            WHERE embedding <=> %s < %s
            ORDER BY distancia ASC;
        """, (embedding_str, embedding_str, limite_distancia))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        agrupados = defaultdict(list)
        for file_name, texto, distancia in rows:
            resumo = resumir_texto_nlp(texto)
            agrupados[file_name].append({
                "trecho_resumido": resumo,
                "distancia": float(distancia)
            })

        projetos_similares = []
        for file_name, trechos in agrupados.items():
            distancias = [t["distancia"] for t in trechos]
            projetos_similares.append({
                "projeto_similar": file_name,
                "quantidade_chunks_similares": len(trechos),
                "media_distancia": round(sum(distancias) / len(distancias), 4),
                "menor_distancia": round(min(distancias), 4),
                "trechos_relevantes": trechos[:3],
                "sugestao_reuso": gerar_sugestao(file_name, distancias)
            })

        projetos_similares.sort(key=lambda x: x["media_distancia"])
        return projetos_similares

    except Exception as e:
        print(f"❌ Erro ao buscar similares: {e}")
        return []

def gerar_sugestao(file_name, distancias):
    if min(distancias) < 0.3:
        return f"O projeto '{file_name}' possui alta similaridade. Avalie reutilizar estruturas, escopo ou lógica técnica."
    elif len(distancias) > 5:
        return f"O projeto '{file_name}' tem vários trechos relevantes. Pode servir como base de referência."
    else:
        return f"O projeto '{file_name}' tem similaridade moderada. Verifique se há pontos específicos que podem ser aproveitados."

@app.route("/avalsimilar", methods=["POST"])
def avaliar():
    dados = request.get_json(force=True)
    nome_arquivo = dados.get("nome_arquivo")
    embedding = dados.get("embedding")

    if not nome_arquivo or not isinstance(embedding, list):
        return jsonify({"error": "Campos 'nome_arquivo' e 'embedding' são obrigatórios"}), 400

    projetos_similares = buscar_similares_por_projeto(embedding)

    return jsonify({
        "nome_projeto_consultado": nome_arquivo,
        "projetos_similares": projetos_similares
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)