# Vacancylane

Search real job listings across ATS boards (Greenhouse, Lever, Ashby, Workday, etc.) plus LinkedIn, Wellfound, and Instahyre using Google-style `site:` queries — and get a **jobs list** in the app.

## Auth + application tracking

Vacancylane uses **Google Sign-In** and stores applications in **Postgres**:

1. Create an OAuth 2.0 **Web** client in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add `http://localhost:3000` under **Authorized JavaScript origins**
3. Put the client ID in both env files:

```bash
# backend/.env
DATABASE_URL=postgresql+psycopg://shyftos-rbac:shyftos@127.0.0.1:5434/vacancylane
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
JWT_SECRET=a-long-random-string

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

4. Start your Postgres container on host port **5434** (this project creates a `vacancylane` database on first boot)
5. Sign in from the header, then click **Apply** on a job — the row is saved under your Google account and the posting opens in a new tab

## App routes

| Route | Purpose |
| --- | --- |
| `/` | Marketing landing page |
| `/search` | Job search dashboard |
| `/applications` | Applied jobs tracker (status updates) |
| `/history` | Previous searches (re-run anytime) |
| `/login` `/signup` `/signin` | Google auth |

Signed-in searches are saved automatically to **History**. Apply from search lands in **Applications**.

## How it works

1. You enter role, location, skills, experience
2. Backend builds ATS dork queries (e.g. `site:jobs.lever.co remote ("AI Engineer") ...`)
3. Searches the web — **Google first** when a Serper/CSE key is set, otherwise DDGS
4. Validates ATS job-detail URLs, removes unrelated pages and duplicates
5. Scores each result against the requested role, skills, location and company
6. Opens every surviving link and drops postings that are already closed

## Search from resume

Upload a PDF, DOCX or plain-text resume with **Search from resume**. The backend
reads the file and fills the search form with:

- primary + alternate job title
- skills
- experience band (from an explicit "X years" line, or the date span of work history)
- location hints from the contact block

You can edit any field before hitting **Search jobs**. No LLM is required — it
uses resume heuristics tuned for tech CVs.

## Getting Google results into the app

google.com cannot be scraped from a server (scripted requests get a JavaScript
gate, not results). To put **real Google organic hits** into this project, add a
SERP key:

### Option A — Serper (recommended)

1. Sign up at [serper.dev](https://serper.dev) — **2,500 free queries**, no credit card
2. Copy the API key into `backend/.env`:

```bash
SERPER_API_KEY=your_key_here
```

3. Restart the backend. `/search/status` should report `"google_enabled": true`.

Each Search jobs run spends one Serper credit per page per ATS query. When
Google returns enough hits for a query, DDGS is skipped for that query to save
credits and time.

> **Free Serper accounts reject `num`** with `Query pattern not allowed for
> free accounts`, so requests never send it — volume comes from paging instead
> (10 organic results per page, up to 4 pages per query).

## Query construction

Google answers "did not match any documents" as soon as too many exact phrases
are stacked. Measured on one board, `"SDE" "India"` returns 10 results while
`"SDE" "India" ("0-2 years" OR "0-1 years" OR "1-2 years")` returns 0.

So:

- **Experience never goes into the query.** Postings phrase it dozens of ways,
  so demanding a literal `"0-2 years"` in Google's index mostly matches nothing.
  Selected bands are read off the posting text afterwards and shown per job.
- **Any query that returns zero results is retried once, relaxed**: `OR` groups
  are dropped and quotes are removed from every phrase after the role. Those
  hits are labelled `…(relaxed)` in the provider list.

## Raw mode

Toggle **Raw results** in the search bar (or send `"raw_results": true`) to see
everything search returned, with every filter stage off:

- no closed-posting verification
- no location, experience or relevance filtering
- no ATS URL validation, junk-title or near-duplicate removal

It is the closest thing to reading the Google results yourself, and it is much
faster since nothing is fetched for verification. Expect noise: non-job pages
and filled postings are included by design.

### Option B — Google Programmable Search

Official Custom Search JSON API (100 free queries/day). Needs both:

```bash
GOOGLE_API_KEY=...
GOOGLE_SEARCH_ENGINE_ID=...
```

Used when Serper is unset or returns nothing.

Without either key, search still works via DDGS metasearch (Yandex, Yahoo, …).

## Result coverage (DDGS fallback)

When Google is not configured (or returns thinly for a query):

- Every query is sent to **several engines and the results are merged**, not
  raced. Each engine indexes a different slice of the ATS sites, so the union is
  roughly twice what the first responder alone returns.
- Each engine is **paged until it repeats itself**. One response is capped at
  about a page, so paging is where most of the extra volume comes from.
- The second wave of queries runs unless the first already produced a large
  candidate pool, because liveness, location and experience filtering discard a
  large share of what search returns.

Use "Open on Google" in the UI to run the same dork on google.com by hand.

## Closed-posting filtering

Search engines keep indexing job pages for months after a role is filled, so a
raw dork search is typically 30–40% dead links. Each candidate is checked before
it reaches you, cheapest and most reliable signal first:

| Source | Check |
| --- | --- |
| Greenhouse, Ashby | Public board API, fetched once per company; the posting id must appear in the open set |
| Lever, SmartRecruiters | Per-posting API — `200` is open, `404` is closed |
| Workday, Workable, LinkedIn, Wellfound, Instahyre, others | Page fetch: dead status codes, redirects away from the posting id, and closed/open markers in the HTML (no board API) |

Closed postings are the only thing a search removes. Location and experience are
**reported, never filtered on**: each job carries `location_match` and
`experience_match` plus the extracted `experience_years`, and the result-side
toggles decide what is shown.

Results are then **ordered by location**, so the jobs where you asked to work
come first and everything else follows rather than disappearing:

| `location_match` | Meaning |
| --- | --- |
| `match` | In a requested city, or anywhere in a requested country |
| `remote` | Remote, and you asked for remote |
| `country` | Same country as a requested city, but a different city |
| `unknown` | No location published, or the string names no place we can resolve |
| `mismatch` | Resolves to somewhere you did not ask for |

Matching runs on resolved place names rather than substrings, so a country
selection matches its cities, `Bengaluru` matches `Bangalore`, accented names
like `Malmö` match `Malmo`, and a city glued to an office name
(`Junglee Bangalore`) still resolves. Relevance orders jobs inside each group.

Every job carries a `status` of `open` or `unknown`. Postings proven closed are
removed and counted in `removed_closed`. Anything that cannot be proven closed
is kept, so a rate limit or timeout never silently hides a real job — client-side
boards like Workday often land in `unknown` for this reason.

`unknown` postings are the ones that still occasionally turn out to be filled,
so the UI's **"Confirmed live" filter is on by default** and shows only postings
the ATS itself reported as open. Turn it off to include the unproven ones.

Verification runs in parallel and adds roughly 3–4s to a search. Set
`verify_live: false` (or toggle "Hide closed jobs" off in the UI) to skip it.

## Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic v2, DDGS
- **Frontend:** Next.js 15, TypeScript, Tailwind, TanStack Query, Zod

## Quick start

### Backend (Python 3.12)

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open http://localhost:3000

## Main API

### `POST /search`

```json
{
  "role": "AI Engineer",
  "alternate_role": "ML Engineer",
  "location": "remote",
  "skills": "Python OR LLM",
  "experience": "3+ years",
  "sources": ["greenhouse", "lever", "ashby"],
  "date_posted": "month",
  "remote_only": true,
  "employment_type": "Full-time",
  "verify_live": true
}
```

Response includes `jobs[]` with title, URL, snippet, company, source,
employment type, remote status, a relevance score, and a `status` /`verified`
pair from the liveness check. `removed_closed` reports how many dead postings
were filtered out.

### `GET /ats-sources`

Lists available ATS boards.

## Docker

```bash
docker compose up --build
```

## Notes

- Results depend on live web indexes; some ATS pages do not expose a posted date
- Only validated job-detail links from known ATS hosts are kept
- Result filters include a "Confirmed live" toggle for API-verified postings only
- Search-time filters include freshness, employment type, remote and ATS source
- Result filters include keyword, source, remote, match threshold and sorting
- Legacy query CRUD endpoints still exist under `/queries` if needed
