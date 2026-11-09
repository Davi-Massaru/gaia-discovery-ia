# Gaia.AI.DiscoveryAgent — modelagem e migração

Data: 2026-11-03. Escopo: extração estrutural do agente existente para uma subclasse nativa `%AI.Agent`, sem modificar comportamentos ou features.

## Configuração anterior e contrato preservado

`AIHubOperation.Handle()` criava o provider OpenAI, instanciava `%AI.Agent` diretamente, aplicava modelo/instruções/limite e criava uma sessão para uma decisão. O BPL mantinha o estado científico fora da sessão e voltava a chamar a Operation após cada catálogo selecionado.

| Aspecto | Antes e depois |
|---|---|
| Provider | `%AI.Provider.Create("openai", {"api_key": ...})` |
| Chave | `OPENAI_API_KEY`; valor vazio quando ausente; nenhum segredo em código |
| Modelo | `OPENAI_MODEL`; fallback `gpt-4.1-mini`; leitura a cada instanciação |
| Instruções | Mesmo `gaia.runtime.SYSTEM_PROMPT`, sem alteração de texto |
| Inicialização | Caminho programático nativo `%New(provider)` / `%OnNew(provider)` |
| Limite do agente | `MaxIterations=1`, como anteriormente |
| Sessão | Nova sessão nativa por decisão, sem introduzir memória conversacional adicional |
| Contexto | Mesmo `agent_prompt`, evidências limitadas e decisões anteriores no estado externo |
| Decisão | Mesma validação JSON, enumerações, fallback e histórico |
| Execução | BPL continua selecionando e chamando somente a Operation autorizada |
| Limites científicos | Até três catálogos distintos e quatro decisões por alerta |
| Falhas | Mesmos códigos e estágios `AI_HUB_PROVIDER`, `AI_HUB_CHAT`, `AI_HUB_VALIDATION` |
| Tools / MCP | Nenhuma ferramenta, política, skill, MCP ou subagente acrescentado |
| Demais features | HTTP/WSGI, UI, imagens, persistência, vetores, PEX e Workflow mantidos |

## Modelo de responsabilidades

```text
DiscoveryWorkflow (Ens.BusinessProcessBPL)
    → AIHubOperation (Ens.BusinessOperation)
        → CreateAgent(): Gaia.AI.DiscoveryAgent
            → %OnNew(provider): provider existente ou OpenAI configurado
            → inicialização herdada de %AI.Agent
            → modelo + instruções + MaxIterations existentes
        → CreateSession() e Chat() herdados
        → Context() / Apply(): mesmas funções Python
        → resposta ou tratamento de falha existente
    → catálogo escolhido / FINISH / persistência / revisão humana
```

`Gaia.AI.DiscoveryAgent` concentra a configuração do agente. O construtor mantém a assinatura de provider opcional da classe base. Isso permite a construção nativa com provider explícito, sem duplicar o ciclo conversacional do SDK. Os métodos de configuração e instruções permanecem `ClassMethod`, com `Language = python`; contexto, validação, embeddings e toda a lógica científica continuam em Embedded Python.

`AIHubOperation` preserva a herança `Ens.BusinessOperation`, as mensagens, a correlação, os estágios de falha, a criação de sessão e a aplicação da decisão. `CreateAgent()` centraliza a composição e permite testar esse limite com uma subclasse local de teste. `ApiKey()`, `Model()` e `Prompt()` continuam disponíveis, delegando ao agente, para manter compatibilidade com diagnósticos existentes.

O prompt continua versionado em Python: sua transferência para XData, o uso declarativo de `%Init()`, Config Store/Wallet, sessão por investigação e RAG nativo são mudanças separadas. Não integram esta migração porque podem alterar inicialização, configuração ou contexto. A extração usa a inicialização programática já existente e chama `##super(provider)` explicitamente.

## Plano e aplicação

