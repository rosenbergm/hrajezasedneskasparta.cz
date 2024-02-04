from bs4 import BeautifulSoup as soup

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
)
from fastapi.security import HTTPBasic
from fastapi.templating import Jinja2Templates

from datetime import date
import requests
import dotenv
import asyncio

dotenv.load_dotenv()

app = FastAPI()

cache = {"date": None, "result": None, "next_events_text": None, "dates": []}
cache_lock = asyncio.Lock()

admin_auth = HTTPBasic()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    global cache
    today = date.today()

    async with cache_lock:
        if today == cache["date"]:
            return templates.TemplateResponse(
                "index.jinja.html",
                {
                    "request": request,
                    "result": cache["result"],
                    "next_events_text": cache["next_events_text"],
                    "dates": cache["dates"],
                },
            )
        else:
            resp = requests.get(
                "https://www.kdykde.cz/calendar/misto/cr/praha/epet-arena"
            )
            doc = soup(resp.content, "lxml")
            el = doc.find_all("div", attrs={"itemtype": "http://schema.org/Event"})

            events = []

            for event in el:
                dt = date(
                    *(
                        map(
                            int,
                            next(
                                s
                                for s in event.find(
                                    "div", class_="iota bold margin-bt-1x"
                                ).text.split("\n")
                                if s
                            )
                            .split(",")[0]
                            .split(".")[::-1],
                        )
                    )
                )

                events.append(dt)

            playing_today = today in events
            result = "Ano" if playing_today else "Ne"

            next_events_text = "A bude hrát i:" if playing_today else "Bude hrát:"

            dates = [
                date.strftime(e, "%d. %m. %Y")
                for e in (events[1:] if playing_today else events)
            ]

            cache = {
                "date": today,
                "result": result,
                "next_events_text": next_events_text,
                "dates": dates,
            }

            return templates.TemplateResponse(
                "index.jinja.html",
                {
                    "request": request,
                    "result": result,
                    "next_events_text": next_events_text,
                    "dates": dates,
                },
            )


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    data = """User-agent: *\nDisallow: /"""
    return data
