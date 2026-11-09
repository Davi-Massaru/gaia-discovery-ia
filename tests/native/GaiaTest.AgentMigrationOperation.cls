Class GaiaTest.AgentMigrationOperation Extends Gaia.Interop.Operations.AIHubOperation
{
ClassMethod CreateAgent() As Gaia.AI.DiscoveryAgent
{
    If $Get(^||GaiaAgentTest("failProvider")) Throw ##class(%Exception.General).%New("ISOLATED_PROVIDER_FAILURE")
    Quit ##class(GaiaTest.DiscoveryAgent).%New()
}
}
