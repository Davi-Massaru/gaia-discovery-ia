Class Gaia.Production Extends Ens.Production
{
XData ProductionDefinition
{
<Production Name="Gaia.Production" TestingEnabled="true" LogGeneralTraceEvents="true">
<Description>Sequential adaptive scientific investigations with native AI Hub and Workflow.</Description>
<ActorPoolSize>1</ActorPoolSize>
<Item Name="DiscoveryService" ClassName="Gaia.Interop.DiscoveryService" PoolSize="0" Enabled="true"/>
<Item Name="DiscoveryWorkflow" ClassName="Gaia.Interop.DiscoveryWorkflow" PoolSize="1" Enabled="true"/>
<Item Name="FinkOperation" ClassName="Gaia.Interop.Operations.FinkOperation" PoolSize="1" Enabled="true">
<Setting Target="Adapter" Name="SSLConfig">GaiaTLS</Setting>
<Setting Target="Adapter" Name="ResponseTimeout">30</Setting>
</Item>
<Item Name="AIHubOperation" ClassName="Gaia.Interop.Operations.AIHubOperation" PoolSize="1" Enabled="true"/>
<Item Name="GaiaOperation" ClassName="Gaia.Interop.Operations.GaiaOperation" PoolSize="1" Enabled="true"/>
<Item Name="SimbadOperation" ClassName="Gaia.Interop.Operations.SimbadOperation" PoolSize="1" Enabled="true"/>
<Item Name="IrsaOperation" ClassName="Gaia.Interop.Operations.IrsaOperation" PoolSize="1" Enabled="true"/>
<Item Name="AstronomyReviewer" ClassName="EnsLib.Workflow.Operation" PoolSize="1" Enabled="true">
<Setting Target="Host" Name="AutoCreateRole">1</Setting>
</Item>
</Production>
}
}
