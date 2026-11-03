"""A least-privilege temporary reviewer only in the disposable fixture container."""
import os
import iris
if os.environ.get('GAIA_E2E_ISOLATED')!='1':raise RuntimeError('Disposable-container guard required')
users=iris.cls('Security.Users')
if not users.Exists('GaiaE2EReviewer'):
    status=users.Create('GaiaE2EReviewer','%DB_USER,%EnsRole_Operator,GaiaWSGI,GaiaWorkflowUser',os.environ['GAIA_E2E_PASSWORD'],
                        'Disposable fixture reviewer','USER','','',0,1)
    if status!=1:raise RuntimeError('Could not create scoped fixture reviewer')
print('SCOPED_FIXTURE_REVIEWER_READY')
