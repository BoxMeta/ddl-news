# DDL.NEWS

Replacement for the Squarespace site. The 20 public articles are archived in `data/posts.json` with images in `public/images/`. URLs stay `/news/<original-slug>`.

New posts publish with one request. No draft state.

## Run locally

```bash
cd ddl-news
PUBLISH_SECRET=dev python3 server.py
```

Open http://localhost:8080

## Publish a post

```bash
curl -X POST http://localhost:8080/api/publish \
  -H "Authorization: Bearer dev" \
  -H "Content-Type: application/json" \
  -d '{"title":"DDL recap — Oct 6","slug":"2026-10-06-ddl-recap","date":"2026-10-06","excerpt":"One line.","body":"First paragraph.\\n\\nSecond paragraph."}'
```

That URL is public as soon as the request returns.

## Put it on ddl.news

1. Push this folder to a GitHub repo.
2. Railway: New Project → Deploy from GitHub. Set `PUBLISH_SECRET` to a long random string. Add custom domains `ddl.news` and `www.ddl.news`.
3. Move DNS off Squarespace. Squarespace has no clean way to keep the site and also serve this app on the same host. In the registrar (Squarespace or wherever ddl.news is registered), point the nameservers at Cloudflare, then:
   - `CNAME www` → your Railway hostname
   - `CNAME ddl.news` (or Cloudflare CNAME flattening on the apex) → the same Railway hostname
4. In Squarespace, remove the domain connection after the new site answers. Do the Squarespace export (Settings → Import & Export) first if you want their zip as a second copy. This archive is the public-page copy.

Do not cancel Squarespace until `https://ddl.news/news/ddnyc-ddl` loads the DDNYC recap from the new host.

## Nightly from Grok

After the domain answers, the automation POSTs the recap to `https://ddl.news/api/publish` with the bearer secret. Tell Grok the live URL and the secret is set, and the 11pm Pacific run can be armed.
