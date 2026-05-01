import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from app.config import settings
from app.database import SessionLocal
from app.models.article import Article


def _parse_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6])
            except Exception:
                pass
    return None

RSS_SOURCES = [
    # ── Global — General ─────────────────────────────────────────────────────
    {"name": "BBC News",           "url": "http://feeds.bbci.co.uk/news/rss.xml",                           "region": "global", "lang": "en", "category": "general"},
    {"name": "Reuters",            "url": "https://feeds.reuters.com/reuters/topNews",                      "region": "global", "lang": "en", "category": "general"},
    {"name": "Al Jazeera",         "url": "https://www.aljazeera.com/xml/rss/all.xml",                     "region": "global", "lang": "en", "category": "general"},
    {"name": "The Guardian",       "url": "https://www.theguardian.com/world/rss",                         "region": "global", "lang": "en", "category": "general"},
    {"name": "Deutsche Welle",     "url": "https://rss.dw.com/rdf/rss-en-all",                             "region": "global", "lang": "en", "category": "general"},
    {"name": "France 24",          "url": "https://www.france24.com/en/rss",                               "region": "global", "lang": "en", "category": "general"},
    {"name": "Associated Press",   "url": "https://feeds.apnews.com/apnews/topnews",                       "region": "global", "lang": "en", "category": "general"},
    {"name": "TIME",               "url": "https://time.com/feed/",                                        "region": "global", "lang": "en", "category": "general"},

    # ── Tech ──────────────────────────────────────────────────────────────────
    {"name": "HackerNews",         "url": "https://hnrss.org/frontpage",                                   "region": "global", "lang": "en", "category": "tech"},
    {"name": "TechCrunch",         "url": "https://techcrunch.com/feed/",                                  "region": "global", "lang": "en", "category": "tech"},
    {"name": "Wired",              "url": "https://www.wired.com/feed/rss",                                "region": "global", "lang": "en", "category": "tech"},
    {"name": "The Verge",          "url": "https://www.theverge.com/rss/index.xml",                        "region": "global", "lang": "en", "category": "tech"},
    {"name": "Ars Technica",       "url": "https://feeds.arstechnica.com/arstechnica/index",               "region": "global", "lang": "en", "category": "tech"},
    {"name": "MIT Tech Review",    "url": "https://www.technologyreview.com/feed/",                        "region": "global", "lang": "en", "category": "tech"},
    {"name": "VentureBeat",        "url": "https://feeds.feedburner.com/venturebeat/SZYF",                 "region": "global", "lang": "en", "category": "tech"},
    {"name": "Engadget",           "url": "https://www.engadget.com/rss.xml",                              "region": "global", "lang": "en", "category": "tech"},
    {"name": "TechRadar",          "url": "https://www.techradar.com/rss",                                 "region": "global", "lang": "en", "category": "tech"},
    {"name": "The Register",       "url": "https://www.theregister.com/headlines.atom",                    "region": "global", "lang": "en", "category": "tech"},
    {"name": "9to5Mac",            "url": "https://9to5mac.com/feed/",                                     "region": "global", "lang": "en", "category": "tech"},
    {"name": "Android Authority",  "url": "https://www.androidauthority.com/feed/",                       "region": "global", "lang": "en", "category": "tech"},
    {"name": "MIT AI News",        "url": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml","region": "global", "lang": "en", "category": "tech"},

    # ── Science ───────────────────────────────────────────────────────────────
    {"name": "NASA",               "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",                "region": "global", "lang": "en", "category": "science"},
    {"name": "New Scientist",      "url": "https://www.newscientist.com/feed/home/",                       "region": "global", "lang": "en", "category": "science"},
    {"name": "Science Daily",      "url": "https://www.sciencedaily.com/rss/all.xml",                      "region": "global", "lang": "en", "category": "science"},
    {"name": "Nature",             "url": "https://www.nature.com/nature.rss",                             "region": "global", "lang": "en", "category": "science"},
    {"name": "Scientific American","url": "https://rss.sciam.com/ScientificAmerican-Global",               "region": "global", "lang": "en", "category": "science"},
    {"name": "Phys.org",           "url": "https://phys.org/rss-feed/",                                   "region": "global", "lang": "en", "category": "science"},
    {"name": "Space.com",          "url": "https://www.space.com/feeds/all",                               "region": "global", "lang": "en", "category": "science"},
    {"name": "Live Science",       "url": "https://www.livescience.com/feeds/all",                         "region": "global", "lang": "en", "category": "science"},

    # ── Health ────────────────────────────────────────────────────────────────
    {"name": "WHO",                "url": "https://www.who.int/rss-feeds/news-english.xml",                "region": "global", "lang": "en", "category": "health"},
    {"name": "WebMD",              "url": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",  "region": "global", "lang": "en", "category": "health"},
    {"name": "Medical News Today", "url": "https://www.medicalnewstoday.com/rss/wordnews.xml",             "region": "global", "lang": "en", "category": "health"},
    {"name": "NHS UK News",        "url": "https://www.nhs.uk/news/latest-news/rss/",                      "region": "uk",     "lang": "en", "category": "health"},
    {"name": "Harvard Health",     "url": "https://www.health.harvard.edu/blog/feed",                      "region": "us",     "lang": "en", "category": "health"},
    {"name": "Healthline",         "url": "https://www.healthline.com/rss/health-news",                    "region": "global", "lang": "en", "category": "health"},

    # ── Business & Finance ────────────────────────────────────────────────────
    {"name": "Financial Times",    "url": "https://www.ft.com/rss/home",                                   "region": "global", "lang": "en", "category": "business"},
    {"name": "Bloomberg",          "url": "https://feeds.bloomberg.com/markets/news.rss",                  "region": "global", "lang": "en", "category": "business"},
    {"name": "Forbes",             "url": "https://www.forbes.com/real-time/feed2/",                       "region": "global", "lang": "en", "category": "business"},
    {"name": "CNBC",               "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",         "region": "us",     "lang": "en", "category": "business"},
    {"name": "MarketWatch",        "url": "https://feeds.content.dowjones.io/public/rss/mktw_topstories",  "region": "us",     "lang": "en", "category": "business"},
    {"name": "The Economist",      "url": "https://www.economist.com/finance-and-economics/rss.xml",       "region": "global", "lang": "en", "category": "business"},
    {"name": "Business Insider",   "url": "https://feeds.businessinsider.com/custom/all",                  "region": "global", "lang": "en", "category": "business"},
    {"name": "Investopedia",       "url": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline", "region": "global", "lang": "en", "category": "business"},

    # ── Environment ───────────────────────────────────────────────────────────
    {"name": "The Guardian Env",   "url": "https://www.theguardian.com/environment/rss",                   "region": "global", "lang": "en", "category": "environment"},
    {"name": "Climate Home News",  "url": "https://www.climatechangenews.com/feed/",                       "region": "global", "lang": "en", "category": "environment"},
    {"name": "Carbon Brief",       "url": "https://www.carbonbrief.org/feed",                              "region": "global", "lang": "en", "category": "environment"},
    {"name": "Grist",              "url": "https://grist.org/feed/",                                       "region": "global", "lang": "en", "category": "environment"},
    {"name": "Yale E360",          "url": "https://e360.yale.edu/feed.xml",                                "region": "global", "lang": "en", "category": "environment"},

    # ── Sports ────────────────────────────────────────────────────────────────
    {"name": "ESPN",               "url": "https://www.espn.com/espn/rss/news",                            "region": "global", "lang": "en", "category": "sports"},
    {"name": "BBC Sport",          "url": "http://feeds.bbci.co.uk/sport/rss.xml",                         "region": "global", "lang": "en", "category": "sports"},
    {"name": "Sky Sports",         "url": "https://www.skysports.com/rss/12040",                           "region": "global", "lang": "en", "category": "sports"},
    {"name": "Bleacher Report",    "url": "https://bleacherreport.com/articles/feed",                      "region": "global", "lang": "en", "category": "sports"},
    {"name": "BBC Cricket",        "url": "https://feeds.bbci.co.uk/sport/cricket/rss.xml",                "region": "global", "lang": "en", "category": "sports"},
    {"name": "ESPN Cricinfo",      "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",    "region": "global", "lang": "en", "category": "sports"},
    {"name": "The Athletic",       "url": "https://theathletic.com/feed/",                                 "region": "global", "lang": "en", "category": "sports"},

    # ── Entertainment ─────────────────────────────────────────────────────────
    {"name": "Variety",            "url": "https://variety.com/feed/",                                    "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Hollywood Reporter", "url": "https://www.hollywoodreporter.com/feed/",                       "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Rolling Stone",      "url": "https://www.rollingstone.com/feed/",                           "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Pitchfork",          "url": "https://pitchfork.com/feed/feed-news/rss",                     "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Deadline",           "url": "https://deadline.com/feed/",                                   "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Collider",           "url": "https://collider.com/feed/",                                   "region": "global", "lang": "en", "category": "entertainment"},

    # ── Gaming ────────────────────────────────────────────────────────────────
    {"name": "IGN",                "url": "https://feeds.ign.com/ign/games-all",                           "region": "global", "lang": "en", "category": "gaming"},
    {"name": "Polygon",            "url": "https://www.polygon.com/rss/index.xml",                        "region": "global", "lang": "en", "category": "gaming"},
    {"name": "Eurogamer",          "url": "https://www.eurogamer.net/?format=rss",                        "region": "global", "lang": "en", "category": "gaming"},
    {"name": "GameSpot",           "url": "https://www.gamespot.com/feeds/mashup/",                       "region": "global", "lang": "en", "category": "gaming"},
    {"name": "PC Gamer",           "url": "https://www.pcgamer.com/rss/",                                  "region": "global", "lang": "en", "category": "gaming"},
    {"name": "Rock Paper Shotgun", "url": "https://www.rockpapershotgun.com/feed/news",                    "region": "global", "lang": "en", "category": "gaming"},

    # ── Crypto ────────────────────────────────────────────────────────────────
    {"name": "CoinDesk",           "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",              "region": "global", "lang": "en", "category": "crypto"},
    {"name": "CoinTelegraph",      "url": "https://cointelegraph.com/rss",                                "region": "global", "lang": "en", "category": "crypto"},
    {"name": "Decrypt",            "url": "https://decrypt.co/feed",                                      "region": "global", "lang": "en", "category": "crypto"},
    {"name": "The Block",          "url": "https://www.theblock.co/rss.xml",                              "region": "global", "lang": "en", "category": "crypto"},
    {"name": "Bitcoin Magazine",   "url": "https://bitcoinmagazine.com/.rss/full/",                       "region": "global", "lang": "en", "category": "crypto"},

    # ── India ─────────────────────────────────────────────────────────────────
    {"name": "The Hindu",          "url": "https://www.thehindu.com/feeder/default.rss",                   "region": "india",  "lang": "en", "category": "general"},
    {"name": "NDTV",               "url": "https://feeds.feedburner.com/ndtvnews-top-stories",              "region": "india",  "lang": "en", "category": "general"},
    {"name": "Times of India",     "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",    "region": "india",  "lang": "en", "category": "general"},
    {"name": "Indian Express",     "url": "https://indianexpress.com/feed/",                               "region": "india",  "lang": "en", "category": "general"},
    {"name": "Hindustan Times",    "url": "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",        "region": "india",  "lang": "en", "category": "general"},
    {"name": "The Wire",           "url": "https://thewire.in/feed",                                       "region": "india",  "lang": "en", "category": "politics"},
    {"name": "Mint",               "url": "https://www.livemint.com/rss/news",                             "region": "india",  "lang": "en", "category": "business"},
    {"name": "Economic Times",     "url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",      "region": "india",  "lang": "en", "category": "business"},
    {"name": "Business Standard",  "url": "https://www.business-standard.com/rss/home_page_top_stories.rss","region": "india", "lang": "en", "category": "business"},
    {"name": "India Today",        "url": "https://www.indiatoday.in/rss/home",                            "region": "india",  "lang": "en", "category": "general"},
    {"name": "Deccan Herald",      "url": "https://www.deccanherald.com/rss-feeds/home.feed",              "region": "india",  "lang": "en", "category": "general"},
    {"name": "NDTV Sports",        "url": "https://feeds.feedburner.com/ndtvsports-latest",                "region": "india",  "lang": "en", "category": "sports"},

    # ── US ───────────────────────────────────────────────────────────────────
    {"name": "NPR",                "url": "https://feeds.npr.org/1001/rss.xml",                            "region": "us",     "lang": "en", "category": "general"},
    {"name": "AP News",            "url": "https://rsshub.app/apnews/topics/apf-topnews",                  "region": "us",     "lang": "en", "category": "general"},
    {"name": "Washington Post",    "url": "https://feeds.washingtonpost.com/rss/world",                    "region": "us",     "lang": "en", "category": "general"},
    {"name": "NY Times",           "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",     "region": "us",     "lang": "en", "category": "general"},
    {"name": "Politico",           "url": "https://www.politico.com/rss/politicopicks.xml",                "region": "us",     "lang": "en", "category": "politics"},
    {"name": "The Hill",           "url": "https://thehill.com/rss/syndicator/19109",                      "region": "us",     "lang": "en", "category": "politics"},
    {"name": "Axios",              "url": "https://api.axios.com/feed/",                                   "region": "us",     "lang": "en", "category": "general"},
    {"name": "Vox",                "url": "https://www.vox.com/rss/index.xml",                             "region": "us",     "lang": "en", "category": "general"},
    {"name": "ProPublica",         "url": "https://www.propublica.org/feeds/propublica/main",              "region": "us",     "lang": "en", "category": "general"},
    {"name": "The Atlantic",       "url": "https://www.theatlantic.com/feed/all/",                         "region": "us",     "lang": "en", "category": "general"},

    # ── UK ───────────────────────────────────────────────────────────────────
    {"name": "The Guardian UK",    "url": "https://www.theguardian.com/uk/rss",                            "region": "uk",     "lang": "en", "category": "general"},
    {"name": "BBC UK",             "url": "http://feeds.bbci.co.uk/news/uk/rss.xml",                       "region": "uk",     "lang": "en", "category": "general"},
    {"name": "The Telegraph",      "url": "https://www.telegraph.co.uk/rss.xml",                           "region": "uk",     "lang": "en", "category": "general"},
    {"name": "The Independent",    "url": "https://www.independent.co.uk/news/rss",                        "region": "uk",     "lang": "en", "category": "general"},
    {"name": "Sky News",           "url": "https://feeds.skynews.com/feeds/rss/home.xml",                  "region": "uk",     "lang": "en", "category": "general"},
    {"name": "Evening Standard",   "url": "https://www.standard.co.uk/news/rss",                           "region": "uk",     "lang": "en", "category": "general"},

    # ── Australia ─────────────────────────────────────────────────────────────
    {"name": "ABC News AU",        "url": "https://www.abc.net.au/news/feed/51120/rss.xml",                "region": "australia", "lang": "en", "category": "general"},
    {"name": "The Guardian AU",    "url": "https://www.theguardian.com/australia-news/rss",                "region": "australia", "lang": "en", "category": "general"},
    {"name": "Sydney Morning Herald","url": "https://www.smh.com.au/rss/feed.xml",                         "region": "australia", "lang": "en", "category": "general"},
    {"name": "news.com.au",        "url": "https://www.news.com.au/content-feeds/latest-news-national/",  "region": "australia", "lang": "en", "category": "general"},

    # ── Canada ────────────────────────────────────────────────────────────────
    {"name": "CBC News",           "url": "https://www.cbc.ca/cmlink/rss-topstories",                     "region": "canada", "lang": "en", "category": "general"},
    {"name": "Global News",        "url": "https://globalnews.ca/feed/",                                  "region": "canada", "lang": "en", "category": "general"},
    {"name": "Toronto Star",       "url": "https://www.thestar.com/content/thestar/feed.rss",              "region": "canada", "lang": "en", "category": "general"},
    {"name": "National Post",      "url": "https://nationalpost.com/feed/",                               "region": "canada", "lang": "en", "category": "general"},

    # ── Europe ────────────────────────────────────────────────────────────────
    {"name": "Euronews",           "url": "https://www.euronews.com/rss?format=mrss&level=theme&name=news","region": "europe", "lang": "en", "category": "general"},
    {"name": "POLITICO EU",        "url": "https://www.politico.eu/feed/",                                "region": "europe", "lang": "en", "category": "politics"},
    {"name": "DW Europe",          "url": "https://rss.dw.com/rdf/rss-en-eu",                             "region": "europe", "lang": "en", "category": "general"},
    {"name": "The Local",          "url": "https://feeds.thelocal.com/rss/en",                            "region": "europe", "lang": "en", "category": "general"},
    {"name": "EUobserver",         "url": "https://euobserver.com/rss.xml",                               "region": "europe", "lang": "en", "category": "politics"},

    # ── Middle East ───────────────────────────────────────────────────────────
    {"name": "Arab News",          "url": "https://www.arabnews.com/rss.xml",                             "region": "middle-east", "lang": "en", "category": "general"},
    {"name": "Jerusalem Post",     "url": "https://www.jpost.com/rss/rssfeedsheadlines.aspx",             "region": "middle-east", "lang": "en", "category": "general"},
    {"name": "Al Monitor",         "url": "https://www.al-monitor.com/rss",                               "region": "middle-east", "lang": "en", "category": "general"},
    {"name": "Gulf News",          "url": "https://gulfnews.com/rss/uae",                                 "region": "middle-east", "lang": "en", "category": "general"},
    {"name": "Daily Sabah",        "url": "https://www.dailysabah.com/feeds.rss",                         "region": "middle-east", "lang": "en", "category": "general"},
    {"name": "Haaretz",            "url": "https://www.haaretz.com/cmlink/1.628765",                      "region": "middle-east", "lang": "en", "category": "general"},

    # ── Africa ────────────────────────────────────────────────────────────────
    {"name": "AllAfrica",          "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf","region": "africa", "lang": "en", "category": "general"},
    {"name": "Mail & Guardian",    "url": "https://mg.co.za/feed/",                                      "region": "africa", "lang": "en", "category": "general"},
    {"name": "The East African",   "url": "https://www.theeastafrican.co.ke/tea/rss",                     "region": "africa", "lang": "en", "category": "general"},
    {"name": "Daily Nation Kenya", "url": "https://nation.africa/rss/",                                   "region": "africa", "lang": "en", "category": "general"},

    # ── Latin America ─────────────────────────────────────────────────────────
    {"name": "Mercopress",         "url": "https://en.mercopress.com/rss",                                "region": "latam",  "lang": "en", "category": "general"},
    {"name": "Rio Times",          "url": "https://riotimesonline.com/feed/",                             "region": "latam",  "lang": "en", "category": "general"},
    {"name": "Buenos Aires Herald","url": "https://buenosairesherald.com/feed",                           "region": "latam",  "lang": "en", "category": "general"},
    {"name": "El País English",    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada", "region": "latam", "lang": "en", "category": "general"},

    # ── Asia Pacific ──────────────────────────────────────────────────────────
    {"name": "Japan Times",        "url": "https://www.japantimes.co.jp/feed/",                           "region": "asia",   "lang": "en", "category": "general"},
    {"name": "Straits Times",      "url": "https://www.straitstimes.com/news/world/rss.xml",              "region": "asia",   "lang": "en", "category": "general"},
    {"name": "SCMP",               "url": "https://www.scmp.com/rss/91/feed",                             "region": "asia",   "lang": "en", "category": "general"},
    {"name": "Nikkei Asia",        "url": "https://asia.nikkei.com/rss/feed/nar",                         "region": "asia",   "lang": "en", "category": "business"},
    {"name": "Korea Herald",       "url": "https://www.koreaherald.com/rss/rss.xml",                      "region": "asia",   "lang": "en", "category": "general"},
    {"name": "Jakarta Post",       "url": "https://www.thejakartapost.com/feed",                          "region": "asia",   "lang": "en", "category": "general"},
    {"name": "Dawn (Pakistan)",    "url": "https://www.dawn.com/feeds/home",                              "region": "asia",   "lang": "en", "category": "general"},
    {"name": "Channel NewsAsia",   "url": "https://www.channelnewsasia.com/rssfeeds/8395986",             "region": "asia",   "lang": "en", "category": "general"},
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Verax/1.0)"}


def _extract_text(url: str) -> str:
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            r = client.get(url, headers=_HEADERS)
            soup = BeautifulSoup(r.text, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            return " ".join(p.get_text(strip=True) for p in soup.find_all("p"))[:3000]
    except Exception:
        return ""


def fetch_all_feeds() -> None:
    db = SessionLocal()
    try:
        for source in RSS_SOURCES:
            _fetch_feed(source, db)
    finally:
        db.close()


def _parse_author(entry) -> str | None:
    # Try standard author field, then Dublin Core creator
    author = getattr(entry, "author", None) or getattr(entry, "dc_creator", None)
    if not author and getattr(entry, "authors", None):
        author = entry.authors[0].get("name", "")
    return author[:200] if author else None


def _parse_source_tags(entry) -> str | None:
    tags = getattr(entry, "tags", None)
    if not tags:
        return None
    terms = [t.get("term", "") for t in tags if t.get("term")]
    return ", ".join(terms)[:500] if terms else None


def _fetch_feed(source: dict, db) -> None:
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:settings.articles_per_feed]:
            url = entry.get("link", "").strip()
            if not url or db.query(Article).filter(Article.url == url).first():
                continue
            db.add(Article(
                title=entry.get("title", "")[:500],
                url=url,
                text=_extract_text(url),
                source_name=source["name"],
                region=source["region"],
                language=source["lang"],
                category=source["category"],
                published_at=_parse_date(entry),
                rss_summary=entry.get("summary", "") or None,
                author=_parse_author(entry),
                source_tags=_parse_source_tags(entry),
            ))
        db.commit()
    except Exception:
        db.rollback()
