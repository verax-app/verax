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
    # Global — General
    {"name": "BBC News",          "url": "http://feeds.bbci.co.uk/news/rss.xml",                          "region": "global", "lang": "en", "category": "general"},
    {"name": "Reuters",           "url": "https://feeds.reuters.com/reuters/topNews",                     "region": "global", "lang": "en", "category": "general"},
    {"name": "Al Jazeera",        "url": "https://www.aljazeera.com/xml/rss/all.xml",                    "region": "global", "lang": "en", "category": "general"},
    {"name": "The Guardian",      "url": "https://www.theguardian.com/world/rss",                        "region": "global", "lang": "en", "category": "general"},
    {"name": "Deutsche Welle",    "url": "https://rss.dw.com/rdf/rss-en-all",                            "region": "global", "lang": "en", "category": "general"},
    {"name": "France 24",         "url": "https://www.france24.com/en/rss",                              "region": "global", "lang": "en", "category": "general"},

    # Tech
    {"name": "HackerNews",        "url": "https://hnrss.org/frontpage",                                  "region": "global", "lang": "en", "category": "tech"},
    {"name": "TechCrunch",        "url": "https://techcrunch.com/feed/",                                 "region": "global", "lang": "en", "category": "tech"},
    {"name": "Wired",             "url": "https://www.wired.com/feed/rss",                               "region": "global", "lang": "en", "category": "tech"},
    {"name": "The Verge",         "url": "https://www.theverge.com/rss/index.xml",                       "region": "global", "lang": "en", "category": "tech"},
    {"name": "Ars Technica",      "url": "https://feeds.arstechnica.com/arstechnica/index",              "region": "global", "lang": "en", "category": "tech"},
    {"name": "MIT Tech Review",   "url": "https://www.technologyreview.com/feed/",                       "region": "global", "lang": "en", "category": "tech"},
    {"name": "VentureBeat",       "url": "https://feeds.feedburner.com/venturebeat/SZYF",                "region": "global", "lang": "en", "category": "tech"},

    # Science
    {"name": "NASA",              "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",               "region": "global", "lang": "en", "category": "science"},
    {"name": "New Scientist",     "url": "https://www.newscientist.com/feed/home/",                      "region": "global", "lang": "en", "category": "science"},
    {"name": "Science Daily",     "url": "https://www.sciencedaily.com/rss/all.xml",                     "region": "global", "lang": "en", "category": "science"},
    {"name": "Nature",            "url": "https://www.nature.com/nature.rss",                            "region": "global", "lang": "en", "category": "science"},

    # Health
    {"name": "WHO",               "url": "https://www.who.int/rss-feeds/news-english.xml",               "region": "global", "lang": "en", "category": "health"},
    {"name": "WebMD",             "url": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC", "region": "global", "lang": "en", "category": "health"},
    {"name": "Medical News Today","url": "https://www.medicalnewstoday.com/rss/wordnews.xml",            "region": "global", "lang": "en", "category": "health"},

    # Business
    {"name": "Financial Times",   "url": "https://www.ft.com/rss/home",                                  "region": "global", "lang": "en", "category": "business"},
    {"name": "Bloomberg",         "url": "https://feeds.bloomberg.com/markets/news.rss",                 "region": "global", "lang": "en", "category": "business"},
    {"name": "Forbes",            "url": "https://www.forbes.com/real-time/feed2/",                      "region": "global", "lang": "en", "category": "business"},

    # Environment
    {"name": "The Guardian Env",  "url": "https://www.theguardian.com/environment/rss",                  "region": "global", "lang": "en", "category": "environment"},
    {"name": "Climate Home News", "url": "https://www.climatechangenews.com/feed/",                      "region": "global", "lang": "en", "category": "environment"},

    # Sports
    {"name": "ESPN",              "url": "https://www.espn.com/espn/rss/news",                           "region": "global", "lang": "en", "category": "sports"},
    {"name": "BBC Sport",         "url": "http://feeds.bbci.co.uk/sport/rss.xml",                        "region": "global", "lang": "en", "category": "sports"},
    {"name": "Sky Sports",        "url": "https://www.skysports.com/rss/12040",                          "region": "global", "lang": "en", "category": "sports"},

    # Entertainment
    {"name": "Variety",           "url": "https://variety.com/feed/",                                   "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Hollywood Reporter","url": "https://www.hollywoodreporter.com/feed/",                      "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Rolling Stone",     "url": "https://www.rollingstone.com/feed/",                          "region": "global", "lang": "en", "category": "entertainment"},
    {"name": "Pitchfork",         "url": "https://pitchfork.com/feed/feed-news/rss",                    "region": "global", "lang": "en", "category": "entertainment"},

    # Gaming
    {"name": "IGN",               "url": "https://feeds.ign.com/ign/games-all",                         "region": "global", "lang": "en", "category": "gaming"},
    {"name": "Polygon",           "url": "https://www.polygon.com/rss/index.xml",                       "region": "global", "lang": "en", "category": "gaming"},
    {"name": "Eurogamer",         "url": "https://www.eurogamer.net/?format=rss",                       "region": "global", "lang": "en", "category": "gaming"},

    # Crypto
    {"name": "CoinDesk",          "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",             "region": "global", "lang": "en", "category": "crypto"},
    {"name": "CoinTelegraph",     "url": "https://cointelegraph.com/rss",                               "region": "global", "lang": "en", "category": "crypto"},
    {"name": "Decrypt",           "url": "https://decrypt.co/feed",                                     "region": "global", "lang": "en", "category": "crypto"},

    # India
    {"name": "The Hindu",         "url": "https://www.thehindu.com/feeder/default.rss",                  "region": "india",  "lang": "en", "category": "general"},
    {"name": "NDTV",              "url": "https://feeds.feedburner.com/ndtvnews-top-stories",             "region": "india",  "lang": "en", "category": "general"},
    {"name": "Times of India",    "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",   "region": "india",  "lang": "en", "category": "general"},
    {"name": "Indian Express",    "url": "https://indianexpress.com/feed/",                              "region": "india",  "lang": "en", "category": "general"},
    {"name": "Hindustan Times",   "url": "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",       "region": "india",  "lang": "en", "category": "general"},
    {"name": "The Wire",          "url": "https://thewire.in/feed",                                      "region": "india",  "lang": "en", "category": "politics"},
    {"name": "Mint",              "url": "https://www.livemint.com/rss/news",                            "region": "india",  "lang": "en", "category": "business"},

    # US
    {"name": "NPR",               "url": "https://feeds.npr.org/1001/rss.xml",                           "region": "us",     "lang": "en", "category": "general"},
    {"name": "AP News",           "url": "https://rsshub.app/apnews/topics/apf-topnews",                 "region": "us",     "lang": "en", "category": "general"},
    {"name": "Washington Post",   "url": "https://feeds.washingtonpost.com/rss/world",                   "region": "us",     "lang": "en", "category": "general"},
    {"name": "NY Times",          "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",    "region": "us",     "lang": "en", "category": "general"},
    {"name": "Politico",          "url": "https://www.politico.com/rss/politicopicks.xml",               "region": "us",     "lang": "en", "category": "politics"},

    # UK
    {"name": "The Guardian UK",   "url": "https://www.theguardian.com/uk/rss",                           "region": "uk",     "lang": "en", "category": "general"},
    {"name": "BBC UK",            "url": "http://feeds.bbci.co.uk/news/uk/rss.xml",                      "region": "uk",     "lang": "en", "category": "general"},
    {"name": "The Telegraph",     "url": "https://www.telegraph.co.uk/rss.xml",                          "region": "uk",     "lang": "en", "category": "general"},
    {"name": "The Independent",   "url": "https://www.independent.co.uk/news/rss",                       "region": "uk",     "lang": "en", "category": "general"},

    # Australia
    {"name": "ABC News AU",       "url": "https://www.abc.net.au/news/feed/51120/rss.xml",               "region": "australia", "lang": "en", "category": "general"},
    {"name": "The Guardian AU",   "url": "https://www.theguardian.com/australia-news/rss",               "region": "australia", "lang": "en", "category": "general"},
    {"name": "Sydney Morning Herald", "url": "https://www.smh.com.au/rss/feed.xml",                      "region": "australia", "lang": "en", "category": "general"},

    # Canada
    {"name": "CBC News",          "url": "https://www.cbc.ca/cmlink/rss-topstories",                    "region": "canada", "lang": "en", "category": "general"},
    {"name": "Global News",       "url": "https://globalnews.ca/feed/",                                 "region": "canada", "lang": "en", "category": "general"},
    {"name": "Toronto Star",      "url": "https://www.thestar.com/content/thestar/feed.rss",             "region": "canada", "lang": "en", "category": "general"},

    # Europe
    {"name": "Euronews",          "url": "https://www.euronews.com/rss?format=mrss&level=theme&name=news", "region": "europe", "lang": "en", "category": "general"},
    {"name": "POLITICO EU",       "url": "https://www.politico.eu/feed/",                               "region": "europe", "lang": "en", "category": "politics"},
    {"name": "DW Europe",         "url": "https://rss.dw.com/rdf/rss-en-eu",                            "region": "europe", "lang": "en", "category": "general"},
    {"name": "The Local",         "url": "https://feeds.thelocal.com/rss/en",                           "region": "europe", "lang": "en", "category": "general"},

    # Middle East
    {"name": "Arab News",         "url": "https://www.arabnews.com/rss.xml",                            "region": "middle-east", "lang": "en", "category": "general"},
    {"name": "Jerusalem Post",    "url": "https://www.jpost.com/rss/rssfeedsheadlines.aspx",            "region": "middle-east", "lang": "en", "category": "general"},
    {"name": "Al Monitor",        "url": "https://www.al-monitor.com/rss",                              "region": "middle-east", "lang": "en", "category": "general"},

    # Africa
    {"name": "AllAfrica",         "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "region": "africa", "lang": "en", "category": "general"},
    {"name": "Mail & Guardian",   "url": "https://mg.co.za/feed/",                                     "region": "africa", "lang": "en", "category": "general"},
    {"name": "The East African",  "url": "https://www.theeastafrican.co.ke/tea/rss",                    "region": "africa", "lang": "en", "category": "general"},

    # Latin America
    {"name": "Mercopress",        "url": "https://en.mercopress.com/rss",                               "region": "latam",  "lang": "en", "category": "general"},
    {"name": "Rio Times",         "url": "https://riotimesonline.com/feed/",                            "region": "latam",  "lang": "en", "category": "general"},
    {"name": "Buenos Aires Herald","url": "https://buenosairesherald.com/feed",                         "region": "latam",  "lang": "en", "category": "general"},

    # Asia Pacific
    {"name": "Japan Times",       "url": "https://www.japantimes.co.jp/feed/",                          "region": "asia",   "lang": "en", "category": "general"},
    {"name": "Straits Times",     "url": "https://www.straitstimes.com/news/world/rss.xml",             "region": "asia",   "lang": "en", "category": "general"},
    {"name": "SCMP",              "url": "https://www.scmp.com/rss/91/feed",                            "region": "asia",   "lang": "en", "category": "general"},
    {"name": "Nikkei Asia",       "url": "https://asia.nikkei.com/rss/feed/nar",                        "region": "asia",   "lang": "en", "category": "business"},
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
            ))
        db.commit()
    except Exception:
        db.rollback()
