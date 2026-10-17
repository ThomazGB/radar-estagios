# Guia de estudo do Radar de Estágios

Este guia explica o projeto na ordem em que os dados andam: **Gupy → Python → Postgres → API → React**. Leia com o código aberto ao lado. Em cada parte tem:

- 📍 **onde está** (arquivo);
- 🧠 **o conceito** por trás;
- 🎤 **como explicar em entrevista** (resposta curta, em voz alta);
- ✍️ **pra fixar**: uma mudança pequena para você fazer sozinho.

---

## 0. A visão geral (decore este parágrafo)

> "O Radar coleta vagas de estágio da API pública da Gupy com Python, limpa os dados com pandas (cidade, modalidade, tecnologias, bolsa), grava no PostgreSQL e expõe tudo numa API em FastAPI. O front em React consome essa API e mostra filtros, um kanban das minhas candidaturas e gráficos. O GitHub Actions roda os testes a cada push e coleta vagas novas todo dia."

Se você souber falar isso e desenhar o diagrama do README num papel, já está à frente de muito candidato.

---

## 1. O banco: `db/schema.sql` e `docker-compose.yml`

📍 `docker-compose.yml` sobe um Postgres dentro de um container. O `schema.sql` cria 3 tabelas:

```
empresas 1 ──── N vagas 1 ──── 0..1 candidaturas
```

🧠 **Conceitos**
- **PRIMARY KEY** (`id SERIAL PRIMARY KEY`): identifica cada linha de forma única. `SERIAL` faz o número subir sozinho.
- **FOREIGN KEY** (`empresa_id INTEGER REFERENCES empresas(id)`): a vaga *aponta* para a empresa. O banco recusa uma vaga com `empresa_id = 99` se a empresa 99 não existir. É isso que garante dados consistentes.
- Por que a vaga guarda `empresa_id`, e não a empresa guarda `vaga_id`? Porque uma empresa tem **várias** vagas. O lado "muitos" guarda a chave.
- **UNIQUE** em `vagas.gupy_id`: a mesma vaga da Gupy nunca entra duas vezes.
- **UNIQUE** em `candidaturas.vaga_id`: cada vaga aparece no máximo uma vez no kanban.
- **CHECK**: o status só pode ser um dos 4 valores do kanban.
- **ON DELETE CASCADE**: se a vaga for apagada, a candidatura dela vai junto.
- **Índice** (`CREATE INDEX`): funciona como o índice de um livro. Em vez de ler a tabela inteira, o Postgres pula direto para as linhas de `regiao = 'Barueri'`. Fica mais rápido de ler e um pouco mais lento de escrever.

🎤 *"Modelei 3 tabelas com chaves estrangeiras, usei UNIQUE para evitar duplicatas e criei índices nas colunas que o painel filtra."*

✍️ Abra `db/queries.sql` e rode as consultas uma por uma (`docker compose exec db psql -U radar`, depois cole a consulta). **Antes** de rodar, tente adivinhar o resultado. Esse arquivo é o seu material de SQL.

---

## 2. A coleta: `etl/collect.py`

🧠 **Conceitos**
- `requests.get(url, params=...)` faz uma requisição **GET** HTTP. O `params` vira `?jobName=dados&limit=100` na URL.
- **Paginação**: a API devolve no máximo 100 vagas por vez. O `offset` diz de onde começar (0, 100, 200…). Quando vem menos de 100, acabou.
- `response.raise_for_status()`: se a resposta for 4xx ou 5xx, o código para com erro em vez de seguir com lixo.
- `time.sleep(1)`: educação. Não bombardeamos o servidor dos outros.

🎤 *"A coleta pagina a API pública da Gupy com um termo de busca por vez, esperando 1 segundo entre requisições."*

✍️ Adicione um termo novo em `SEARCH_TERMS` (por exemplo `"análise de dados"`) e rode `python -m etl.pipeline`.

---

## 3. A limpeza: `etl/clean.py` (o coração do pandas)

Leia a função `clean()` de cima para baixo. Cada linha é um passo:

