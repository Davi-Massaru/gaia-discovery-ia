Class Gaia.Interop.Operations.FinkOperation Extends Ens.BusinessOperation
{
Parameter ADAPTER = "EnsLib.HTTP.OutboundAdapter";
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
    from gaia.runtime import fink
    fink(self, request, response)
    return 1
}
Method OnInit() As %Status
{
    Set sc=##super()
    If $SYSTEM.Status.IsError(sc) { Quit sc }
    Try { Do ..RefreshTags() } Catch ex { Set sc=1 }
    Quit 1
}
Method RefreshTags() As %Status [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.runtime import refresh_tags
    return refresh_tags(self)
}
Method Fetch(path As %String, body As %String = "") As %Net.HttpResponse
{
    If (path'="/tags")&&(path'="/sources")&&(path'="/cutouts") { Throw ##class(%Exception.General).%New("Invalid Fink path") }
    Set req=##class(%Net.HttpRequest).%New()
    Set req.ContentType="application/json",req.Timeout=30
    If body'="" { Do req.EntityBody.Write(body) }
    Set method=$Select(body="":"GET",1:"POST")
    Set sc=..Adapter.SendFormDataURL("https://api.lsst.fink-portal.org/api/v1"_path,.resp,method,req)
    If $SYSTEM.Status.IsError(sc) { Throw ##class(%Exception.StatusException).CreateFromStatus(sc) }
    Quit resp
}
XData MessageMap
{
<MapItems><MapItem MessageType="Gaia.Interop.Messages.DiscoveryRequest"><Method>Handle</Method></MapItem></MapItems>
}
}
