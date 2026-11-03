Class Gaia.Interop.DiscoveryService Extends Ens.BusinessService
{
Parameter ADAPTER = "";
Method OnProcessInput(pInput As Gaia.Interop.Messages.DiscoveryRequest, Output pOutput As Gaia.Interop.Messages.DiscoveryResponse) As %Status
{
    Set pOutput=##class(Gaia.Interop.Messages.DiscoveryResponse).%New()
    Set pOutput.RunId=pInput.RunId
    Quit ..SendRequestAsync("DiscoveryWorkflow",pInput)
}
ClassMethod StartRun(tag As %String, count As %Integer = 5) As %String
{
    Set runId=..CreateRun(tag,count)
    Set sc=##class(Ens.Director).CreateBusinessService("DiscoveryService",.service)
    If $SYSTEM.Status.IsError(sc) { Do ..FailRun(runId) Throw ##class(%Exception.StatusException).CreateFromStatus(sc) }
    Set req=##class(Gaia.Interop.Messages.DiscoveryRequest).%New()
    Set req.RunId=runId,req.Kind="START_RUN",req.CorrelationId=runId
    Set payload={"runId":(runId),"tag":(tag),"count":(count)}
    Set req.PayloadJSON=payload.%ToJSON()
    Set sc=service.ProcessInput(req)
    If $SYSTEM.Status.IsError(sc) { Do ..FailRun(runId) Throw ##class(%Exception.StatusException).CreateFromStatus(sc) }
    Quit runId
}
ClassMethod CreateRun(tag As %String, count As %Integer) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.store import new_run, validate_tag
    validate_tag(tag)
    return new_run(tag, count)
}
ClassMethod FailRun(runId As %String) As %Status [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.store import run_update
    run_update(runId, status="FAILED", error="DISPATCH_FAILED")
    return 1
}
ClassMethod Configure(root As %String = "/opt/gaia") As %Status
{
    Set gaiaNamespace=$Namespace
    New $Namespace
    Set $Namespace="%SYS"
    If '##class(Security.Roles).Exists("GaiaWSGI") {
        Set sc=##class(Security.Roles).Create("GaiaWSGI","Native Embedded Python for Gaia WSGI","%Service_EmbeddedPython:U")
        If $SYSTEM.Status.IsError(sc) { Quit sc }
    }
    If '##class(Security.Roles).Exists("GaiaWorkflowUser") {
        Set sc=##class(Security.Roles).Create("GaiaWorkflowUser","Use native Workflow User Portal","%DeepSee_Portal:U")
        If $SYSTEM.Status.IsError(sc) { Quit sc }
    }
    Set tls("Enabled")=1,tls("VerifyPeer")=2,tls("CAFile")="/etc/ssl/certs/ca-certificates.crt"
    If ##class(Security.SSLConfigs).Exists("GaiaTLS") { Set sc=##class(Security.SSLConfigs).Modify("GaiaTLS",.tls) } Else { Set sc=##class(Security.SSLConfigs).Create("GaiaTLS",.tls) }
    If $SYSTEM.Status.IsError(sc) { Quit sc }
    Set props("NameSpace")=gaiaNamespace,props("Enabled")=1,props("DispatchClass")="%SYS.Python.WSGI"
    Set props("WSGIAppName")="app",props("WSGICallable")="app",props("WSGIAppLocation")=root_"/backend",props("WSGIType")=1
    Set props("AutheEnabled")=32
    If ##class(Security.Applications).Exists("/gaia") { Set sc=##class(Security.Applications).Modify("/gaia",.props) } Else { Set sc=##class(Security.Applications).Create("/gaia",.props) }
    If $SYSTEM.Status.IsError(sc) { Quit sc }
    // Workflow Inbox is served by the built-in User Portal, not the WSGI app.
    Set portalApp="/csp/"_$ZConvert(gaiaNamespace,"L")
    Set portal("NameSpace")=gaiaNamespace,portal("CSPZENEnabled")=1,portal("DeepSeeEnabled")=1,portal("AutheEnabled")=32
    If ##class(Security.Applications).Exists(portalApp) { Set sc=##class(Security.Applications).Modify(portalApp,.portal) } Else { Set sc=##class(Security.Applications).Create(portalApp,.portal) }
    If $SYSTEM.Status.IsError(sc) { Quit sc }
    Set $Namespace=gaiaNamespace
    Set ^GaiaConfig("home")=root
    Set stmt=##class(%SQL.Statement).%New()
    Set sc=stmt.%Prepare("GRANT SELECT ON Gaia_Data.DiscoveryReport TO GaiaWSGI")
    If $SYSTEM.Status.IsError(sc) { Quit sc }
    Set result=stmt.%Execute()
    If result.%SQLCODE<0 { Quit 0 }
    If '##class(EnsLib.Workflow.RoleDefinition).%ExistsId("AstronomyReviewer") { Set sc=##class(EnsLib.Workflow.RoleDefinition).CreateRole("AstronomyReviewer") }
    Set reviewer=$SYSTEM.Util.GetEnviron("GAIA_REVIEWER")
    If reviewer="" { Set reviewer="_SYSTEM" }
    If '##class(EnsLib.Workflow.UserDefinition).%ExistsId(reviewer) { Set sc=##class(EnsLib.Workflow.UserDefinition).CreateUser(reviewer,"Astronomy reviewer") }
    Set stmt=##class(%SQL.Statement).%New()
    Set sc=stmt.%Prepare("SELECT COUNT(*) AS MembershipCount FROM EnsLib_Workflow.RoleMembership WHERE RoleName=? AND UserName=?")
    If $SYSTEM.Status.IsError(sc) { Quit sc }
    Set result=stmt.%Execute("AstronomyReviewer",reviewer)
    If result.%SQLCODE<0 { Quit 0 }
    Do result.%Next()
    If result.%Get("MembershipCount")=0 {
        Set sc=##class(EnsLib.Workflow.RoleDefinition).AddUserToRole("AstronomyReviewer",reviewer)
        If $SYSTEM.Status.IsError(sc) { Quit sc }
    }
    Do ##class(Ens.Director).SetAutoStart("Gaia.Production")
    Quit 1
}
}
