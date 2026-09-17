# Acme Events API

API base URL: `http://127.0.0.1:8765`

Authentication: send the API key available in the `ACME_API_KEY` environment variable using the HTTP header `Authorization: Bearer <API_KEY>`.

Create an event by sending a POST request to:

`/v1/events`

The JSON request body contains a `name` field.

A successful request returns an event object containing its ID.
