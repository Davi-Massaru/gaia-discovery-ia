# Efetividade científica do agente e dos relatórios

Data: 2026-11-03. Avaliação documental e retrospectiva dos relatórios reais 33/34, mensagens da sessão 221, código de ingestão/correlação e diagnóstico dos 34 registros existentes. As recomendações abaixo não alteram o sistema ou reclassificam registros.

## Parecer

O sistema demonstrou coleta, orquestração e rastreabilidade reais. É útil como organizador de evidências para triagem astronômica. A precisão científica das avaliações e o ganho da seleção adaptativa de consultas ainda não foram demonstrados. O PASS da integração comprova execução e contratos, sem certificar a interpretação astronômica.

Os dois alertas recentes não têm classificação independente de referência nesta auditoria. Portanto, não é possível calcular acurácia, precisão, sensibilidade ou taxa verdadeira de novidade. A proporção de INCONCLUSIVE não deve ser usada isoladamente como indicador de qualidade.

## Evidência disponível

| Critério | Observação | Conclusão permitida |
|---|---|---|
| Integração nativa | 8 requisições/respostas do agente, 8 decisões válidas e 6 consultas de catálogo com HTTP 200 | Motor e contratos funcionam nos dois exemplos |
| Proveniência | IDs, consultas, separações, timestamps, streams e mensagens persistidos | Relatórios são auditáveis |
| Uso de evidência | Relatório 33 mudou a hipótese após encontrar uma galáxia SIMBAD | Existe reação ao retorno de catálogo |
| Hipóteses concorrentes | Primeira decisão dos dois exemplos contém `alternative=null` | O comportamento de comparação de hipóteses não foi demonstrado no início |
| Escolha adaptativa | Ambos fizeram Gaia → SIMBAD → IRSA → FINISH | A amostra não demonstra economia ou superioridade sobre sequência fixa |
| Evidência temporal | Código seleciona somente a detecção mais recente | Não há análise de evolução da fonte |
| Associação | Busca por cone e separação angular; ressalvas de época/blending | Localização de candidatos, sem associação estatística calibrada |
| Avaliação final | Dois INCONCLUSIVE com execução OK | Incerteza científica separada de falha técnica nessa rodada |

O histórico total contém 29 registros sem decisão válida do agente, três com algum erro de catálogo e dois com execução recente bem-sucedida. Não é uma amostra científica representativa; inclui falhas acumuladas durante desenvolvimento.

## Achados científicos prioritários

### 1. Analogias recuperadas podem reproduzir conclusões historicamente inadequadas

Os relatórios 33 e 34 receberam o registro 30 como analogia. Seu resumo sugere novidade a partir de ausência de matches e falhas de acesso. O registro tem execução degradada e erros de catálogo. O filtro atual em `backend/gaia/embedding.py` exige vetor e avaliação diferente de INCONCLUSIVE, mas não exige execução saudável nem validação científica da interpretação.

As primeiras hipóteses dos dois novos relatórios também mencionam fonte nova/rara antes das consultas locais. Há evidência de exposição a uma analogia problemática; influência causal do RAG não foi comprovada.

**Melhoria:** tornar entradas elegíveis para memória por proveniência, integridade técnica e auditoria científica, preservando a regra atual de exclusão de INCONCLUSIVE. Realizar ensaio com/sem histórico usando as mesmas evidências e o mesmo orçamento. Manter os registros históricos intactos.

### 2. Ausência em catálogo está sendo associada a novidade cedo demais

No relatório 33, a primeira hipótese menciona ausência de contrapartes antes de consultas. No 34, a primeira hipótese descreve objeto não catalogado/raro. O retorno EMPTY só sustenta ausência de linha na consulta executada. Não estabelece a ausência da fonte em todos os dados disponíveis nem uma população rara.

