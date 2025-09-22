import psycopg2

conn = psycopg2.connect(
    dbname="embeddings",
    user="devuser",
    host="127.0.0.1",
    port="5432"
)
print("✅ Conectado com sucesso!")
conn.close()