# Acme Events API

The API base URL is `http://127.0.0.1:8765`.

Create an event by sending a POST request to `/v1/events`.

Requests must include `Authorization: Bearer FIRSTCALL_LOCAL_TOKEN` and `Content-Type: application/json`.

The JSON request body contains a `name` field.

A successful request returns HTTP 201 and an event object containing its ID.