**Melhoria:** exigir hipóteses inicialmente neutras; distinguir fato fornecido, hipótese e informação ainda não investigada. Qualquer interpretação de novidade deve depender de evidências adicionais independentes. Tags do broker devem ser tratadas como seleção prévia, sem substituir classificação de referência.

### 3. A normalização AllWISE perde a distinção entre detecção e limite

O candidato IRSA do relatório 33 tem `ph_qual=BUUU`. A banda W2 está marcada U; seu valor numérico não deve ser interpretado como uma detecção W2 normal nem formar uma cor W1−W2 comum. O parser atual converte os números, mas não produz uma interpretação determinística do flag por banda.

A documentação [AllWISE](https://irsa.ipac.caltech.edu/data/WISE/docs/release/AllWISE/expsup/sec2_1a.html) descreve a ordem W1/W2/W3/W4, as classes de qualidade, os limites e os campos de incerteza.

**Melhoria:** normalizar medição/limite por banda, preservar qualidade e incertezas, obter indicadores de contaminação quando disponíveis e impedir inferências fotométricas não sustentadas. A ressalva deve chegar ao agente como dado estruturado.

### 4. Evidência contextual e identificação física estão sendo confundidas

O relatório 33 encontrou `VIPERS 105148635`, tipo galáxia, a 0,1703″. Isso é contexto catalogado registrado. A conclusão final mistura falta de identificação definitiva com falta de contexto. Pelo contrato do produto, CATALOG_CONTEXT_FOUND não exige identidade física confirmada.

Uma interpretação mais útil seria: contexto de uma galáxia próxima; associação/hospedeira ainda não determinada; candidato IRSA a 9,6364″ com associação fraca e limitações fotométricas. Isso não classifica o evento como supernova, AGN ou descoberta.

No relatório 34, Gaia e SIMBAD retornaram EMPTY e o único candidato IRSA está a 9,1323″. Manter INCONCLUSIVE é defensável com os dados disponíveis. A auditoria não demonstrou que essa fonte infravermelha seja a contraparte.

**Melhoria:** explicitar no prompt os critérios das três avaliações e exemplos contrastados. O mecanismo determinístico deve continuar impedindo que falhas sejam convertidas em ausência científica. Reclassificações históricas requerem uma execução/revisão explícita e rastreável.

### 5. A associação espacial ainda é insuficiente para interpretação física

Não há propagação aplicada das posições Gaia à época do alerta, uso das incertezas/covariâncias na associação, avaliação de densidade local ou tratamento específico de possíveis hospedeiras estendidas. A documentação de [crossmatch Gaia](https://gea.esac.esa.int/archive/documentation/GDR1/Catalogue_consolidation/sec_cu1cva/sec_cu1cva_procsteps.html) descreve uso de erros, movimento próprio e densidade no escore de associação.

**Melhoria:** uma camada determinística em Embedded Python deve representar compatibilidade posicional, ambiguidades e qualidade. Faltas de dados devem resultar em indicação explícita de informação insuficiente, sem probabilidades inventadas. Consultas limitadas precisam ordenar candidatos no servidor e registrar possível truncamento.

Essas limitações são observadas no código; não foi demonstrado que tenham causado os EMPTY específicos dos dois alertas. Apenas aumentar raios pode adicionar associações fortuitas.

### 6. Falta informação para decidir a natureza temporal e a confiabilidade do alerta

A ingestão solicita coordenadas, tempo e fluxo/erro, e retém o registro de maior MJD. Não calcula curva de luz, cores contemporâneas, recorrência, movimento, limites anteriores ou qualidade de subtração. A razão fluxo/erro dos registros selecionados é aproximadamente 7,31 e 8,13; esses números isolados não caracterizam a população da fonte.

Imagens estão corretamente disponíveis ao revisor, mas o agente recebe apenas dados estruturados. Não existe inspeção multimodal automática demonstrada. PNGs renderizados não substituem imagens calibradas, WCS e metadados para medidas científicas.

Os [produtos Rubin](https://rubinobservatory.org/for-scientists/data-products/data-access) incluem séries temporais e informações de objetos móveis. A [discussão técnica Rubin sobre fotometria de alertas](https://www.rubin.community/t/photometric-quality-of-alert-photometry/11720), por integrante da equipe, recomenda considerar confiabilidade e problemas de subtração.

**Melhoria:** após validar os campos disponíveis na API efetivamente usada, incorporar uma série temporal limitada, banda, sinal/erro, qualidade e indicadores de movimento. Esse enriquecimento amplia o escopo da ingestão e precisa de contratos e testes próprios.

## Plano de validação científica

1. Definir o resultado esperado como triagem: identificar contexto, explicitar incertezas e recomendar uma próxima observação útil. Definir classes físicas somente quando houver dados e referência para avaliá-las.
2. Montar um conjunto piloto proposto de 100–200 objetos com referência independente e revisada: fontes estelares variáveis, núcleos ativos, transientes associados a galáxias, objetos móveis, artefatos e casos realmente sem informação suficiente. Esse tamanho é um início de avaliação, não garantia estatística.
3. Separar objetos de ajuste e avaliação; diferentes alertas da mesma fonte não devem aparecer nos dois conjuntos. Na avaliação retrospectiva, impedir uso de informação posterior à data que o agente deveria conhecer.
4. Congelar evidências externas com timestamps, versões e identificadores. Comparar versões do agente sobre as mesmas evidências, sem confundir mudança de catálogo com melhoria do modelo.
5. Comparar três estratégias com mesmo orçamento máximo: sequência fixa de catálogos; agente atual; agente com melhorias de normalização/associação. Fazer comparação com/sem RAG e repetir chamadas para medir variabilidade do LLM.
6. Submeter relatórios sem identificar a versão a revisores astronômicos; resolver divergências e registrar justificativas. A anotação de referência não deve ser derivada somente de um tag do broker ou de relatórios anteriores do próprio agente.
7. Medir os resultados abaixo com intervalos de confiança e estratificação por população, qualidade e disponibilidade de dados.

| Medida | O que responde |
|---|---|
| Afirmações sustentadas por evidência | O relatório afirma apenas o que os dados permitem? |
| Associação correta e recuperação de contrapartes | A contraparte real é encontrada e falsos vizinhos são evitados? |
| Precisão e recuperação da fila REVIEW_CANDIDATE | Os casos relevantes chegam ao humano com carga aceitável? |
| Qualidade da abstenção | INCONCLUSIVE concentra falta real de informação e identifica a causa? |
| Informação necessária obtida por consulta | As consultas alteram hipóteses ou decisões de modo útil? |
| Concordância entre execuções e revisores | A avaliação é estável e compreensível? |
| Latência, tokens, custo e tempo do revisor | Há ganho operacional sobre a sequência fixa e a triagem manual? |

Metas de precisão/recuperação devem ser definidas conforme a população e a capacidade de seguimento. Uma fração menor de INCONCLUSIVE, isoladamente, pode significar mais confiança injustificada.

## Priorização proposta

- **P0:** qualidade do histórico recuperado; tratamento de limites AllWISE; fatos versus hipóteses; definição operacional das avaliações; referência verificável para cada afirmação relevante.
- **P1:** camada de associação em Embedded Python com incertezas, épocas, ambiguidades e ordenação de candidatos; relatório separando contexto encontrado, associação possível e classificação ainda aberta.
- **P2:** enriquecimento temporal/qualidade do alerta e benchmark independente, antes de reivindicar classificação física ou ganho adaptativo.

Preservar `Gaia.AI.DiscoveryAgent`, a Production, o BPL, as Operations, Embedded Python e ClassMethods. O trabalho recomendado é principalmente de qualidade de evidência e avaliação científica. A migração estrutural do agente não resolve esses pontos por si só.
