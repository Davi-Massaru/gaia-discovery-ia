"""Install ONLY test doubles in a disposable IRIS container."""
import os
import sys
from pathlib import Path
import iris

if os.environ.get('GAIA_E2E_ISOLATED')!='1':
    raise RuntimeError('Requires explicit GAIA_E2E_ISOLATED=1 on a disposable container')
sys.path.insert(0,'/opt/gaia/backend')
from gaia.store import check_status
check_status(iris.cls('Ens.Director').StopProduction(10,1))
folder=Path('/tmp/gaia-e2e-classes')
folder.mkdir(exist_ok=True)
for name,base,function in [('Fink','FinkOperation','fink'),('AIHub','AIHubOperation','agent'),
                           ('Gaia','GaiaOperation','tap'),('Simbad','SimbadOperation','tap'),('Irsa','IrsaOperation','tap')]:
    code='SIMBAD' if name=='Simbad' else name.upper()
    invocation=f'fixtures.{function}(request,response)' if function!='tap' else f'fixtures.tap("{code}",request,response)'
    body=f'''Class GaiaTest.{name}Operation Extends Gaia.Interop.Operations.{base}
{{
Method Handle(pRequest As Gaia.Interop.Messages.DiscoveryRequest, Output pResponse As Gaia.Interop.Messages.DiscoveryResponse) As %Status
{{
 Set pResponse=##class(Gaia.Interop.Messages.DiscoveryResponse).%New()
 Set pResponse.RunId=pRequest.RunId,pResponse.Kind=pRequest.Kind,pResponse.CorrelationId=pRequest.CorrelationId
 Do ..Fixture(pRequest,pResponse)
 Quit 1
}}
Method Fixture(request As Gaia.Interop.Messages.DiscoveryRequest, response As Gaia.Interop.Messages.DiscoveryResponse) As %Status [ Language = python ]
{{
    import sys,iris
    if iris.gref("^GaiaConfig").get(["testFixtures"])!=1:
        raise RuntimeError("Test fixtures are disabled")
    sys.path.insert(0,"/opt/gaia/backend")
    sys.path.insert(0,"/opt/gaia/tests/e2e")
    import fixtures
    {invocation}
    return 1
}}
}}
'''
    if name=='Fink':body=body.replace('Method Handle', 'Method OnInit() As %Status { Quit 1 }\nMethod Handle')
    (folder/f'GaiaTest.{name}Operation.cls').write_text(body)
check_status(iris.cls('%SYSTEM.OBJ').LoadDir(str(folder),'ck'))
production=iris.cls('Ens.Config.Production')._OpenId('Gaia.Production')
for index in range(1,production.Items.Count()+1):
    item=production.Items.GetAt(index)
    if item.Name in ['FinkOperation','AIHubOperation','GaiaOperation','SimbadOperation','IrsaOperation']:
        item.ClassName='GaiaTest.'+item.Name
check_status(production._Save())
check_status(production.SaveToClass())
iris.gref('^GaiaConfig')['testFixtures']=1
check_status(iris.cls('Ens.Director').StartProduction('Gaia.Production'))
print('ISOLATED_FIXTURE_PRODUCTION_READY',flush=True)
