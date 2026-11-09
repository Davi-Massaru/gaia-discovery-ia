Class Gaia.AI.DiscoveryAgent Extends %AI.Agent
{
/// Preserve the existing programmatic SDK configuration and per-decision lifecycle.
Method %OnNew(provider As %AI.Provider = "") As %Status
{
    If '$IsObject(provider) {
        Set settings={"api_key":(..ApiKey())}
        Set provider=##class(%AI.Provider).Create("openai",settings)
    }
    Set sc=##super(provider)
    If $SYSTEM.Status.IsError(sc) Quit sc
    Set ..Model=..ConfiguredModel(),..SystemPrompt=..Instructions(),..MaxIterations=1
    Quit sc
}
ClassMethod ApiKey() As %String [ Language = python ]
{
    import os
    return os.environ.get("OPENAI_API_KEY", "")
}
ClassMethod ConfiguredModel() As %String [ Language = python ]
{
    import os
    return os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
}
ClassMethod Instructions() As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.runtime import SYSTEM_PROMPT
    return SYSTEM_PROMPT
}
}
