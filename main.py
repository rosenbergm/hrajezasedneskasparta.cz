import csv
import json
import os
import secrets
import requests
from typing import Annotated

from bs4 import BeautifulSoup as soup

import dotenv
import httpx
from fastapi import (
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    status,
    BackgroundTasks,
)
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from datetime import date

import requests


dotenv.load_dotenv()

app = FastAPI()

admin_auth = HTTPBasic()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    resp = requests.get("https://www.kdykde.cz/calendar/misto/cr/praha/epet-arena")
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

    today = date.today()

    playing_today = today in events
    result = "Ano" if playing_today else "Ne"

    return templates.TemplateResponse('index.jinja.html', {
        "request": request,
        "result": result,
        "next_events_text": "A bude hrát i:" if playing_today else "Bude hrát:",
        "dates": [date.strftime(e, '%d. %m. %Y') for e in (events[1:] if playing_today else events)]
    })
