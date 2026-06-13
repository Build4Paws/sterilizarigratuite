"""
sterilizarigratuite — unified API Lambda entry point.

The implementation lives in the `api/` package (config, helpers, models,
public_handlers, admin, reports, router). The AWS handler stays
`lambda_function.lambda_handler` so the function configuration is unchanged.
"""
from api.router import lambda_handler

__all__ = ["lambda_handler"]
