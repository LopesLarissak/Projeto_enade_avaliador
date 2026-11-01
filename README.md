# Projeto ENADE avaliador

Pipeline de ingestão, mensageria, indexação e busca de questões do ENADE.

## Stack
- Python 3.11, FastAPI, PyMuPDF, Pydantic
- Kafka (KRaft), Elasticsearch 8, Redis
- React + Vite
- Docker Compose
- OpenLDAP (base de autenticação) e MIT Kerberos (perfil de infraestrutura)

> Esta é uma base executável para desenvolvimento. LDAP e Kerberos estão provisionados como serviços de laboratório, mas a autenticação Kerberos SASL/GSSAPI ponta a ponta exige emissão de principals/keytabs e configuração TLS/JAAS compatível com as imagens escolhidas. Não considere RF22/RF23 concluídos antes dos testes de integração descritos abaixo.

## Subir no Codespaces
1. Crie um repositório GitHub vazio e abra-o em Codespaces.
2. Copie os arquivos desta estrutura para a raiz.
3. Execute:
   ```bash
   cp .env.example .env
   docker compose up -d --build
   ```
4. Acompanhe: `docker compose ps` e `docker compose logs -f api worker`.
5. API: http://localhost:8000/docs
6. Frontend: http://localhost:5173
7. Elasticsearch: http://localhost:9200
8. OpenLDAP: localhost:389 (admin / senha definida no `.env`).

## Ingerir PDFs
Coloque os PDFs em `data/pdfs/` e execute:
```bash
docker compose exec api python -m app.ingestion.cli --input /app/data/pdfs
```
O produtor publica questões no tópico `enade.questions`; o worker indexa no Elasticsearch. PDFs não são apagados.

## Endpoints principais
- `GET /health`
- `GET /questions?q=ética&area=...&course=...&year=...&kind=FG`
- `GET /questions/{id}`
- `GET /analytics/courses`
- `GET /analytics/competencies`
- `POST /cart/{session_id}` e `GET /cart/{session_id}`
- `POST /auth/login` (LDAP)

## Organização
- `app/ingestion`: extração, segmentação e produtor Kafka
- `app/worker`: consumidor Kafka, DLQ e Elasticsearch
- `app/api`: rotas, autenticação e cache
- `frontend`: interface React
- `infra`: configurações auxiliares

## Limitações deliberadas da primeira entrega
1. A segmentação automática por heurística precisa ser validada em PDFs reais; o formato das provas varia.
2. Fórmulas/imagens são preservadas como referência de página e sinalizadas para revisão. Conversão multimodal para LaTeX/Mermaid deve ser adicionada com avaliação humana; não há conversão fictícia.
3. `competencies` e `knowledge_objects` são metadados que precisam ser enriquecidos a partir das diretrizes/itens oficiais.
4. Para produção, configurar TLS, secrets manager, backup, replicação, ACLs Kafka/Elasticsearch e Kerberos SASL/GSSAPI real.
5. O compose é de laboratório/desenvolvimento, não uma implantação de produção.

## Testes
```bash
docker compose exec api pytest -q
```

## Decisões iniciais de topologia
Para laboratório local: 1 broker Kafka, 3 partições no tópico principal e 1 no DLQ; Elasticsearch com 1 shard primário e 0 réplicas; Redis standalone. Em produção, aumentar brokers/partições conforme vazão, shards conforme volume e réplicas conforme disponibilidade. Em nó único, réplicas não aumentam tolerância à falha.

## GitHub
```bash
git init
git add .
git commit -m "feat: estrutura inicial do pipeline ENADE"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```
