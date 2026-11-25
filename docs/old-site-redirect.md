# Retiring the old address (fxbot-ochre.vercel.app)

The site moved to https://fx-bot-vert.vercel.app on 25 Nov 2026. The old Vercel
project lives in Ore's **old** Vercel account (Claude's Vercel connector only sees
the new one), so these steps are Ore's.

Status on 25 Nov 2026: the old address answers `402 DEPLOYMENT_DISABLED`, so it is
not running the app. But it still holds the database keys, may still be linked to
this GitHub repo (a push to `main` could redeploy the full app there), and old
email links (practice, `/p/unsubscribe/<token>`) now hit a dead page.

## Step 1 (do this whichever option you pick)
Old Vercel account -> old project -> Settings -> Environment Variables:
**delete every variable** (SUPABASE_URL, SUPABASE_SECRET_KEY, SITE_PASSWORD,
TWELVEDATA_API_KEY, SENDBYTE_*). Without them the old project cannot reach the
database even if it comes back to life.

## Option A: delete (simplest, old links stop working)
Settings -> General -> Delete Project. Old unsubscribe links then show a Vercel
404; people can still unsubscribe from any newer email.

## Option B: redirect (recommended, old links keep working)
Same old project:
1. Settings -> Build and Deployment -> Root Directory: `redirect-old-site`
   (Framework preset: Other; no build command).
2. Deployments -> Redeploy the latest `main` (or push any commit).

`redirect-old-site/vercel.json` sends every path, with its query string, to the
same path on the new site with a 301. It has no code and needs no variables.

## Check (Claude can run this)
```
curl -sI https://fxbot-ochre.vercel.app/api/health          # 301 -> new site (B) or 404 (A)
curl -sI https://fxbot-ochre.vercel.app/p/unsubscribe/abc   # B: 301 to fx-bot-vert.../p/unsubscribe/abc
```
