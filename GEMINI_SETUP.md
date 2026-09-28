# Getting a Gemini API key + understanding pricing

TalentMatch AI uses Google's Gemini API for two things: reading/extracting
structured data from resumes & Naukri profiles, and answering chatbot
questions. This guide covers getting a key and what it costs.

> Google updates Gemini's model line-up and prices often (there were four
> new Flash model versions between roughly mid-2025 and late-2026 alone), so
> treat the numbers below as a September 2026 snapshot, not a permanent
> price list. Before relying on a number for budgeting, double check
> **[ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)**.

## 1. Create an API key (2 minutes, free)

1. Go to **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**
   and sign in with any Google account.
2. Click **Create API key** (choose "Create key in new project" if asked).
3. Copy the key it gives you (a long string starting with `AIza...`).
4. Open `backend/.env` in this project (copy it from `backend/.env.example`
   first if it doesn't exist yet) and paste it in:
   ```
   GEMINI_API_KEY=AIza...your key here...
   ```
5. Save the file and (re)start the app.

No credit card is required to get a key or to use the free tier.

## 2. Free tier vs. paid tier ("usage tiers", not subscription plans)

There's no Basic/Pro/Business "plan" to pick for the Gemini **API** (that's
a different product - Google's Gemini app subscriptions - and isn't what
this app uses). What actually exists is a ladder of **usage tiers**:

