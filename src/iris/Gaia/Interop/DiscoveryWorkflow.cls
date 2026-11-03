Class Gaia.Interop.DiscoveryWorkflow Extends Ens.BusinessProcessBPL
{
ClassMethod Total(state As %String) As %Integer [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    return len(json.loads(state).get("objects", []))
}
ClassMethod ObjectRequest(state As %String, index As %Integer) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.runtime import object_request
    return object_request(state, index)
}
ClassMethod Action(state As %String) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    return json.loads(state)["current"].get("next_action", "FINISH")
}
ClassMethod Save(state As %String, sessionId As %String) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    from gaia.store import save_report
    return json.dumps(save_report(json.loads(state), sessionId))
}
ClassMethod IsCandidate(state As %String) As %Boolean [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    return json.loads(state)["current"].get("assessment") == "REVIEW_CANDIDATE"
}
ClassMethod ReportId(state As %String) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    return json.loads(state)["reportId"]
}
ClassMethod FinishRun(state As %String) As %Status [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.runtime import finish_run
    return finish_run(state)
}
ClassMethod Review(response As EnsLib.Workflow.TaskResponse) As %Status
{
    // Access native Workflow fields before crossing the Embedded Python bridge.
    Set reportId=$Piece(response.%Subject," ",3),action=response.%Action
    Quit ..ApplyReview(reportId,action)
}
ClassMethod ApplyReview(reportId As %String, action As %String) As %Status [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.store import review
    try:
        return review(reportId, action)
    except Exception as error:
        import traceback
        frames = ','.join(f'{frame.name}:{frame.lineno}' for frame in traceback.extract_tb(error.__traceback__))
        iris.cls('%SYS.System').WriteToConsoleLog('Gaia native review failed: '+type(error).__name__+' '+frames,0,2)
        raise
}
ClassMethod ReviewError(state As %String) As %Status [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    from gaia.store import review
    return review(json.loads(state)["reportId"], "DISPATCH_ERROR")
}
ClassMethod RunError(state As %String) As %Status [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.runtime import run_error
    return run_error(state)
}
XData BPL [ XMLNamespace = "http://www.intersystems.com/bpl" ]
{
<process language="objectscript" request="Gaia.Interop.Messages.DiscoveryRequest" response="Gaia.Interop.Messages.DiscoveryResponse">
<context>
<property name="State" type="%String"><parameters><parameter name="MAXLEN" value="1000000"/></parameters></property>
<property name="Index" type="%Integer" initialexpression="0"/>
<property name="Total" type="%Integer"/>
<property name="ReviewResult" type="%Integer"/>
<property name="HasReviews" type="%Boolean" initialexpression="0"/>
<property name="ReviewCall" type="%String"><parameters><parameter name="MAXLEN" value="100"/></parameters></property>
<property name="ReviewCalls" type="%String"><parameters><parameter name="MAXLEN" value="4000"/></parameters></property>
</context>
<sequence><scope name="RunGuard">
<assign property="context.State" value="request.PayloadJSON"/>
<call name="ListFink" target="FinkOperation" async="0">
<request type="Gaia.Interop.Messages.DiscoveryRequest">
<assign property="callrequest.RunId" value="request.RunId"/>
<assign property="callrequest.Kind" value='"LIST_BY_TAG"'/>
<assign property="callrequest.CorrelationId" value="request.RunId"/>
<assign property="callrequest.PayloadJSON" value="context.State"/>
</request><response type="Gaia.Interop.Messages.DiscoveryResponse">
<assign property="context.State" value="callresponse.PayloadJSON"/>
</response></call>
<assign property="context.Total" value="##class(Gaia.Interop.DiscoveryWorkflow).Total(context.State)"/>
<while condition="context.Index &lt; context.Total">
<assign property="context.State" value="##class(Gaia.Interop.DiscoveryWorkflow).ObjectRequest(context.State,context.Index)"/>
<call name="GetFinkEvidence" target="FinkOperation" async="0">
<request type="Gaia.Interop.Messages.DiscoveryRequest">
<assign property="callrequest.RunId" value="request.RunId"/>
<assign property="callrequest.Kind" value='"GET_SOURCES"'/>
<assign property="callrequest.CorrelationId" value="request.RunId"/>
<assign property="callrequest.PayloadJSON" value="context.State"/>
</request><response type="Gaia.Interop.Messages.DiscoveryResponse">
<assign property="context.State" value="callresponse.PayloadJSON"/>
</response></call>
<while condition='##class(Gaia.Interop.DiscoveryWorkflow).Action(context.State) &apos;= "FINISH"'>
<call name="AgentDecide" target="AIHubOperation" async="0">
<request type="Gaia.Interop.Messages.DiscoveryRequest">
<assign property="callrequest.RunId" value="request.RunId"/>
<assign property="callrequest.Kind" value='"AGENT_DECIDE"'/>
<assign property="callrequest.CorrelationId" value="request.RunId"/>
<assign property="callrequest.PayloadJSON" value="context.State"/>
</request><response type="Gaia.Interop.Messages.DiscoveryResponse">
<assign property="context.State" value="callresponse.PayloadJSON"/>
</response></call>
<switch name="AdaptiveScientificRouting">
<case condition='##class(Gaia.Interop.DiscoveryWorkflow).Action(context.State) = "CHECK_GAIA"'><call name="CheckGAIA" target="GaiaOperation" async="0">
<request type="Gaia.Interop.Messages.DiscoveryRequest">
<assign property="callrequest.RunId" value="request.RunId"/>
<assign property="callrequest.Kind" value='"CATALOG_QUERY"'/>
<assign property="callrequest.CorrelationId" value="request.RunId"/>
<assign property="callrequest.PayloadJSON" value="context.State"/>
</request><response type="Gaia.Interop.Messages.DiscoveryResponse">
<assign property="context.State" value="callresponse.PayloadJSON"/>
</response></call></case><case condition='##class(Gaia.Interop.DiscoveryWorkflow).Action(context.State) = "CHECK_SIMBAD"'><call name="CheckSIMBAD" target="SimbadOperation" async="0">
<request type="Gaia.Interop.Messages.DiscoveryRequest">
<assign property="callrequest.RunId" value="request.RunId"/>
<assign property="callrequest.Kind" value='"CATALOG_QUERY"'/>
<assign property="callrequest.CorrelationId" value="request.RunId"/>
<assign property="callrequest.PayloadJSON" value="context.State"/>
</request><response type="Gaia.Interop.Messages.DiscoveryResponse">
<assign property="context.State" value="callresponse.PayloadJSON"/>
</response></call></case><case condition='##class(Gaia.Interop.DiscoveryWorkflow).Action(context.State) = "CHECK_IRSA"'><call name="CheckIRSA" target="IrsaOperation" async="0">
<request type="Gaia.Interop.Messages.DiscoveryRequest">
<assign property="callrequest.RunId" value="request.RunId"/>
<assign property="callrequest.Kind" value='"CATALOG_QUERY"'/>
<assign property="callrequest.CorrelationId" value="request.RunId"/>
<assign property="callrequest.PayloadJSON" value="context.State"/>
</request><response type="Gaia.Interop.Messages.DiscoveryResponse">
<assign property="context.State" value="callresponse.PayloadJSON"/>
</response></call></case>
</switch></while>
<assign property="context.State" value="##class(Gaia.Interop.DiscoveryWorkflow).Save(context.State,process.%SessionId)"/>
<if condition="##class(Gaia.Interop.DiscoveryWorkflow).IsCandidate(context.State)"><true>
<assign property="context.ReviewCall" value='"Review_"_##class(Gaia.Interop.DiscoveryWorkflow).ReportId(context.State)'/>
<scope name="ReviewDispatchGuard"><call name="@context.ReviewCall" target="AstronomyReviewer" async="1">
<request type="EnsLib.Workflow.TaskRequest">
<assign property="callrequest.%Subject" value='"Gaia report "_##class(Gaia.Interop.DiscoveryWorkflow).ReportId(context.State)'/>
<assign property="callrequest.%Message" value='"Preliminary candidate for further investigation. Report "_##class(Gaia.Interop.DiscoveryWorkflow).ReportId(context.State)_" at /gaia/#report/"_##class(Gaia.Interop.DiscoveryWorkflow).ReportId(context.State)'/>
<assign property="callrequest.%Actions" value='"ACCEPT,REJECT"'/>
</request><response type="EnsLib.Workflow.TaskResponse">
<assign property="context.ReviewResult" value="##class(Gaia.Interop.DiscoveryWorkflow).Review(callresponse)"/>
</response></call>
<assign property="context.ReviewCalls" value='context.ReviewCalls_$Select(context.ReviewCalls="":"",1:",")_context.ReviewCall'/>
<assign property="context.HasReviews" value="1"/>
<faulthandlers><catchall><code name="ReviewDispatchFailure"><![CDATA[ Do ##class(Gaia.Interop.DiscoveryWorkflow).ReviewError(context.State) ]]></code></catchall></faulthandlers>
</scope>
</true></if>
<assign property="context.Index" value="context.Index+1"/>
</while>
<code name="ScientificCompletion"><![CDATA[ Do ##class(Gaia.Interop.DiscoveryWorkflow).FinishRun(context.State) ]]></code>
<if condition="context.HasReviews"><true><sync name="WaitNativeReviews" type="all" calls="@context.ReviewCalls"/></true></if>
<faulthandlers><catchall><code name="RunFailure"><![CDATA[ Do ##class(Gaia.Interop.DiscoveryWorkflow).RunError(context.State) ]]></code></catchall></faulthandlers>
</scope><reply/>
</sequence></process>
}
}
