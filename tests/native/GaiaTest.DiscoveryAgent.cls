/// Deterministic model boundary; loaded only in a disposable test container.
Class GaiaTest.DiscoveryAgent Extends Gaia.AI.DiscoveryAgent
{
Method Chat(session As %AI.Agent.Session, input As %String, feedback As %RegisteredObject = "") As %AI.LLM.Response
{
    Set ^||GaiaAgentTest("input")=input
    Set ^||GaiaAgentTest("sessionId")=session.%Id()
    If $Get(^||GaiaAgentTest("failChat")) Throw ##class(%Exception.General).%New("ISOLATED_CHAT_FAILURE")
    Set answer=##class(%AI.LLM.Response).%New()
    Set answer.Content=$Get(^||GaiaAgentTest("reply"))
    Quit answer
}
}
