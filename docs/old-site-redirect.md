# Old address (fxbot-ochre.vercel.app)

The site moved to https://fx-bot-vert.vercel.app on 25 Nov 2026.

- Ore deleted the old Vercel project (old account), so no copy of the app runs
  there and nothing at the old address can reach the database.
- 25 Nov 2026: Claude added `fxbot-ochre.vercel.app` as a domain on the new
  `fx-bot` project (team betrix) with a **301 redirect** to fx-bot-vert.vercel.app.
  Path and query string are kept, so old email links (practice,
  `/p/unsubscribe/<token>`) land on the new site. Holding the name also stops
  anyone else claiming it and receiving old unsubscribe tokens.
- Do not remove that domain from the project while old emails may still be used.

Check:
```
curl -sI https://fxbot-ochre.vercel.app/p/unsubscribe/abc   # 301 -> https://fx-bot-vert.vercel.app/p/unsubscribe/abc
```
