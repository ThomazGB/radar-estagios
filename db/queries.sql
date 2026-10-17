-- Radar de Estágios — consultas de estudo
-- Rode no banco local: docker compose exec db psql -U radar
-- Cada bloco mostra um conceito de SQL usando os dados reais do projeto.

-- 1. SELECT básico: algumas colunas, poucas linhas
SELECT titulo, cidade, modalidade
FROM vagas
LIMIT 10;

-- 2. WHERE: só vagas remotas
SELECT titulo, cidade
FROM vagas
WHERE modalidade = 'remoto';

-- 3. WHERE com IN: várias cidades de uma vez
SELECT titulo, cidade
FROM vagas
WHERE regiao IN ('Cotia', 'Barueri', 'Osasco');

-- 4. ORDER BY + LIMIT: as 5 maiores bolsas (NULLS LAST joga as vagas sem bolsa para o fim)
SELECT titulo, bolsa
FROM vagas
ORDER BY bolsa DESC NULLS LAST
LIMIT 5;

-- 5. ILIKE: busca por texto, sem diferenciar maiúscula/minúscula (% = qualquer coisa)
SELECT titulo
FROM vagas
WHERE titulo ILIKE '%dados%';

-- 6. IS NULL: vagas que não informam bolsa
SELECT COUNT(*) AS sem_bolsa
FROM vagas
WHERE bolsa IS NULL;

-- 7. INNER JOIN: título da vaga + nome da empresa (só linhas que existem nas DUAS tabelas)
SELECT v.titulo, e.nome AS empresa
FROM vagas v
JOIN empresas e ON e.id = v.empresa_id
LIMIT 10;

-- 8. LEFT JOIN: TODAS as vagas, com o status da candidatura quando existir (senão vem NULL)
SELECT v.titulo, c.status
FROM vagas v
LEFT JOIN candidaturas c ON c.vaga_id = v.id
LIMIT 10;

-- 9. LEFT JOIN + IS NULL: vagas em que você AINDA NÃO se candidatou
SELECT v.titulo
FROM vagas v
LEFT JOIN candidaturas c ON c.vaga_id = v.id
WHERE c.id IS NULL
LIMIT 10;

-- 10. GROUP BY + COUNT: quantas vagas por região
SELECT regiao, COUNT(*) AS total
FROM vagas
GROUP BY regiao
ORDER BY total DESC;

-- 11. GROUP BY com duas colunas: região x modalidade
SELECT regiao, modalidade, COUNT(*) AS total
FROM vagas
GROUP BY regiao, modalidade
ORDER BY regiao, total DESC;

-- 12. AVG / MIN / MAX: estatísticas da bolsa
SELECT ROUND(AVG(bolsa)) AS media, MIN(bolsa) AS menor, MAX(bolsa) AS maior
FROM vagas
WHERE bolsa IS NOT NULL;

-- 13. HAVING: filtra DEPOIS de agrupar (WHERE filtra antes). Empresas com 2+ vagas
SELECT e.nome, COUNT(*) AS vagas
FROM vagas v
JOIN empresas e ON e.id = v.empresa_id
GROUP BY e.nome
HAVING COUNT(*) >= 2
ORDER BY vagas DESC;

-- 14. Arrays: vagas que pedem Python (ANY procura dentro do array)
SELECT titulo, tecnologias
FROM vagas
WHERE 'Python' = ANY(tecnologias);

-- 15. unnest: "abre" o array em linhas para contar as tecnologias mais pedidas
SELECT tec, COUNT(*) AS total
FROM vagas, unnest(tecnologias) AS tec
GROUP BY tec
ORDER BY total DESC
LIMIT 10;

-- 16. Datas: vagas publicadas nos últimos 7 dias
SELECT titulo, publicada_em
FROM vagas
WHERE publicada_em >= now() - INTERVAL '7 days'
ORDER BY publicada_em DESC;

-- 17. CASE: cria uma faixa de bolsa
SELECT titulo, bolsa,
       CASE
           WHEN bolsa IS NULL THEN 'não informada'
           WHEN bolsa < 1500 THEN 'até 1.500'
           WHEN bolsa < 2500 THEN '1.500 a 2.500'
           ELSE 'acima de 2.500'
       END AS faixa
FROM vagas;

-- 18. Subconsulta: vagas com bolsa acima da média
SELECT titulo, bolsa
FROM vagas
WHERE bolsa > (SELECT AVG(bolsa) FROM vagas)
ORDER BY bolsa DESC;

-- 19. INSERT / UPDATE / DELETE: o ciclo de uma candidatura (é o que a API faz)
-- INSERT INTO candidaturas (vaga_id) VALUES (1);
-- UPDATE candidaturas SET status = 'candidatei', atualizada_em = now() WHERE vaga_id = 1;
-- DELETE FROM candidaturas WHERE vaga_id = 1;

-- 20. Índice: EXPLAIN mostra se o Postgres usa o índice idx_vagas_regiao
--     (com poucas linhas ele pode preferir ler a tabela toda — e tudo bem)
EXPLAIN SELECT * FROM vagas WHERE regiao = 'Barueri';
