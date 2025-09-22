## PostgreSQL com pgvector

Usamos a imagem `ankane/pgvector`, que sobrescreve o `pg_hba.conf` no primeiro boot.  
Para garantir persistência e controle de autenticação, usamos um `Dockerfile.postgres` que:

- Copia um `pg_hba.conf` customizado para `/etc/pg_hba.conf`
- Redefine o caminho no `postgresql.conf` via `hba_file = ...`

Isso garante que o banco aceite conexões sem senha após reinicialização.