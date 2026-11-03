Class Gaia.Interop.Messages.DiscoveryResponse Extends Ens.Response
{
Property RunId As %String(MAXLEN = 64);
Property Kind As %String(VALUELIST = ",START_RUN,LIST_BY_TAG,GET_SOURCES,GET_CUTOUT,AGENT_DECIDE,CATALOG_QUERY,SAVE_REPORT");
Property CorrelationId As %String(MAXLEN = 200);
Property PayloadJSON As %String(MAXLEN = 1000000);
Property ImageStreamRef As %Stream.GlobalBinary;
Property Status As %String(VALUELIST = ",OK,EMPTY,ERROR") [ InitialExpression = "OK" ];
Property ErrorCode As %String(MAXLEN = 100);
Property ErrorSummary As %String(MAXLEN = 500);
}