| Tier | How you get there | What changes |
|---|---|---|
| **Free** | Default, the moment you create a key | No cost, but low rate limits - roughly 10-15 requests/minute and 250-1,000 requests/**day** depending on the model |
| **Tier 1** | Link a billing account (credit card) to the project in AI Studio - takes effect instantly | Rate limits jump enormously (~300 requests/minute), you're billed per token used, default monthly cap of $250 (you can set your own lower cap) |
| **Tier 2 / 3** | Automatic, once your account has enough spend/payment history | Even higher limits - not needed for this app's scale |

Solo use (a handful of uploads a day, a few chatbot questions) usually fits
inside the free tier's daily request quota. **5 users sharing this app does
not** - see the sizing section below.

### For 5 users, <1,000 uploads/month, <100 chatbot queries/day

Rough math: ~100 queries/day × 2 Gemini calls each (embed the question +
generate the answer) is already ~200 requests/day - more than the free
tier's ~250/day ceiling for Gemini 2.5 Flash on its own, before counting any
uploads or multiple users hitting it in the same minute. **You should enable
billing and move to Tier 1** - it's the only "upgrade" that exists, it's
pay-as-you-go (no monthly fee just for having it), and at this volume it's
cheap:

- Extraction (~1,500 upload calls/month on Flash-Lite): **~$0.70/month**
- Chat (~3,000 queries/month on Flash): **~$5/month**
- Embeddings (~1,000 calls/month, background indexing): **well under $1/month**
- **Total: roughly $6-10/month** for the whole 5-person team at your stated ceiling.

### Activation steps (Tier 1)

1. Go to **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**,
   select the project your key belongs to.
2. Click **Set up Billing** (or, in the left sidebar, **Billing**) and link
   an existing Google Cloud Billing account, or create one - just needs a
   payment method, like any Google Cloud service.
3. Optional but recommended: in the same Billing panel, set a **monthly
   spend cap** (e.g. $15-20) so costs can never run away even if usage
   spikes far beyond your estimate.
4. That's it - no redeploy, no key rotation. Your existing `GEMINI_API_KEY`
   automatically gets the higher limits within minutes.
5. Confirm it took effect at **[aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit)**
   (it will show "Tier 1" and the new per-model limits).

No code or `.env` changes are needed to move tiers - tier is a property of
the billing account behind your key, not something you configure in the app.

## 3. What this app actually uses, and roughly what it costs

Two Gemini calls happen in this app:

- **Extraction** (when you upload a resume/profile): reads one document
  (~1,000-3,000 tokens) and returns structured JSON (~500-800 tokens).
- **Chat** (when you ask the chatbot a question): sends a handful of
  retrieved candidate snippets as context (~1,500-3,000 tokens) plus your
  question, and gets back an answer (~200-500 tokens).
- **Embeddings** (automatic, in the background, on every add/edit/upload):
  a few hundred tokens per candidate to keep the chatbot's search index
  up to date.

For a database of a few hundred candidates with everyday recruiter usage
(uploading new profiles as they come in, asking the chatbot a few dozen
questions a day), total volume is on the order of a few hundred thousand
tokens a month - **a few cents to low single-digit dollars a month** on the
default model below, and likely **free** if you stay on the free tier.

### Which model for which job (already the app's default)

The app uses **two different models for two different jobs**, set separately
in `backend/.env`:

| Job | Env variable | Default model | Why |
|---|---|---|---|
| **Extraction** (parsing every uploaded resume/profile) | `GEMINI_EXTRACTION_MODEL` | `gemini-2.5-flash-lite` | Runs on every upload - highest volume, purely mechanical (read a document, fill a form). The cheapest model is accurate enough and keeps bulk-upload cost near zero. |
| **Chat** (answering recruiter questions) | `GEMINI_CHAT_MODEL` | `gemini-2.5-flash` | Lower volume, but answer quality (comparing candidates, reasoning about fit) matters more here, so the fuller Flash model is worth the extra cost. |
| **Search/embeddings** (indexing candidates for the chatbot) | `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Same job either way - no quality/cost tradeoff to make. |

If cost ever matters more than answer quality, you can drop `GEMINI_CHAT_MODEL`
to `gemini-2.5-flash-lite` too. If you want noticeably better chat reasoning
and don't mind paying more, try `gemini-2.5-pro`. Check
**[ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models)**
for the current full list, since Google adds new versions regularly.

### Pricing snapshot (September 2026, paid tier, per 1 million tokens)

| Model | Input | Output | Notes |
|---|---|---|---|
| **Gemini 2.5 Flash-Lite** | ~$0.10 | ~$0.40 | Cheapest stable option; good enough for straightforward extraction |
| **Gemini 2.5 Flash** (this app's default) | ~$0.30 | ~$2.50 | Best all-round quality/cost balance |
| **Gemini 2.5 Pro** | ~$1.25 (≤200k) | ~$10.00 (≤200k) | Overkill for this use case, but available |
| **Gemini 3.5/3.6/3.7/3.8 Flash** (newer, evolving fast) | often discounted/free through introductory periods, then roughly $0.75-1.50 | roughly $3.75-9.00 | Newest generation as of late 2026 - check current status/pricing before switching |
| **Gemini embedding model** (`gemini-embedding-001`, used for the chatbot's search index) | low cost per 1M tokens (well under $0.20 typically) | - | Only input tokens are billed for embeddings |

*(Rounded, paid-tier, standard-context pricing. Free-tier usage within rate
limits is $0. Source: Google's official pricing page and independent Gemini
pricing trackers, September 2026 - see links at the bottom of this file.)*

### If you want to change models

Open `backend/.env` and edit these lines, then restart the app - that's the
entire "integration," since every Gemini call in the code (`backend/app/gemini_client.py`)
reads the model name from config rather than having it hardcoded:

```
GEMINI_EXTRACTION_MODEL=gemini-2.5-flash-lite
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Swap in any current model ID from the models page - no other code changes
needed.

## 4. Monitoring usage & cost

- See real-time usage and set budget alerts at
  [aistudio.google.com](https://aistudio.google.com) (top-right, your
  project) or in the linked Google Cloud project's **Billing** section.
- If you ever want to hard-stop spending, you can delete the API key or
  disable billing on the Cloud project - the app will simply show a
  friendly "couldn't reach Gemini" message instead of crashing.

---

**Sources** (checked September 2026 - re-check before budgeting a large
deployment, since this space moves quickly):
- [Gemini API pricing - Google AI for Developers](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API models - Google AI for Developers](https://ai.google.dev/gemini-api/docs/models)
- [Gemini API rate limits - Google AI for Developers](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Giving you more transparency and control over your Gemini API costs - Google](https://blog.google/innovation-and-ai/technology/developers-tools/more-control-over-gemini-api-costs/)
- [Gemini API Pricing (September 2026) - BenchLM](https://benchlm.ai/google/api-pricing)
- [Gemini pricing in 2026 - CloudZero](https://www.cloudzero.com/blog/gemini-pricing/)
- [Gemini API Free Tier Rate Limits 2026 - AI Free API](https://www.aifreeapi.com/en/posts/gemini-api-free-tier-rate-limits)

Exact RPM/TPM/RPD numbers per model are only officially published live in
your own **[AI Studio rate-limit dashboard](https://aistudio.google.com/rate-limit)**
(Google's docs point there rather than publishing a static table) - the
numbers above are third-party-tracked approximations, good enough to plan
around but worth a glance at your dashboard once you're live.
