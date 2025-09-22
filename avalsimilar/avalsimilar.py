from flask import Flask, request, jsonify
from collections import defaultdict
import psycopg2
import unicodedata
from transformers import pipeline
import traceback

# --------------------------------------------------------------------------
# 🔧 Configurações iniciais
# --------------------------------------------------------------------------

app = Flask(__name__)
DEBUG_MODE = False  # Ativa logs detalhados e testes de conexão

# Define credenciais de acesso ao banco com base no ambiente
if DEBUG_MODE:
    DB_CONFIG = {
        "dbname": "embeddings",
        "user": "devuser",
        "host": "127.0.0.1"
    }
else:
    DB_CONFIG = {
        "dbname": "embeddings",
        "user": "n8n",
        "password": "n8npass",
        "host": "postgre",
        "port": "5432"
    }

# Carregamento do modelo de sumarização
if DEBUG_MODE:
    print("🔍 Carregando modelo de sumarização...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# --------------------------------------------------------------------------
# 🛡️ Função de limpeza de texto com blindagem máxima
# --------------------------------------------------------------------------

def limpar_texto(texto):
    try:
        if isinstance(texto, str):
            texto = unicodedata.normalize("NFKC", texto)
            texto = texto.replace("\x00", "")
            return texto

        texto = texto.decode("utf-8")
        texto = unicodedata.normalize("NFKC", texto)
        return texto

    except UnicodeDecodeError:
        try:
            texto = texto.decode("latin1")
            texto = unicodedata.normalize("NFKC", texto)
            return texto
        except Exception:
            pass

    except Exception:
        pass

    texto_str = str(texto)
    texto_str = texto_str.encode("latin1", errors="replace").decode("utf-8", errors="replace")
    texto_str = unicodedata.normalize("NFKC", texto_str)
    texto_str = texto_str.replace("\x00", "")
    return texto_str[:300] + "..."

# --------------------------------------------------------------------------
# 🔍 Teste de conexão com o banco de dados
# --------------------------------------------------------------------------

def testar_conexao():
    print("🔍 Testando conexão com o banco PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        versao = cur.fetchone()
        cur.close()
        conn.close()
        print(f"✅ Conexão bem-sucedida! Versão do PostgreSQL: {versao[0]}")
    except Exception as e:
        print("❌ Erro ao conectar:")
        try:
            print(repr(e))
        except Exception:
            traceback.print_exc()

# --------------------------------------------------------------------------
# 📝 Função de sumarização de texto
# --------------------------------------------------------------------------

def resumir_texto_nlp(texto, max_length=130, min_length=30):
    if DEBUG_MODE:
        print(f"📝 Resumindo trecho com {len(texto)} caracteres...")
    try:
        resumo = summarizer(texto, max_length=max_length, min_length=min_length, do_sample=False)
        return resumo[0]['summary_text']
    except Exception as e:
        print(f"⚠️ Erro ao resumir trecho: {e}")
        return texto[:300] + "..."

# --------------------------------------------------------------------------
# 🔍 Busca por projetos similares com base em embeddings
# --------------------------------------------------------------------------

def buscar_similares_por_projeto(embedding_input, limite_distancia=0.5):
    try:
        embedding_str = "[" + ",".join(str(x) for x in embedding_input) + "]"

        conn = psycopg2.connect(**DB_CONFIG)
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
            texto_limpo = limpar_texto(texto)
            resumo = resumir_texto_nlp(texto_limpo)
            agrupados[file_name].append({
                "trecho_resumido": resumo,
                "distancia": float(distancia)
            })

        projetos_similares = []
        for file_name, trechos in agrupados.items():
            distancias = [t["distancia"] for t in trechos]
            sugestao = gerar_sugestao(file_name, distancias)
            projetos_similares.append({
                "projeto_similar": file_name,
                "quantidade_chunks_similares": len(trechos),
                "media_distancia": round(sum(distancias) / len(distancias), 4),
                "menor_distancia": round(min(distancias), 4),
                "trechos_relevantes": trechos[:3],
                "sugestao_reuso": sugestao
            })

        projetos_similares.sort(key=lambda x: x["media_distancia"])
        return projetos_similares

    except Exception:
        print("❌ Erro ao buscar similares:")
        traceback.print_exc()
        return []

# --------------------------------------------------------------------------
# 💡 Geração de sugestão de reuso com base nas distâncias
# --------------------------------------------------------------------------

def gerar_sugestao(file_name, distancias):
    if min(distancias) < 0.3:
        return f"O projeto '{file_name}' possui alta similaridade. Avalie reutilizar estruturas, escopo ou lógica técnica."
    elif len(distancias) > 5:
        return f"O projeto '{file_name}' tem vários trechos relevantes. Pode servir como base de referência."
    else:
        return f"O projeto '{file_name}' tem similaridade moderada. Verifique se há pontos específicos que podem ser aproveitados."

# --------------------------------------------------------------------------
# 🚩 Rota principal da API
# --------------------------------------------------------------------------

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

# --------------------------------------------------------------------------
# 🚀 Inicialização do servidor Flask
# --------------------------------------------------------------------------

if __name__ == "__main__":
    if DEBUG_MODE:
        testar_conexao()
        print("🚀 Servidor Flask iniciado em modo debug.")
    app.run(host="0.0.0.0", port=5000, debug=True)