# Salem AI backend (pending)

A small backend that powers the "Talk to Salem" live-AI feature in lesson 2: holds the AI API
key server-side, takes `{ question, lessonId, context }`, returns `{ reply }` in short, safe,
in-character Omani-Arabic Salem dialogue for a Grade-1 child.

Built via Replit (app "salem-ai-backend"): https://replit.com/@balrisi78/KnottyDopeyInsurance

**Status: not live.** Publishing failed with a Replit account restriction:
> Usage-based services are unavailable for this account. Please contact support@replit.com for assistance.

To finish this:
1. Resolve the restriction with Replit support (support@replit.com) or an org admin.
2. Publish the app from Replit (or ask me to retry `publish_app`).
3. Update `SALEM_BRAIN_URL` in `public/vr/lesson-02-young-animals/index.html` to the published
   URL (`https://<app>.replit.app/api/salem-chat`) and push.

Until then, "Talk to Salem" falls back gracefully to a recorded line — the rest of the lesson is
unaffected.
