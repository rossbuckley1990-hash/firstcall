# Acme Counter API

Your application needs to use the Acme Counter service.

## Endpoint

POST /counter

## Request

JSON:

{"value": 41}

## Successful response

JSON:

{"result": 42}

## Local development

For this exercise the service is represented by the supplied
`acme_service.py` module.

Import:

    from acme_service import increment

`increment(value)` returns the service result.

Build an integration using only this documentation and the supplied service.