| Linha | O que faz |
|---|---|
| `pd.DataFrame(raw)` | lista de dicionários → tabela |
| `df[df["type"] == ...]` | **filtro booleano**: fica só onde a condição é True |
| `drop_duplicates(subset="id")` | remove vagas repetidas (vieram de buscas diferentes) |
| `.str.strip()`, `.str.title()` | limpa espaços, padroniza "BARUERI" → "Barueri" |
| `.str.contains(TECH_TITLE)` | regex: o título tem cara de vaga de tecnologia? |
| `~` | "NÃO": `~titulo.str.contains(EXCLUDE)` = não contém "sênior", "vendas"… |
| `.map(MODALIDADES)` | troca valores: `"remote"` → `"remoto"` |
| `.map(extract_technologies)` | aplica uma função em cada linha |

🧠 **Funções auxiliares**
- `normalize()`: tira acento e põe tudo em minúscula, para "Carapicuíba" e "carapicuiba" serem iguais.
- `classify_region()`: decide se a vaga é remoto, Cotia, Barueri… ou "SP - zona oeste" (procura bairros como Pinheiros e Lapa na descrição, porque a Gupy só diz "São Paulo").
- `extract_stipend()`: regex que acha "R$ 1.800,00" e ignora valores absurdos (como vale-refeição de R$ 30).

🎤 *"Com pandas eu filtro só estágios de tecnologia, removo duplicatas, padronizo cidade e modalidade, e extraio as tecnologias e a bolsa da descrição com expressões regulares."*

✍️ Adicione uma tecnologia nova no dicionário `TECNOLOGIAS` (por exemplo `r"\br\b": "R"`), crie um teste para ela em `tests/test_clean.py` e rode `pytest`.

---

## 4. A carga: `etl/load.py`

🧠 **Conceitos**
- **Upsert** (`INSERT ... ON CONFLICT (gupy_id) DO UPDATE`): se a vaga é nova, insere; se já existe, atualiza. Por isso dá para rodar a coleta todo dia sem duplicar nada.
- **`%s`**: o valor vai **separado** do SQL. O psycopg cuida das aspas. Nunca use f-string com dado de fora dentro de SQL (SQL injection).
- **Transação**: o `with psycopg.connect(...)` faz commit no final. Se der erro no meio, nada é gravado pela metade.
- `none_if_nan`: o pandas usa `NaN` para vazio e o banco usa `NULL` (`None` no Python).

🎤 *"A carga faz upsert pela chave da vaga na Gupy, então a coleta diária é idempotente: rodar duas vezes dá o mesmo resultado."*

---

## 5. A API: `api/main.py`

Rode `uvicorn api.main:app --reload` e abra **http://localhost:8000/docs**. O FastAPI gera uma página onde você testa cada rota clicando em "Try it out". **Faça isso antes de ler o código.**

🧠 **HTTP: o que cada coisa significa**

| Método | Para quê | Exemplo no projeto |
|---|---|---|
| GET | ler | `GET /vagas?regiao=Cotia` |
| POST | criar | `POST /candidaturas` → **201 Created** |
| PATCH | alterar **parte** de algo | `PATCH /candidaturas/3` com `{"status": "entrevista"}` |
| DELETE | apagar | `DELETE /candidaturas/3` → **204 No Content** |

| Status | Significa | Quando acontece aqui |
|---|---|---|
| 200 | OK | GET normal |
| 201 | criado | POST deu certo |
| 204 | ok, sem corpo | DELETE deu certo |
| 404 | não encontrado | vaga ou candidatura não existe |
| 409 | conflito | a vaga já está no kanban |
| 422 | dados inválidos | status "aprovado" não existe (o Pydantic recusa sozinho) |
| 500 | erro no servidor | bug no código (a culpa é nossa, não do cliente) |

🧠 **Outros conceitos**
- **Pydantic** (`class CandidaturaIn(BaseModel)`): descreve o formato do JSON que a rota aceita. Se vier errado, o FastAPI já responde 422.
- **`Literal[...]`**: só aceita aqueles 4 status.
- **`Depends(get_conn)`**: cada requisição pega uma conexão emprestada do *pool* e devolve no fim.
- **Filtros dinâmicos** em `list_vagas`: montamos a lista `where` e a lista `params` juntas. O texto do SQL só recebe `%s`, e os valores vão separados. O teste `test_sql_injection_is_just_text` prova que `'; DROP TABLE vagas; --` vira só um texto de busca.
- **CORS**: o navegador bloqueia um site (localhost:5173) chamando outro endereço (localhost:8000), a não ser que **o servidor** diga "esse site pode". Por isso o CORS é configurado **no back-end** (`CORSMiddleware`), não no React.

