# Deploying the chatbot backend to Railway (Upfront Windows)

This branch (`upfront-deploy`) is deploy-ready: the Procfile and dockerfile both start the
chatbot service (`chatbot_app:app`, FastAPI `POST /chat`), not the legacy Flask quoter.

## One-time setup

1. Sign in at https://railway.app with GitHub (the `dmagal` account that owns this repo).
2. **New Project → Deploy from GitHub repo** → pick `dmagal/ai-estimator`.
3. In the service settings, set **branch: `upfront-deploy`** (Settings → Source).
   Railway auto-detects the Dockerfile; no start-command override needed.
4. **Variables** — add:
   | Variable | Value |
   |---|---|
   | `OPENAI_API_KEY` | a key from YOUR OpenAI account (platform.openai.com → API keys; billing must be enabled) |
   | `CHAT_CUSTOM_HEADER_KEY` | `default-key` (must match the site widget; public by design — the rate limit is the real control) |
   | `RESEND_API_KEY` | optional — without it the bot works but quote emails don't send (customer sees "couldn't generate the quote right now" at the email step). See below. |
   | `OPENAI_MODEL` | optional — defaults to `gpt-5.4-mini` (cheap tier, right for this workload). Set only if that model name doesn't exist on your account (check platform.openai.com/docs/models) or you want to try another. |
5. Settings → Networking → **Generate Domain**. Copy the `https://….up.railway.app` URL.
6. Update the website: in `~/Desktop/active/upfront-windows/site/assets/js/chat.js`,
   set `CHAT_API_URL` to `https://<your-domain>.up.railway.app/chat` and redeploy the site.

## Smoke test

```sh
curl -s -X POST https://<your-domain>.up.railway.app/chat \
  -H 'Content-Type: application/json' -H 'Authorization: Bearer default-key' \
  -d '{"message": "2 casement windows, about 36 x 60, with installation"}'
```
A healthy reply asks follow-up questions or summarizes the project — NOT
"I can't help with that" (that's the kill-switch, which also fires when the
OpenAI key is invalid or out of credit).

## About quote emails (Resend)

Quote emails currently send from `Direct Windows <hello@quote.directwindows.ca>` — a domain
verified in the OLD Resend account. For the new brand, once upfrontwindows.ca is purchased:

1. Create your own free Resend account → verify `quote.upfrontwindows.ca` (add the DKIM/SPF
   records it gives you in Cloudflare DNS).
2. Change the from-address in `quote_emailer/quote_emailer.py` to
   `Upfront Windows <hello@quote.upfrontwindows.ca>`, rebrand
   `quote_emailer/email_template*.html`, and update `UNSUBSCRIBE_PAGE_URL`.
3. Set `RESEND_API_KEY` on the Railway service.

## Notes

- Rate limits (5/min, 100/day per IP) are enforced in `chatbot_app.py` via slowapi.
- CORS allows any origin, so the site works from localhost, *.pages.dev, and the real domain.
- LangSmith tracing is imported but inert unless `LANGSMITH_API_KEY`/`LANGCHAIN_TRACING_V2` are set.
