# Validação real de Gaia.AI.DiscoveryAgent pela interoperabilidade

Data: 2026-11-03, aproximadamente 08:31–08:35, America/Sao_Paulo.

Resultado: **PASS** para o fluxo executado, com fontes e respostas reais, sem fixtures.

## Execução

- Ambiente: `gaia-discovery-dev`, IRIS 2026.3.0AI build 154U, namespace USER; Production `Gaia.Production` ativa.
- Entrada: HTTP autenticado `POST /gaia/api/discoveries/run`, tag `extragalactic_new_candidate`, `count=2`.
- Aceite assíncrono: **HTTP 202 em 0,134 s**.
- Run: `62c736ab-9e6e-4724-8bb0-702ff793b0d9`; conclusão `COMPLETED`, dois relatórios persistidos.
- Caminho: WSGI → `DiscoveryService` → `DiscoveryWorkflow` → `AIHubOperation` → `Gaia.AI.DiscoveryAgent` → Operations dos catálogos selecionados → relatórios.
- Provider OpenAI, modelo `gpt-4.1-mini`. `Chat` e `CreateSession` herdados de `%AI.Agent`, conforme metadados nativos. Nenhuma classe `GaiaTest.*` na Production; flag de fixtures desativada.

## Resultados

| Relatório | Objeto Rubin/Fink | Sessão de interoperabilidade | Chamadas/decisões válidas | Gaia | SIMBAD | IRSA | Avaliação |
|---|---|---|---|---|---|---|---|
| 33 | 171141237268545549 | 221 | 4 / 4 | EMPTY | OK: 1 candidato | OK: 1 candidato | INCONCLUSIVE |
| 34 | 171145624633737349 | 221 | 4 / 4 | EMPTY | EMPTY | OK: 1 candidato | INCONCLUSIVE |

Foram registradas **oito requisições e oito respostas reais do agente** na sessão 221. Em cada objeto, o agente escolheu `CHECK_GAIA → CHECK_SIMBAD → CHECK_IRSA → FINISH`. As oito decisões passaram na validação do schema e nos limites de ações distintas. As seis consultas de catálogo roteadas pelo BPL concluíram com HTTP 200. O fallback real de SIMBAD para Harvard preservou os detalhes das tentativas.

Ambos os relatórios têm `executionStatus=OK`. `INCONCLUSIVE` é a avaliação científica retornada após a investigação, sem confirmação de identidade ou descoberta. Os identificadores astronômicos permanecem strings.

## Verificações adicionais

- Seis PNGs autênticos obtidos por HTTP, validados e comparados byte a byte aos streams persistidos; SHA-256 e cópias no pacote.
- Detalhes e listagem HTTP 200; parâmetros inválidos 400; recursos ausentes 404; página e JavaScript HTTP 200.
- Busca semântica real HTTP 200.
- Verificação independente do provider de embeddings: vetor real de **1536 dimensões**; `VECTOR_COSINE` nativo do vetor consigo mesmo = **1,0**. Esse teste não alterou relatórios nem as regras de elegibilidade de embeddings.
- Diagnóstico adicional do adaptador Java PEX: Gaia HTTP 200 / EMPTY; SIMBAD HTTP 200 / EMPTY; IRSA HTTP 200 / OK. Essas consultas são separadas das seis consultas científicas do BPL.

## Evidências e reprodução

Diretório: `dist/agent-interop-real-62c736ab-9e6e-4724-8bb0-702ff793b0d9/`.

Arquivo ZIP correspondente: `dist/agent-interop-real-62c736ab-9e6e-4724-8bb0-702ff793b0d9.zip`.

O pacote contém resumo, `evidence.json`, validação HTTP, relatórios completos, mensagens da sessão 221, evidências enviadas em cada chamada do agente, decisões validadas, o prompt utilizado e seis imagens originais. Inclui hashes do prompt, das imagens e dos arquivos de implementação. Não inclui credenciais.

Scripts: `scripts/validate_real_e2e.py` inicia e valida a investigação; `scripts/collect_agent_interop_evidence.py` exporta o pacote e executa a verificação independente de embeddings. Ambos executam em Embedded Python no IRIS de desenvolvimento. Executar novamente o primeiro script cria novas investigações e chamadas reais ao provedor.

## Limites desta rodada

O Workflow humano não foi acionado: ambos os resultados foram `INCONCLUSIVE`, com revisão `NOT_REQUIRED`. Nenhuma avaliação foi alterada para forçar a criação de uma tarefa. ACCEPT/REJECT foram cobertos anteriormente em integração isolada, não nesta rodada real.

Os relatórios desta rodada não receberam novos embeddings, conforme a regra existente para INCONCLUSIVE. A disponibilidade do provider de embeddings e a operação SQL vetorial foram verificadas separadamente, e a busca semântica usou o histórico elegível existente.

Esta rodada validou o ambiente de desenvolvimento. O contêiner Compose existente não foi reconstruído ou apresentado como atualizado por este teste.
