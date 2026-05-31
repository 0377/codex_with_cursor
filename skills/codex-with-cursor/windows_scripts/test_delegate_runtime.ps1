. (Join-Path $PSScriptRoot '_runtime.ps1')
Invoke-CodexWithCcRuntime -PythonScript 'test_delegate_runtime.py' -RemainingArgs $args
