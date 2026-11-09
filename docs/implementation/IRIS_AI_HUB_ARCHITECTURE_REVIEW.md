# Validação da arquitetura IRIS / AI Hub

Data: 2026-11-03. Escopo: inspeção do código, metadados do IRIS instalado e testes isolados existentes. Esta revisão não modifica a implementação nem certifica uma execução ponta a ponta.

**Registro histórico anterior à migração:** a extração posteriormente autorizada para `Gaia.AI.DiscoveryAgent` está documentada no [modelo de migração](DISCOVERY_AGENT_MIGRATION.md). As constatações abaixo descrevem a arquitetura antes dessa extração.

## Parecer

A aplicação adere às abstrações de interoperabilidade do IRIS e utiliza de fato o SDK nativo do AI Hub. A implementação do agente é programática, dentro de uma Business Operation. Criar uma subclasse de `%AI.Agent` é uma melhoria recomendada de encapsulamento e reutilização; sua ausência, isoladamente, não torna a solução incompatível com o IRIS.

Não é adequado substituir a herança de `AIHubOperation`: ela deve continuar estendendo `Ens.BusinessOperation` e compor um agente. A classe proposta `Gaia.AI.DiscoveryAgent Extends %AI.Agent` deve concentrar a identidade e configuração do agente. Não é necessário converter todos os componentes de IA em agentes.

## Arquitetura observada

```text
Navegador → Flask hospedado no WSGI do IRIS
          → DiscoveryService (Ens.BusinessService)
          → DiscoveryWorkflow (Ens.BusinessProcessBPL)
              → FinkOperation (adaptador HTTP nativo)
              → AIHubOperation (Ens.BusinessOperation)
                  → %AI.Provider → %AI.Agent → nova sessão → Chat
                  → validação determinística da decisão em Embedded Python
              → Operation do catálogo escolhido → adaptador Java PEX TAP
              → nova decisão com evidências atualizadas, até FINISH
              → DiscoveryReport (%Persistent, streams e vetor)
              → Workflow nativo para revisão humana quando aplicável
```

O agente retorna decisões JSON; o BPL executa as consultas. Não há ferramentas registradas no agente. O histórico científico é reconstruído em Python e enviado no contexto de cada chamada. A busca usa SQL vetorial nativo; o embedding é obtido diretamente da API OpenAI por Python.

## Constatações e recomendações

| Componente | Evidência | Avaliação / ação |
|---|---|---|
| Production, Service, BPL e Operations | `src/iris/Gaia/Production.cls`, `Interop/DiscoveryService.cls`, `Interop/DiscoveryWorkflow.cls` | Heranças e separação de responsabilidades aderentes ao IRIS. Preservar. |
| Agente nativo | `AIHubOperation.cls:16–21` cria `%AI.Provider` e `%AI.Agent`, configura modelo/prompt e chama `Chat` | Uso real do SDK. Extrair uma classe própria é recomendado, sem criar outro agente funcional ou outro fluxo. |
| Configuração do agente | Prompt em `backend/gaia/runtime.py:193`; configuração e ciclo de vida na Operation | Responsabilidade distribuída. Concentrar identidade, instruções e configuração em `Gaia.AI.DiscoveryAgent`; Python pode continuar responsável pelo contexto e validação científica. |
| Inicialização | Ausência de `%Init()` na Operation; método disponível no runtime | Padronizar a inicialização e tratar seu `%Status`, especialmente na migração para configuração declarativa. A inspeção não demonstrou falha funcional do caminho programático existente. |
| Sessões | `CreateSession()` executado a cada decisão | Não existe uma única sessão conversacional reutilizada por investigação nesse caminho. O contexto externo torna o desenho viável, mas é necessário documentar essa escolha, correlacionar IDs e definir retenção. Reutilizar sessão por investigação apenas se necessário. |
| Observabilidade | Relatório salva `InteropSessionId`; Operation não exporta ID/estatísticas da sessão AI Hub | Acrescentar correlação entre execução, objeto, mensagem e sessão AI Hub, mais latência/tokens quando expostos. Sessões de interoperabilidade e AI Hub são distintas. |
| Tools e políticas | Nenhum ToolSet ou Policy conectado ao agente | Coerente com a decisão de deixar a execução no BPL. Criar `%AI.ToolSet` / `%AI.Tool` e políticas somente se o agente passar a executar ferramentas. Operations não se tornam tools automaticamente. |
| Credenciais | Chave lida do ambiente e passada diretamente ao provider | Funciona, mas não utiliza a configuração centralizada do AI Hub. Avaliar Config Store/Wallet e recursos RBAC para governar modelos e credenciais. Não implica, por si só, exposição da chave. |
| Histórico semântico | `backend/gaia/embedding.py` usa HTTP OpenAI e `VECTOR_COSINE` | Aderente ao Vector Search IRIS. Usa uma integração própria para embeddings; avaliar `%AI.RAG.Embedding.OpenAI` para uniformizar o acesso ao provedor, preservando contratos e filtros existentes. |
| Revisão humana | `EnsLib.Workflow.Operation` e mensagens nativas no BPL | Escolha aderente ao Workflow IRIS. Preservar. |
| Documentação | `CLASS_MAP.md:26` e `CLASS_CONTRACTS.md:50` evitam classe própria; `SPEC.md` ainda declara implementação somente documental | Restrição a subclasses é uma decisão do projeto, não exigência do SDK. Atualizar esses documentos antes/junto de eventual refatoração. |

