Para exportar o banco de dados no PostgreSQL 18 (ou versões anteriores), a ferramenta padrão é o **`pg_dump`**.

Aqui estão os comandos para os cenários mais comuns:

### 1. Se o PostgreSQL está instalado no seu Computador (Local)

Abra o terminal e execute:

```bash
pg_dump -U seu_usuario -h localhost -p 5432 nome_do_banco > backup_sofia.sql

```

* **`-U seu_usuario`**: O usuário do banco (ex: `postgres`).
* **`-h localhost`**: O host (endereço).
* **`-p 5432`**: A porta (padrão é 5432).
* **`nome_do_banco`**: O nome do database que você quer exportar.
* **`> backup_sofia.sql`**: O arquivo de saída.

---

### 2. Se o PostgreSQL está rodando no Docker (Muito Provável)

Como você mencionou o uso de containers anteriormente, este é provavelmente o comando que você precisa. Execute isso no terminal da sua máquina (fora do container):

```bash
docker exec -t nome_do_container_postgres pg_dump -U usuario_db nome_do_banco > backup_sofia.sql

```

*Exemplo prático:*

```bash
docker exec -t sofia_postgres pg_dump -U postgres sofia_education > backup_completo.sql

```

---

### 3. Variações Úteis

**Apenas a Estrutura (Schema) - Sem dados:**
Útil para versionar o banco ou criar ambientes de dev limpos.

```bash
pg_dump -U usuario -s nome_do_banco > schema.sql

```

**Apenas os Dados (Data Only) - Sem estrutura:**
Útil para popular um banco que já tem as tabelas criadas.

```bash
pg_dump -U usuario -a nome_do_banco > dados.sql

```

**Formato Customizado (Comprimido):**
Melhor para bancos grandes. Para restaurar, você precisará usar o `pg_restore` em vez de apenas ler o arquivo SQL.

```bash
pg_dump -U usuario -F c nome_do_banco > backup.dump

```

### Dica sobre Senha

Se ele pedir senha toda vez e você quiser automatizar, você pode definir a variável de ambiente antes do comando (Linux/Mac):

```bash
PGPASSWORD='sua_senha' pg_dump -U usuario -h localhost nome_do_banco > backup.sql

```