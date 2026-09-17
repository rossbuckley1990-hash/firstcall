# Resend — Send Email

Send an email with the Resend HTTP API.

Endpoint:

POST https://api.resend.com/emails

Authentication:

Authorization: Bearer $RESEND_API_KEY

Content-Type:

application/json

Example request body:

{
  "from": "FIRSTCALL <onboarding@resend.dev>",
  "to": ["delivered@resend.dev"],
  "subject": "Hello World",
  "html": "<strong>It works</strong>"
}

The API key is available at runtime in the RESEND_API_KEY environment
variable.

A successful request returns JSON containing the created email id.

For this test, use onboarding@resend.dev as the sender and
delivered@resend.dev as the recipient.
