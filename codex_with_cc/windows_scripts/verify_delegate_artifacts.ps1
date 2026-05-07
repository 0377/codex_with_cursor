. (Join-Path $PSScriptRoot '_runtime.ps1')
Invoke-CodexWithCcRuntime -PythonScript 'verify_delegate_artifacts.py' -RemainingArgs $args
