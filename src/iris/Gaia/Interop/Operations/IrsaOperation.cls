Class Gaia.Interop.Operations.IrsaOperation Extends Ens.BusinessOperation
{
Parameter ADAPTER = "Gaia.Interop.Adapters.TAPOutboundAdapter";
Parameter INVOCATION = "Queue";
Method Handle(pRequest As Gaia.Interop.Messages.DiscoveryRequest, Output pResponse As Gaia.Interop.Messages.DiscoveryResponse) As %Status
{
    Set pResponse=##class(Gaia.Interop.Messages.DiscoveryResponse).%New()
    Set pResponse.RunId=pRequest.RunId,pResponse.Kind=pRequest.Kind,pResponse.CorrelationId=pRequest.CorrelationId
    Do ..Execute(pRequest,pResponse)
    Quit 1
}
Method Execute(request As Gaia.Interop.Messages.DiscoveryRequest, response As Gaia.Interop.Messages.DiscoveryResponse) As %Status [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.runtime import catalog
    catalog(self, "IRSA", request, response)
    return 1
}
XData MessageMap
{
<MapItems><MapItem MessageType="Gaia.Interop.Messages.DiscoveryRequest"><Method>Handle</Method></MapItem></MapItems>
}
}