## Heranças propostas por responsabilidade

| Responsabilidade | Base apropriada |
|---|---|
| Agente científico com identidade própria | `%AI.Agent` |
| Integração do agente com filas/mensagens da Production | `Ens.BusinessOperation` |
| Ferramentas disponibilizadas ao modelo, se necessárias | `%AI.ToolSet` / `%AI.Tool` |
| Autorização/auditoria de ferramentas, se necessárias | `%AI.Policy.Authorization` / `%AI.Policy.Audit` |
| Orquestração da investigação e revisão | `Ens.BusinessProcessBPL` |
| Persistência de relatórios | `%Persistent` |
| Cálculos e helpers determinísticos | Funções Python / `%RegisteredObject`, conforme o contrato |

Prioridade recomendada: extrair o agente e padronizar inicialização; explicitar ciclo de vida/correlação de sessões; centralizar configuração e credenciais; avaliar integração nativa de embeddings. ToolSets, MCP, skills e subagentes dependem de necessidade funcional, não são requisitos de aderência.

## Verificações executadas

- Dois contêineres locais em execução e saudáveis na consulta: `gaia-discovery-dev` e `gaia_discovery_ai-iris-1`.
- Versão lida dentro de `gaia-discovery-dev`: **IRIS 2026.3.0AI, Build 154U**, Linux Ubuntu x86-64. Não inferir compatibilidade pela comparação isolada de números de build entre releases.
- Metadados do namespace USER confirmam `%AI.Agent`, `%AI.Agent.Session` persistente, `%AI.ToolSet`, `%AI.Tool`, `%AI.Policy.*`, `%AI.RAG.Embedding.OpenAI`, `%AI.RAG.VectorStore.IRIS`, `%AI.RAG.KnowledgeBase` e `%AI.Utils.*`.
- `%AI.Agent` instalado expõe `%Init`, `%OnNew(provider)`, `CreateSession(config)`, `Chat(session,input,feedback)` e `Run`.
- Parâmetros declarativos instalados incluem `PROVIDER`, `MODEL`, `APIKEY`, `PROVIDERCONFIG`, `TOOLSETS` e `SKILLS`.
- Instanciação local com credencial fictícia e `%Init()` concluída com sucesso, sem chamar o LLM ou criar sessão persistente. Provider e ToolManager já existiam antes de `%Init()` no caminho programático testado.
- Nenhuma classe própria `Gaia.*` de agente apareceu nos metadados consultados.
- `docker exec gaia-discovery-dev python3 -m unittest discover -s /opt/gaia/tests -v`: **31 testes aprovados**. Cobrem contratos e comportamento isolado, sem comprovar integração real com serviços externos.
- Não foram realizadas chamadas pagas, consultas aos catálogos nem alterações nas classes/Production durante a revisão. Não foi compilada uma subclasse proposta; a existência dos parâmetros não substitui esse teste.

## Fontes primárias

- [AI Hub ObjectScript SDK Guide](https://github.com/intersystems-community/ai-hub-eap/blob/master/ObjectScript_SDK_Guide.md): documenta criação programática e configuração declarativa por subclasse, com `%Init()`. O `master` evolui; não equivale à documentação congelada do runtime local.
- [AI Hub Advanced SDK](https://github.com/intersystems-community/ai-hub-eap/blob/master/ObjectScript_SDK_Advanced.md): políticas, skills e RAG. Disponibilidade das classes acima confirmada separadamente no runtime local; comportamento completo não exercitado nesta revisão.
- [Config Store Guide](https://github.com/intersystems-community/ai-hub-eap/blob/master/Config_Store_Guide.md): configuração centralizada, recursos de acesso e integração com Wallet.

Conclusão: a proposta de criar uma classe própria `extends %AI.Agent` é apropriada para organizar o agente científico. A arquitetura atual já usa AI Hub nativo e pode evoluir preservando Production, BPL, Operations, validação determinística e Workflow existentes.
