. (Join-Path $PSScriptRoot '_runtime.ps1')
Invoke-CodexWithCcRuntime -PythonScript 'run_real_delegate_chain_validation.py' -RemainingArgs $args
