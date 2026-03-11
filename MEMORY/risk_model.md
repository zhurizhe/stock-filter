# risk_model.md

## Risks
- API credential leakage through committed `.env` files
- rate limits or quota exhaustion during bulk historical pulls
- inconsistent downstream analysis if date ranges and adjustment modes are mixed

## Controls
- keep secrets in `.env`, never in code
- expose narrow CLI scripts with explicit date arguments
- write raw outputs to caller-selected CSV paths for auditability