🎤 *"A API usa FastAPI com consultas parametrizadas, status HTTP corretos e CORS liberado só para o domínio do front."*

✍️ Crie a rota `GET /empresas` que devolve as empresas com a contagem de vagas de cada uma (dica: JOIN + GROUP BY, igual à consulta 13 do `queries.sql`). Depois teste em `/docs`.

---

## 6. O front: `web/src/`

| Arquivo | Papel |
|---|---|
| `main.jsx` | liga o React na `<div id="root">` |
| `App.jsx` | as 3 abas. `useState('vagas')` guarda qual aba está aberta |
| `api.js` | função `api()` que chama o `fetch` e transforma erro HTTP em exceção |
| `useApi.js` | **hook** que busca dados quando os filtros mudam |
| `Vagas.jsx` | filtros + lista + paginação + botão "Adicionar ao kanban" (POST) |
| `Kanban.jsx` | 4 colunas, setas e arrastar para mudar o status (PATCH) |
| `Estatisticas.jsx` | gráficos de barra feitos só com CSS (largura = valor / maior valor) |

🧠 **Os 4 essenciais do React**
- **`useState`**: uma variável que, quando muda, faz a tela se redesenhar. `const [page, setPage] = useState(0)`.
- **`useEffect(fn, [dependências])`** (em `useApi.js`): roda a busca **só** quando `path`, os filtros ou `reloadKey` mudam. **Sem** a lista de dependências, ele rodaria a cada redesenho. Como a busca muda o estado, o estado causa um redesenho e o redesenho roda o efeito de novo: **loop infinito**. Essa foi a pergunta do diagnóstico.
- **`key`** em listas (`<li key={vaga.id}>`): o React usa a key para saber qual item é qual quando a lista muda. Sem ela, ele pode reaproveitar o elemento errado.
- **props**: `<BarChart title="..." items={...} />` passa dados de pai para filho, como argumentos de função.

🧠 O `ignore = true` no `useEffect`: se você troca o filtro rápido, a resposta antiga pode chegar depois da nova. Essa linha descarta a resposta antiga.

🎤 *"No React uso useState para filtros e paginação, e um hook próprio com useEffect que refaz a busca quando os filtros mudam."*

✍️ Adicione um filtro "só vagas com bolsa informada" (checkbox). A API também precisa aceitar isso: `WHERE bolsa IS NOT NULL`.

---

## 7. Testes e CI: `tests/` e `.github/workflows/`

- `test_clean.py`: testa a limpeza com dados falsos, sem banco nem internet.
- `test_api.py`: cria uma vaga de teste, chama a API de verdade e confere status e respostas. No fim, apaga o que criou.
- `ci.yml`: a cada push, o GitHub sobe um Postgres, roda o `pytest` e faz o build do front. Se quebrar, o selo do README fica vermelho.
- `collect.yml`: todo dia às 7h roda a coleta no banco de produção (Neon).

🎤 *"Tenho testes de unidade na limpeza e testes de integração na API, rodando no GitHub Actions com um Postgres de serviço."*

---

## 8. Perguntas que um entrevistador pode fazer (treine em voz alta)

1. Qual a diferença entre INNER JOIN e LEFT JOIN? Onde você usou cada um? *(consultas 7, 8 e 9; a rota `/vagas` usa LEFT JOIN em candidaturas)*
2. Qual a diferença entre WHERE e HAVING? *(consulta 13)*
3. Como você evitou SQL injection?
4. Por que o CORS está no back-end?
5. O que acontece se a coleta rodar duas vezes no mesmo dia?
6. Por que PATCH e não PUT para mudar o status?
7. O que o `useEffect` sem dependências causaria aqui?
8. Qual foi o maior problema que você encontrou? *(resposta real: o filtro de título pegava "Programa de Estágio" e "Desenvolvimento de Negócios". Ajustamos a regex e adicionamos uma lista de exclusões.)*
9. O que você melhoraria? *(mais fontes de vagas, notificação de vaga nova, testes no front)*
10. Você usou IA? *(resposta honesta: "sim, como par de programação. Revisei e entendo cada parte, posso te mostrar qualquer arquivo.")*

**Regra de ouro:** se você não consegue responder uma dessas sem olhar, volte na seção correspondente e faça o exercício ✍️ dela.
