# 🚀 Milli Yapay Zeka — Deployment Rehberi

## 💰 Fiyat Karşılaştırması

| Platform | Fiyat | Uyku Modu | Hız | Öneri |
|----------|-------|-----------|-----|-------|
| **Streamlit Cloud** | **ÜCRETSİZ** | ✅ (1h) | Yavaş boot | UI için ideal |
| **Render Free** | **ÜCRETSİZ** | ✅ (15 dk) | Yavaş boot | Test için |
| **Fly.io** | ~$0-3/ay | ✅ (ayarlanabilir) | Hızlı | API için en iyi |
| **Railway** | $5/ay | ❌ | Çok hızlı | Production |
| **Render Paid** | $7/ay | ❌ | Hızlı | Stabil |
| **Heroku** | $7/ay | ❌ | Orta | Eski platform |
| **Google Cloud Run** | Pay-per-use ~$1-5/ay | ✅ | Hızlı | Scale gerekirse |

### 🏆 En Ucuz Kombinasyon (Neredeyse Ücretsiz)
- **Streamlit UI** → Streamlit Community Cloud (ÜCRETSİZ)
- **FastAPI Backend** → Fly.io (aylık ~$0-3, kullanıma göre)
- **Database** → Supabase Free (500MB, ÜCRETSİZ)

---

## Option 1: Streamlit Community Cloud (ÜCRETSİZ — En Kolay)

Sadece Streamlit UI'ı deploy eder. FastAPI ayrı çalışır.

```bash
# 1. GitHub'a push
git push origin main

# 2. share.streamlit.io adresine git
# 3. "New app" → repo seç → app_streamlit_cloud.py seç
# 4. Secrets ekle:
```

**Secrets (share.streamlit.io → Settings → Secrets):**
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "AIza..."
ZHIPUAI_API_KEY = "..."
GITHUB_TOKEN = "ghp_..."
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJ..."
FASTAPI_URL = "https://milli-yapay-zeka.fly.dev"
```

---

## Option 2: Fly.io (En Ucuz Full-Stack — ~$0-3/ay)

```bash
# Kurulum
curl -L https://fly.io/install.sh | sh
fly auth login

# Deploy
fly launch --name milli-yapay-zeka --region ams
fly secrets set ANTHROPIC_API_KEY=sk-ant-...
fly secrets set GOOGLE_API_KEY=AIza...
fly secrets set ZHIPUAI_API_KEY=...
fly secrets set GITHUB_TOKEN=ghp_...
fly secrets set SUPABASE_URL=https://xxx.supabase.co
fly secrets set SUPABASE_KEY=eyJ...
fly deploy

# URL: https://milli-yapay-zeka.fly.dev
```

---

## Option 3: Render (Tamamen Ücretsiz — Yavaş Boot)

```bash
# 1. render.com → New → Blueprint
# 2. GitHub repo bağla
# 3. render.yaml otomatik detect edilir
# 4. Environment variables ekle
```

**Render Dashboard'da eklenecek env vars:**
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `ZHIPUAI_API_KEY`
- `GITHUB_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_KEY`

---

## Option 4: Railway ($5/ay — En Kolay Production)

```bash
# Kurulum
npm install -g @railway/cli
railway login

# Deploy
railway init
railway up

# Environment variables
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set GOOGLE_API_KEY=AIza...
# ... diğerleri

# URL: https://milli-yapay-zeka.up.railway.app
```

---

## Option 5: Docker (Kendi Sunucun / VPS)

```bash
# .env dosyasını düzenle
cp .env.example .env
nano .env

# Docker ile çalıştır
docker-compose up -d

# Güncelleme
docker-compose pull && docker-compose up -d

# Loglar
docker-compose logs -f
```

**Ucuz VPS önerileri:**
- [Hetzner](https://hetzner.com) — CX11: €3.79/ay (Almanya)
- [Contabo](https://contabo.com) — VPS S: €4.99/ay
- [DigitalOcean](https://digitalocean.com) — Basic: $4/ay

---

## Supabase Kurulumu (ÜCRETSİZ)

```sql
-- supabase.com → SQL Editor'de çalıştır
create table projects (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  created_at timestamptz default now(),
  updated_at timestamptz
);

create table sessions (
  id uuid default gen_random_uuid() primary key,
  title text,
  project_id uuid references projects(id) on delete cascade,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table messages (
  id uuid default gen_random_uuid() primary key,
  session_id uuid references sessions(id) on delete cascade,
  project_id uuid references projects(id) on delete set null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  model text,
  created_at timestamptz default now()
);

create table auto_saves (
  session_id uuid primary key,
  state jsonb,
  saved_at timestamptz default now()
);

-- Row Level Security (isteğe bağlı)
alter table projects enable row level security;
alter table sessions enable row level security;
alter table messages enable row level security;
```
