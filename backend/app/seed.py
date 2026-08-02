"""Seed database with collections, ATS presets, and 50 search query templates."""

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import AtsPreset, Collection, Query

COLLECTIONS = [
    {"name": "AI", "description": "AI / ML / LLM roles", "color": "#c586c0"},
    {"name": "Backend", "description": "Backend and API engineering", "color": "#4ec9b0"},
    {"name": "Full Stack", "description": "Full stack engineering", "color": "#dcdcaa"},
    {"name": "Remote", "description": "Remote-friendly searches", "color": "#9cdcfe"},
    {"name": "India", "description": "India-based opportunities", "color": "#ce9178"},
    {"name": "US", "description": "US-based opportunities", "color": "#569cd6"},
]

ATS_PRESETS = [
    {
        "name": "Greenhouse",
        "slug": "greenhouse",
        "description": "Search Greenhouse-hosted job boards",
        "query_template": (
            'site:job-boards.greenhouse.io {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "Lever",
        "slug": "lever",
        "description": "Search Lever-hosted careers pages",
        "query_template": (
            'site:jobs.lever.co {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "Ashby",
        "slug": "ashby",
        "description": "Search Ashby-hosted job boards",
        "query_template": (
            'site:jobs.ashbyhq.com {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "Workday",
        "slug": "workday",
        "description": "Search Workday myworkdayjobs listings",
        "query_template": (
            'site:myworkdayjobs.com {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "SmartRecruiters",
        "slug": "smartrecruiters",
        "description": "Search SmartRecruiters job boards",
        "query_template": (
            'site:jobs.smartrecruiters.com {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "Workable",
        "slug": "workable",
        "description": "Search Workable apply pages",
        "query_template": (
            'site:apply.workable.com {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "LinkedIn",
        "slug": "linkedin",
        "description": "Search LinkedIn job listings",
        "query_template": (
            'site:linkedin.com/jobs {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "Wellfound",
        "slug": "wellfound",
        "description": "Search Wellfound (AngelList) startup jobs",
        "query_template": (
            'site:wellfound.com/jobs {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "Instahyre",
        "slug": "instahyre",
        "description": "Search Instahyre job listings",
        "query_template": (
            'site:instahyre.com {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "Teamtailor",
        "slug": "teamtailor",
        "description": "Search Teamtailor career sites",
        "query_template": (
            'site:teamtailor.com {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "name": "BambooHR",
        "slug": "bamboohr",
        "description": "Search BambooHR career portals",
        "query_template": (
            'site:bamboohr.com/careers {{location}} ("{{role}}" OR "{{alternate_role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
]

# 50 seed query templates
QUERIES = [
    # AI / ML (1-10)
    {
        "title": "Greenhouse — AI Engineer Remote",
        "category": "AI Engineer",
        "collection": "AI",
        "tags": ["greenhouse", "remote", "ai"],
        "is_favorite": True,
        "notes": "Core AI eng search on Greenhouse",
        "query_text": (
            'site:job-boards.greenhouse.io {{location}} ("AI Engineer" OR "Machine Learning Engineer") '
            '(Python OR PyTorch OR LLM) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — LLM Engineer",
        "category": "AI Engineer",
        "collection": "AI",
        "tags": ["lever", "llm"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co {{location}} ("LLM Engineer" OR "Generative AI Engineer") '
            '(LangChain OR RAG OR "prompt engineering") ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — ML Engineer",
        "category": "ML Engineer",
        "collection": "AI",
        "tags": ["ashby", "ml"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.ashbyhq.com {{location}} ("ML Engineer" OR "Machine Learning") '
            '(TensorFlow OR PyTorch OR scikit-learn) ("{{experience}}")'
        ),
    },
    {
        "title": "Workday — AI Research Scientist",
        "category": "AI Engineer",
        "collection": "AI",
        "tags": ["workday", "research"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:myworkdayjobs.com {{location}} ("AI Research" OR "Research Scientist") '
            '(NLP OR "computer vision" OR transformers) ("{{experience}}")'
        ),
    },
    {
        "title": "Greenhouse — GenAI Platform",
        "category": "AI Engineer",
        "collection": "AI",
        "tags": ["greenhouse", "genai"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:job-boards.greenhouse.io {{location}} ("Generative AI" OR GenAI OR "AI Platform") '
            '(Python OR FastAPI OR Kubernetes) ("{{experience}}")'
        ),
    },
    {
        "title": "SmartRecruiters — NLP Engineer",
        "category": "AI Engineer",
        "collection": "AI",
        "tags": ["smartrecruiters", "nlp"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.smartrecruiters.com {{location}} ("NLP Engineer" OR "Natural Language") '
            '(transformers OR BERT OR spaCy) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — Applied Scientist",
        "category": "ML Engineer",
        "collection": "AI",
        "tags": ["lever", "applied-science"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co {{location}} ("Applied Scientist" OR "Applied ML") '
            '(Python OR A/B OR experimentation) ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — AI Infra Engineer",
        "category": "AI Engineer",
        "collection": "AI",
        "tags": ["ashby", "infra"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.ashbyhq.com {{location}} ("AI Infrastructure" OR "ML Platform") '
            '(Kubernetes OR CUDA OR "model serving") ("{{experience}}")'
        ),
    },
    {
        "title": "Workable — Computer Vision",
        "category": "ML Engineer",
        "collection": "AI",
        "tags": ["workable", "cv"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:apply.workable.com {{location}} ("Computer Vision" OR "CV Engineer") '
            '(OpenCV OR YOLO OR "deep learning") ("{{experience}}")'
        ),
    },
    {
        "title": "Teamtailor — AI Product Engineer",
        "category": "AI Engineer",
        "collection": "AI",
        "tags": ["teamtailor", "product"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:teamtailor.com {{location}} ("AI Engineer" OR "AI Product") '
            '(OpenAI OR Claude OR embeddings) ("{{experience}}")'
        ),
    },
    # Backend (11-20)
    {
        "title": "Greenhouse — Backend Python",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["greenhouse", "python"],
        "is_favorite": True,
        "notes": "Python backend on Greenhouse",
        "query_text": (
            'site:job-boards.greenhouse.io {{location}} ("Backend Engineer" OR "Software Engineer Backend") '
            '(Python OR Django OR FastAPI) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — Backend Go",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["lever", "golang"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co {{location}} ("Backend Engineer" OR "Software Engineer") '
            '(Go OR Golang OR gRPC) ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — Backend Node",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["ashby", "nodejs"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.ashbyhq.com {{location}} ("Backend Engineer" OR "Node.js Engineer") '
            '(Node OR TypeScript OR NestJS) ("{{experience}}")'
        ),
    },
    {
        "title": "Workday — Java Backend",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["workday", "java"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:myworkdayjobs.com {{location}} ("Backend Engineer" OR "Java Developer") '
            '(Java OR Spring OR Kotlin) ("{{experience}}")'
        ),
    },
    {
        "title": "SmartRecruiters — API Engineer",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["smartrecruiters", "api"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.smartrecruiters.com {{location}} ("API Engineer" OR "Backend Engineer") '
            '(REST OR GraphQL OR microservices) ("{{experience}}")'
        ),
    },
    {
        "title": "Workable — Platform Engineer Backend",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["workable", "platform"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:apply.workable.com {{location}} ("Platform Engineer" OR "Backend Platform") '
            '(Kubernetes OR AWS OR Terraform) ("{{experience}}")'
        ),
    },
    {
        "title": "BambooHR — Backend Engineer",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["bamboohr", "general"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:bamboohr.com/careers {{location}} ("Backend Engineer" OR "Software Engineer") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Greenhouse — Distributed Systems",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["greenhouse", "distributed"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:job-boards.greenhouse.io {{location}} ("Distributed Systems" OR "Backend Engineer") '
            '(Kafka OR Redis OR Cassandra) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — Rust Backend",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["lever", "rust"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co {{location}} ("Backend Engineer" OR "Systems Engineer") '
            '(Rust OR systems OR performance) ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — Staff Backend",
        "category": "Backend",
        "collection": "Backend",
        "tags": ["ashby", "staff"],
        "is_favorite": False,
        "notes": "Senior/staff level",
        "query_text": (
            'site:jobs.ashbyhq.com {{location}} ("Staff Backend" OR "Senior Backend Engineer") '
            '(architecture OR leadership OR scalable) ("{{experience}}")'
        ),
    },
    # Full Stack (21-28)
    {
        "title": "Greenhouse — Full Stack React",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["greenhouse", "react"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:job-boards.greenhouse.io {{location}} ("Full Stack" OR "Fullstack Engineer") '
            '(React OR Next.js OR TypeScript) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — Full Stack Python",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["lever", "python"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co {{location}} ("Full Stack" OR "Fullstack") '
            '(Python OR Django OR React) ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — Full Stack TypeScript",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["ashby", "typescript"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.ashbyhq.com {{location}} ("Full Stack Engineer" OR "Software Engineer") '
            '(TypeScript OR Node OR React) ("{{experience}}")'
        ),
    },
    {
        "title": "Workday — Full Stack Java",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["workday", "java"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:myworkdayjobs.com {{location}} ("Full Stack" OR "Fullstack Developer") '
            '(Java OR Spring OR Angular) ("{{experience}}")'
        ),
    },
    {
        "title": "SmartRecruiters — Full Stack",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["smartrecruiters"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.smartrecruiters.com {{location}} ("Full Stack Engineer" OR "{{role}}") '
            '({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Workable — Full Stack Startup",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["workable", "startup"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:apply.workable.com {{location}} ("Full Stack" OR "Software Engineer") '
            '(startup OR SaaS OR product) ("{{experience}}")'
        ),
    },
    {
        "title": "Teamtailor — Full Stack Vue",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["teamtailor", "vue"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:teamtailor.com {{location}} ("Full Stack" OR "Frontend Engineer") '
            '(Vue OR Nuxt OR TypeScript) ("{{experience}}")'
        ),
    },
    {
        "title": "Greenhouse — Next.js Full Stack",
        "category": "Full Stack",
        "collection": "Full Stack",
        "tags": ["greenhouse", "nextjs"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:job-boards.greenhouse.io {{location}} ("Full Stack" OR "Frontend Engineer") '
            '("Next.js" OR NextJS OR React) ("{{experience}}")'
        ),
    },
    # Remote (29-35)
    {
        "title": "Greenhouse — Remote Backend",
        "category": "Backend",
        "collection": "Remote",
        "tags": ["greenhouse", "remote"],
        "is_favorite": True,
        "notes": "Force remote keyword",
        "query_text": (
            'site:job-boards.greenhouse.io (remote OR "work from home") '
            '("Backend Engineer" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — Remote Full Stack",
        "category": "Full Stack",
        "collection": "Remote",
        "tags": ["lever", "remote"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co (remote OR distributed) '
            '("Full Stack" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — Remote AI",
        "category": "AI Engineer",
        "collection": "Remote",
        "tags": ["ashby", "remote", "ai"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:jobs.ashbyhq.com (remote OR "anywhere") '
            '("AI Engineer" OR "ML Engineer") (Python OR LLM) ("{{experience}}")'
        ),
    },
    {
        "title": "Workday — Remote Software Eng",
        "category": "Backend",
        "collection": "Remote",
        "tags": ["workday", "remote"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:myworkdayjobs.com (remote OR "telecommute") '
            '("Software Engineer" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "SmartRecruiters — Remote DevOps",
        "category": "DevOps",
        "collection": "Remote",
        "tags": ["smartrecruiters", "remote", "devops"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.smartrecruiters.com (remote) '
            '("DevOps" OR "SRE" OR "Platform Engineer") (Kubernetes OR AWS OR Terraform) ("{{experience}}")'
        ),
    },
    {
        "title": "Workable — Remote Frontend",
        "category": "Frontend",
        "collection": "Remote",
        "tags": ["workable", "remote", "frontend"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:apply.workable.com (remote) '
            '("Frontend Engineer" OR "UI Engineer") (React OR TypeScript OR CSS) ("{{experience}}")'
        ),
    },
    {
        "title": "Multi-ATS — Remote General",
        "category": "Other",
        "collection": "Remote",
        "tags": ["multi", "remote"],
        "is_favorite": False,
        "notes": "Search across Greenhouse + Lever + Ashby",
        "query_text": (
            '(site:job-boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com) '
            '(remote) ("{{role}}" OR "{{alternate_role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    # India (36-42)
    {
        "title": "Greenhouse — India Backend",
        "category": "Backend",
        "collection": "India",
        "tags": ["greenhouse", "india"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:job-boards.greenhouse.io (India OR Bangalore OR Bengaluru OR Hyderabad OR Pune OR Mumbai) '
            '("Backend Engineer" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — India Full Stack",
        "category": "Full Stack",
        "collection": "India",
        "tags": ["lever", "india"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co (India OR Bangalore OR "Remote - India") '
            '("Full Stack" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — India AI Engineer",
        "category": "AI Engineer",
        "collection": "India",
        "tags": ["ashby", "india", "ai"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:jobs.ashbyhq.com (India OR Bangalore OR Bengaluru) '
            '("AI Engineer" OR "ML Engineer") (Python OR LLM OR PyTorch) ("{{experience}}")'
        ),
    },
    {
        "title": "Workday — India Software Eng",
        "category": "Backend",
        "collection": "India",
        "tags": ["workday", "india"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:myworkdayjobs.com (India OR Bangalore OR Hyderabad OR Chennai) '
            '("Software Engineer" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "SmartRecruiters — India DevOps",
        "category": "DevOps",
        "collection": "India",
        "tags": ["smartrecruiters", "india"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.smartrecruiters.com (India OR Bangalore OR Pune) '
            '("DevOps" OR "SRE") (Kubernetes OR AWS OR Azure) ("{{experience}}")'
        ),
    },
    {
        "title": "Workable — India Data Engineer",
        "category": "Data Engineer",
        "collection": "India",
        "tags": ["workable", "india", "data"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:apply.workable.com (India OR Bangalore OR Hyderabad) '
            '("Data Engineer" OR "Analytics Engineer") (Spark OR Airflow OR SQL) ("{{experience}}")'
        ),
    },
    {
        "title": "Multi-ATS — India AI Roles",
        "category": "AI Engineer",
        "collection": "India",
        "tags": ["multi", "india", "ai"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            '(site:job-boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com) '
            '(India OR Bangalore OR Bengaluru) ("AI Engineer" OR "ML Engineer" OR LLM) '
            '(Python) ("{{experience}}")'
        ),
    },
    # US (43-50)
    {
        "title": "Greenhouse — US Backend SF/NYC",
        "category": "Backend",
        "collection": "US",
        "tags": ["greenhouse", "us"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:job-boards.greenhouse.io ("San Francisco" OR "New York" OR Seattle OR Austin OR "United States") '
            '("Backend Engineer" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Lever — US Full Stack",
        "category": "Full Stack",
        "collection": "US",
        "tags": ["lever", "us"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.lever.co ("United States" OR "San Francisco" OR "New York" OR remote) '
            '("Full Stack" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "Ashby — US AI Engineer",
        "category": "AI Engineer",
        "collection": "US",
        "tags": ["ashby", "us", "ai"],
        "is_favorite": True,
        "notes": None,
        "query_text": (
            'site:jobs.ashbyhq.com ("San Francisco" OR "New York" OR "United States" OR remote) '
            '("AI Engineer" OR "ML Engineer") (Python OR LLM) ("{{experience}}")'
        ),
    },
    {
        "title": "Workday — US Staff Engineer",
        "category": "Backend",
        "collection": "US",
        "tags": ["workday", "us", "staff"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:myworkdayjobs.com ("United States" OR USA) '
            '("Staff Engineer" OR "Principal Engineer") ({{skills}}) ("{{experience}}")'
        ),
    },
    {
        "title": "SmartRecruiters — US Frontend",
        "category": "Frontend",
        "collection": "US",
        "tags": ["smartrecruiters", "us"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:jobs.smartrecruiters.com ("United States" OR "San Francisco" OR "New York") '
            '("Frontend Engineer" OR "UI Engineer") (React OR TypeScript) ("{{experience}}")'
        ),
    },
    {
        "title": "Workable — US Data Engineer",
        "category": "Data Engineer",
        "collection": "US",
        "tags": ["workable", "us", "data"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:apply.workable.com ("United States" OR remote) '
            '("Data Engineer" OR "Analytics Engineer") (Spark OR Snowflake OR dbt) ("{{experience}}")'
        ),
    },
    {
        "title": "Teamtailor — US Mobile",
        "category": "Mobile",
        "collection": "US",
        "tags": ["teamtailor", "us", "mobile"],
        "is_favorite": False,
        "notes": None,
        "query_text": (
            'site:teamtailor.com ("United States" OR remote) '
            '("iOS Engineer" OR "Android Engineer" OR "Mobile Engineer") '
            '(Swift OR Kotlin OR React Native) ("{{experience}}")'
        ),
    },
    {
        "title": "BambooHR — US General SWE",
        "category": "Other",
        "collection": "US",
        "tags": ["bamboohr", "us"],
        "is_favorite": False,
        "notes": "Generic US SWE search on BambooHR",
        "query_text": (
            'site:bamboohr.com/careers ("United States" OR USA OR remote) '
            '("Software Engineer" OR "{{role}}") ({{skills}}) ("{{experience}}")'
        ),
    },
]


def seed(db: Session | None = None) -> None:
    own_session = db is None
    if own_session:
        init_db()
        db = SessionLocal()

    assert db is not None

    try:
        if db.query(Collection).count() == 0:
            for c in COLLECTIONS:
                db.add(Collection(**c))
            db.commit()
            print(f"Seeded {len(COLLECTIONS)} collections")

        existing_presets = {p.slug: p for p in db.query(AtsPreset).all()}
        added = 0
        for p in ATS_PRESETS:
            if p["slug"] in existing_presets:
                continue
            db.add(AtsPreset(**p))
            added += 1
        if added:
            db.commit()
            print(f"Seeded {added} ATS presets")
        elif not existing_presets:
            print("No ATS presets to seed")
        else:
            print("ATS presets already present, skipping")

        if db.query(Query).count() == 0:
            collections = {c.name: c.id for c in db.query(Collection).all()}
            for q in QUERIES:
                data = {**q}
                collection_name = data.pop("collection")
                db.add(
                    Query(
                        **data,
                        collection_id=collections.get(collection_name),
                    )
                )
            db.commit()
            print(f"Seeded {len(QUERIES)} search queries")
        else:
            print("Queries already seeded, skipping")
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    seed()
