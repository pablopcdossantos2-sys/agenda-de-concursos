# Metodologia do comparador de conteúdos

## Finalidade

O comparador ajuda a estimar a sobreposição entre os conteúdos programáticos de dois concursos. Ele não substitui a leitura dos editais nem afirma equivalência jurídica, bibliográfica ou pedagógica entre tópicos.

## Como os dados são organizados

Cada concurso contém disciplinas. Cada disciplina contém tópicos individuais. Um tópico tem:
- descrição original, conforme cadastrada pelo usuário;
- nome padronizado opcional, usado como identificador conceitual quando duas descrições representam o mesmo assunto.

O nome original é preservado. A padronização não o substitui.

## Etapas do cálculo

1. Normalização textual: converte para minúsculas, remove acentos e pontuação e reduz espaços repetidos.
2. Associação de disciplinas: compara os nomes normalizados por uma combinação de Jaccard de palavras e similaridade de sequência. O comparador associa nomes com pontuação lexical igual ou superior ao limiar interno de 0,55.
3. Associação de tópicos: dentro de cada par de disciplinas, compara tópicos. Se ambos tiverem o mesmo nome padronizado não vazio, a correspondência é considerada explícita e recebe 100%. Caso contrário, usa similaridade lexical; pares com pontuação a partir de 0,34 são candidatos.
4. Seleção de pares: a implementação escolhe correspondências de maior pontuação sem reutilizar o mesmo tópico em dois pares.
5. Agregação: calcula a cobertura ponderada de tópicos correspondentes em cada disciplina pareada. Disciplinas sem par contribuem com zero. A pontuação global pondera cada disciplina pela quantidade de tópicos da maior lista entre os dois concursos.

A similaridade lexical combina Jaccard de conjuntos de palavras (65%) e SequenceMatcher (35%). Na pontuação por disciplina, 90% vêm da cobertura dos tópicos e 10% da semelhança dos nomes das disciplinas.

## Interpretação

- 100% significa que todos os tópicos contabilizados foram associados segundo as regras acima. Não significa que os editais sejam idênticos.
- Uma pontuação intermediária sugere sobreposição parcial; examine os pares listados.
- Tópicos exclusivos de cada concurso reduzem a pontuação.
- A chave padronizada é uma decisão do usuário e pode gerar associação explícita mesmo com descrições muito diferentes. Use-a apenas quando houver equivalência de fato.
- O limiar lexical pode produzir falsos positivos ou deixar de reconhecer sinônimos. Revise manualmente os resultados.

## Limitações conhecidas

A primeira versão não utiliza modelos semânticos, embeddings, ontologias oficiais, stemming avançado ou análise contextual. Também não interpreta subitens hierárquicos de um edital automaticamente. A análise é textual e explicável; melhorias semânticas podem ser adicionadas futuramente sem alterar o formato de armazenamento.
