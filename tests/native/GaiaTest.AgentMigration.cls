Class GaiaTest.AgentMigration Extends %RegisteredObject
{
ClassMethod Assert(condition As %Boolean, message As %String)
{
    If 'condition Throw ##class(%Exception.General).%New(message)
}
ClassMethod CleanupSession()
{
    Set id=$Get(^||GaiaAgentTest("sessionId"))
    If id'="" Do ##class(%AI.Agent.Session).%DeleteId(id)
    Kill ^||GaiaAgentTest("sessionId")
}
ClassMethod Run() As %Status
{
    Kill ^||GaiaAgentTest
    Set resultStatus=1
    Try {
        // Compare the original programmatic configuration with the extracted class.
        Set settings={"api_key":(##class(Gaia.AI.DiscoveryAgent).ApiKey())}
        Set provider=##class(%AI.Provider).Create("openai",settings)
        Set baseline=##class(%AI.Agent).%New(provider)
        Set baseline.Model=##class(Gaia.Interop.Operations.AIHubOperation).Model()
        Set baseline.SystemPrompt=##class(Gaia.Interop.Operations.AIHubOperation).Prompt(),baseline.MaxIterations=1
        Set actual=##class(Gaia.Interop.Operations.AIHubOperation).CreateAgent()
        Do ..Assert(actual.%ClassName(1)="Gaia.AI.DiscoveryAgent","Wrong agent class")
        Do ..Assert(actual.Provider.Name=baseline.Provider.Name,"Provider changed")
        Do ..Assert(actual.Model=baseline.Model,"Model changed")
        Do ..Assert(actual.SystemPrompt=baseline.SystemPrompt,"Instructions changed")
        Do ..Assert(actual.MaxIterations=baseline.MaxIterations,"Iteration limit changed")
        Do ..Assert(actual.ToolManager.%Discover().%ToJSON()=baseline.ToolManager.%Discover().%ToJSON(),"Tools changed")
        Set injected=##class(Gaia.AI.DiscoveryAgent).%New(provider)
        Do ..Assert(injected.Provider=provider,"Inherited provider injection changed")

        // Exercise the real Operation and Python validation, mocking only Chat.
        Set op=##class(GaiaTest.AgentMigrationOperation).%New("AIHubOperation")
        Set request=##class(Gaia.Interop.Messages.DiscoveryRequest).%New()
        Set request.RunId="isolated-agent-migration",request.Kind="AGENT_DECIDE",request.CorrelationId="isolated-correlation"
        Set request.PayloadJSON="{""current"":{""actionsDone"":[],""decisionHistory"":[],""catalogs"":{},""finkImages"":{}}}"
        Set ^||GaiaAgentTest("reply")="{""hypothesis"":""Isolated fixture"",""alternative"":null,""next_action"":""CHECK_GAIA"",""question"":""Stellar context?"",""reason"":""Isolated fixture"",""assessment"":null}"
        Set sc=op.Handle(request,.response)
        Do ..Assert('$SYSTEM.Status.IsError(sc),"Operation status changed")
        Set result=##class(%DynamicObject).%FromJSON(response.PayloadJSON)
        Do ..Assert(result.current.%Get("next_action")="CHECK_GAIA","Catalog routing changed")
        Do ..Assert(result.current.decisionHistory.%Size()=1,"Decision history changed")
        Do ..Assert(response.RunId=request.RunId,"Run correlation changed")
        Do ..Assert(response.CorrelationId=request.CorrelationId,"Message correlation changed")
        Set context=##class(%DynamicObject).%FromJSON(^||GaiaAgentTest("input"))
        Do ..Assert(context.remainingDecisions=4,"Decision budget changed")
        Do ..Assert(context.remainingCatalogBudget=3,"Catalog budget changed")
        Do ..CleanupSession()

        Set ^||GaiaAgentTest("reply")="{""hypothesis"":""Isolated fixture"",""alternative"":null,""next_action"":""FINISH"",""question"":"""",""reason"":""Insufficient evidence"",""assessment"":""INCONCLUSIVE""}"
        Set sc=op.Handle(request,.response)
        Set result=##class(%DynamicObject).%FromJSON(response.PayloadJSON)
        Do ..Assert(result.current.assessment="INCONCLUSIVE","Final assessment changed")
        Do ..CleanupSession()

        Set ^||GaiaAgentTest("reply")="invalid-json"
        Set sc=op.Handle(request,.response)
        Set result=##class(%DynamicObject).%FromJSON(response.PayloadJSON)
        Do ..Assert(result.current.failureCode="INVALID_AI_HUB_DECISION","Validation failure changed")
        Do ..CleanupSession()

        Set ^||GaiaAgentTest("failChat")=1
        Set sc=op.Handle(request,.response)
        Set result=##class(%DynamicObject).%FromJSON(response.PayloadJSON)
        Do ..Assert(response.Status="ERROR","Chat error status changed")
        Do ..Assert(result.current.failureStage="AI_HUB_CHAT","Chat failure stage changed")
        Do ..Assert(result.current.assessment="INCONCLUSIVE","Chat fallback changed")
        Do ..CleanupSession()
        Kill ^||GaiaAgentTest("failChat")

        Set ^||GaiaAgentTest("failProvider")=1
        Set sc=op.Handle(request,.response)
        Set result=##class(%DynamicObject).%FromJSON(response.PayloadJSON)
        Do ..Assert(response.Status="ERROR","Provider error status changed")
        Do ..Assert(result.current.failureStage="AI_HUB_PROVIDER","Provider failure stage changed")
        Kill ^||GaiaAgentTest("failProvider")

        Set request.Kind="START_RUN"
        Set sc=op.Handle(request,.response)
        Do ..Assert(response.ErrorCode="INVALID_REQUEST_KIND","Request discriminator changed")
        Kill ^||GaiaAgentTest
        Write "AGENT_MIGRATION_REGRESSION_OK",!
    } Catch ex {
        Do ..CleanupSession()
        Kill ^||GaiaAgentTest
        Set resultStatus=ex.AsStatus()
    }
    Quit resultStatus
}
}