1. Identificar a configuração e os contratos efetivamente usados na Operation e no runtime instalado.
2. Extrair a configuração para `src/iris/Gaia/AI/DiscoveryAgent.cls`; herdar o motor, sessões e `Chat()` do SDK.
3. Compor o novo agente na Operation, preservando os demais caminhos e os métodos de compatibilidade.
4. Atualizar `CLASS_MAP`, contratos, componente AI Hub, SPEC, mapa tecnológico, README e probe para o novo tipo.
5. Compilar no build instalado; comparar configuração anterior e nova; executar regressão nativa da Operation e testes existentes.
6. Validar BPL, persistência, vetores e Workflow no contêiner descartável com fontes externas simuladas. Registrar os resultados abaixo.

Nenhuma migração SQL, alteração de mensagens ou mudança de dados históricos é necessária. `Gaia.PKG` no manifesto IPM e o carregamento recursivo em `install.cos` já incluem o novo subpacote. Docker já copia toda a árvore `src/`.

## Implantação e reversão

No desenvolvimento, carregar/compilar primeiro `DiscoveryAgent.cls`, depois `AIHubOperation.cls`. Os testes `GaiaTest.*` pertencem a `tests/native/`, fora de `src/iris`, e devem ser carregados somente em contêiner descartável.

Para outra instalação, distribuir o código atualizado pelo fluxo Docker/IPM existente, em janela apropriada às execuções em andamento. Não é necessário recriar relatórios, tarefas ou sessões históricas. Esta alteração não reconstrói automaticamente o contêiner Compose já existente.

A reversão recompila a versão anterior da Operation, que instancia `%AI.Agent` diretamente. A classe nova pode permanecer instalada sem uso; sua remoção não é necessária para reverter. Não há reversão de dados.

## Validação

- Runtime de desenvolvimento: IRIS **2026.3.0AI, build 154U**, namespace USER.
- Nova classe e Operation compiladas com sucesso; instanciação confirmou `Gaia.AI.DiscoveryAgent`, provider `openai`, modelo corrente `gpt-4.1-mini`, `MaxIterations=1` e igualdade das instruções.
- Compilação recursiva completa aprovada: **14 classes-fonte**, incluindo `Gaia.Production`, mais classes geradas do BPL.
- Regressão específica: `tests/native/GaiaTest.AgentMigration.cls`. Compara configuração antiga/nova e catálogo de tools; exercita a Operation real com `Chat` simulado, cobrindo seleção de catálogo, FINISH, saída inválida, falhas de provider/chat e discriminador inválido.
- Regressão nativa específica: aprovada (`AGENT_MIGRATION_REGRESSION_OK`). O runner `tests/native/run.py` também verifica fallback, override e valor vazio do modelo, além de chave ausente/vazia e delegação dos métodos de compatibilidade, sem imprimir credenciais.
- Suíte Python existente: **31 testes aprovados**.
- Integração isolada: **oito cenários aprovados**, incluindo decisões adaptativas, FINISH, JSON inválido, evidência ausente, falha de catálogo, feed vazio, ACCEPT/REJECT correlacionados aos relatórios corretos e falha de dispatch de revisão. Busca SQL em vetores persistidos também aprovada. Essa suíte simula fontes externas/Operation de IA; a suíte nativa específica acima exercita separadamente a Operation real com somente a resposta do agente simulada.
- Auditoria estática: **40 arquivos obrigatórios**, links relativos, JSON, manifesto de APIs, schemas e sintaxe Python aprovados.

Os testes com respostas simuladas não comprovam a disponibilidade externa do modelo. A migração não realiza chamadas pagas nem substitui o prompt para obter respostas iguais de um modelo probabilístico.

Para reproduzir a regressão específica, em terminal IRIS USER de um contêiner descartável com `GAIA_E2E_ISOLATED=1` e o código instalado:

```objectscript
do ##class(%SYS.Python).Run("import runpy; runpy.run_path('/opt/gaia/tests/native/run.py')")
```

## Referências

- [Class map](CLASS_MAP.md)
- [Contratos](CLASS_CONTRACTS.md)
- [Componente AI Hub](../specification/components/03_AI_HUB.md)
- [Revisão anterior à extração](IRIS_AI_HUB_ARCHITECTURE_REVIEW.md)
- [AI Hub ObjectScript SDK](https://github.com/intersystems-community/ai-hub-eap/blob/master/ObjectScript_SDK_Guide.md)
