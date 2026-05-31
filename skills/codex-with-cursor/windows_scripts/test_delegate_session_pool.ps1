. (Join-Path $PSScriptRoot '_runtime.ps1')
Invoke-CodexWithCcRuntime -PythonScript 'test_delegate_session_pool.py' -RemainingArgs $args
