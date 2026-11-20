# Putting the website online (about 20 minutes)

You need: your GitHub login, Vercel login, Supabase login, and your Twelve Data key.
**Never paste a key or password into GitHub, a chat or an email.** They only go in the Vercel and Supabase dashboards.

## 1. Database (Supabase)
1. Go to supabase.com → organization **Betrix** → **New project**.
   Name `fx-bot`, region **West EU (Ireland)**, Free plan. Choose a database password and keep it in a password manager (the website doesn't need it).
2. Wait until the project says it's ready (1–2 minutes), then tell Claude "the fx-bot project exists". Claude creates the tables.
   (Or do it yourself: **SQL Editor** → New query → paste all of `db/migrations/001_init.sql` → Run.)
3. **Project Settings → API Keys.** You need two values for step 2:
   - the **Project URL** (looks like `https://abcd1234.supabase.co`)
   - the **secret** key (starts with `sb_secret_`; on older projects it's the `service_role` key). Click reveal and copy it.

## 2. Hosting (Vercel)
1. vercel.com → **Add New… → Project → Import Git Repository** → choose **Scaper20/FX-bot**.
   If it isn't listed, click "Adjust GitHub App Permissions" and give Vercel access to that one repository.
2. Leave **Root Directory** as `./`. If Vercel suggests a framework, choose **Flask** (or "Other"). No build command.
3. Open **Environment Variables** and add these four (all environments are fine):

   | Name | Value |
   |---|---|
   | `SUPABASE_URL` | the Project URL from step 1.3 |
   | `SUPABASE_SECRET_KEY` | the secret key from step 1.3 |
   | `TWELVEDATA_API_KEY` | your Twelve Data key |
   | `SITE_PASSWORD` | a long password you choose for logging in to the site |

4. Click **Deploy**. When it finishes, open `https://<your-project>.vercel.app/api/health`.
   You should see `"database": true`, `"feed_key_set": true`, `"password_set": true`.
5. Open the site, log in with `SITE_PASSWORD`, go to **Settings**:
   - enter your real Exness Standard spreads, balance and risk %;
   - click **Check GBP/USD and gold feed**. Both lines should say OK. If gold says it isn't available on your plan, tell Claude.

## 3. Automatic scans
Send Claude the site address (e.g. `https://fx-bot-xyz.vercel.app`). Claude switches on scans every 15 minutes on weekdays
(06:00 London to 18:00 New York). Or do it yourself: SQL Editor → paste `db/migrations/002_schedule.sql`, replace
`YOUR-SITE.vercel.app` with your address → Run.

## Costs and limits (free plans)
- **Twelve Data free:** 800 credits a day. A scan uses 6; scheduled scans use about 384 a day, which leaves about 65 manual scans. The site stops scanning when the daily budget in Settings is reached.
- **Supabase free:** 500 MB database (years of journal entries). A free project pauses after 7 days with no activity; the scheduled scans keep it awake on weekdays.
- **Vercel Hobby:** free for personal, non-commercial use. Making the site public or commercial later means moving to a paid plan, plus the licence checks listed in CLAUDE.md.

## If something goes wrong
- `/api/health` shows what's missing without revealing any secret.
- **Settings → Recent scans** shows each scan's result or error message (for example a Twelve Data error).
- Vercel dashboard → your project → **Logs** shows server errors.
