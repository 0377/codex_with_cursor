. (Join-Path $PSScriptRoot '_runtime.ps1')
Invoke-CodexWithCcRuntime -PythonScript 'verify_delegate_chain.py' -RemainingArgs $args
