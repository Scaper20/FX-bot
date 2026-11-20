# Email setup (SendByte)

Email does two things: **sign-in codes** for public practice traders, and **update emails** you send from the Community page.
Until real delivery works, public practice keeps the old username-only sign-in, so nothing breaks in the meantime.

## 1. Try it safely with a test key (5 minutes)
1. Sign up at sendbyte.africa. You get a **sandbox key** (starts with `sk_test_`). Sandbox emails are simulated: nobody receives them.
2. In Vercel → your project → Settings → Environment Variables, add:
   - `SENDBYTE_API_KEY` = the `sk_test_…` key
   - `SENDBYTE_FROM` = `CRT Practice <practice@mail.kiqstat.app>` (the address you'll verify in step 2)
3. Redeploy (Deployments → … → Redeploy). On the site: Settings → add your own email, then Community → "Send a test to me".
   With a test key it shows in SendByte's email log as sandbox; nothing arrives.

## 2. Real delivery: verify a domain
Real emails must come from a domain you control. Using **kiqstat** works if you (or whoever runs it) can add DNS records for it.
Use a **subdomain**, e.g. `mail.kiqstat.app`, so the main domain's existing email settings aren't touched.

1. In SendByte, add the domain `mail.kiqstat.app` (Domains → Add). It shows 3 DNS records:
   - **DKIM** (required): TXT at `sb._domainkey.mail.kiqstat.app`
   - **SPF** (recommended): TXT at `mail.kiqstat.app`, `v=spf1 include:amazonses.com ~all`
   - **DMARC** (recommended): TXT at `_dmarc.mail.kiqstat.app`
2. Add those TXT records wherever kiqstat's DNS is managed (registrar, Cloudflare…). Copy the values exactly from SendByte.
3. Back in SendByte click **Verify**. It usually passes within minutes (up to an hour).
4. Create a **live key** (starts with `sk_live_`) with the **send only** permission, and put it in Vercel as `SENDBYTE_API_KEY`. Redeploy.

As soon as a live key is set, `/p` switches to **username + email with a 6-digit code**.

## Notes
- **Limits built into the site:** codes expire after 10 minutes, 5 wrong tries lock a code, 5 codes per email per hour, 300 codes a day for the whole site.
- **Update emails:** one email per trader (nobody sees other addresses), each with an unsubscribe link. Re-sending the same update only reaches people who didn't get it yet.
- **Privacy:** only username, email and answers are stored, and a trader can delete everything from "My results". Collecting emails publicly brings Nigeria's data protection law (NDPA 2023) into play; keep the list to this purpose and don't share it.
