Class Gaia.Interop.Operations.AIHubOperation Extends Ens.BusinessOperation
{
Parameter INVOCATION = "Queue";
Method Handle(pRequest As Gaia.Interop.Messages.DiscoveryRequest, Output pResponse As Gaia.Interop.Messages.DiscoveryResponse) As %Status
{
    Set pResponse=##class(Gaia.Interop.Messages.DiscoveryResponse).%New()
    Set pResponse.RunId=pRequest.RunId,pResponse.Kind=pRequest.Kind,pResponse.CorrelationId=pRequest.CorrelationId
    If pRequest.Kind'="AGENT_DECIDE" {
        Set pResponse.Status="ERROR",pResponse.ErrorCode="INVALID_REQUEST_KIND"
        Set pResponse.PayloadJSON=..Failed(pRequest.PayloadJSON,"INVALID_REQUEST_KIND")
        Quit 1
    }
    Try {
        Set stage="AI_HUB_PROVIDER"
        Set agent=..CreateAgent()
        Set session=agent.CreateSession()
        Set stage="AI_HUB_CHAT"
        Set answer=agent.Chat(session,..Context(pRequest.PayloadJSON))
        Set pResponse.PayloadJSON=..Apply(pRequest.PayloadJSON,answer.Content)
    } Catch ex {
        Set pResponse.Status="ERROR"
        Set pResponse.PayloadJSON=..Failed(pRequest.PayloadJSON,"AI_HUB_UNAVAILABLE",ex.DisplayString(),stage)
        Set pResponse.ErrorCode=..FailureCode(pResponse.PayloadJSON)
    }
    Quit 1
}
ClassMethod CreateAgent() As Gaia.AI.DiscoveryAgent
{
    Quit ##class(Gaia.AI.DiscoveryAgent).%New()
}
/// Compatibility entry points for existing diagnostic callers.
ClassMethod ApiKey() As %String [ Language = python ]
{
    import iris
    return iris.cls("Gaia.AI.DiscoveryAgent").ApiKey()
}
ClassMethod Model() As %String [ Language = python ]
{
    import iris
    return iris.cls("Gaia.AI.DiscoveryAgent").ConfiguredModel()
}
ClassMethod Prompt() As %String [ Language = python ]
{
    import iris
    return iris.cls("Gaia.AI.DiscoveryAgent").Instructions()
}
ClassMethod Context(state As %String) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    from gaia.runtime import agent_prompt
    return agent_prompt(json.loads(state))
}
ClassMethod Apply(state As %String, raw As %String) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.runtime import apply_agent
    return apply_agent(state, raw)
}
ClassMethod Failed(state As %String, code As %String = "AI_HUB_UNAVAILABLE", detail As %String = "", stage As %String = "AI_HUB") As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    from gaia.runtime import failure, dumps
    from gaia.diagnostics import diagnostic
    data=json.loads(state)
    safe_code, details = diagnostic(detail, code)
    failure(data["current"], safe_code, stage, details)
    return dumps(data)
}
ClassMethod FailureCode(state As %String) As %String [ Language = python ]
{
    import json
    return json.loads(state)["current"]["failureCode"]
}
XData MessageMap
{
<MapItems><MapItem MessageType="Gaia.Interop.Messages.DiscoveryRequest"><Method>Handle</Method></MapItem></MapItems>
}
}
