import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from dateutil import parser

# ---------- CONFIG ----------
CITY = "Delhi"
URL = "https://in.bookmyshow.com/explore/events-delhi"
SHEET_NAME = "events_data"
# ----------------------------

def connect_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


def fetch_events():
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    cards = soup.select("div.sc-7o7nez-0")
    for card in cards:
        try:
            name = card.select_one("h3").text.strip()
            link = "https://in.bookmyshow.com" + card.a["href"]
            category = card.select_one("span").text.strip()

            events.append({
                "event_name": name,
                "date": "Upcoming",
                "venue": "TBD",
                "city": CITY,
                "category": category,
                "url": link
            })
        except:
            continue

    return events


def update_sheet(events, sheet):
    existing = sheet.get_all_records()
    existing_urls = {row["url"]: i + 2 for i, row in enumerate(existing)}

    today = datetime.today().strftime("%Y-%m-%d")

    for event in events:
        if event["url"] in existing_urls:
            row = existing_urls[event["url"]]
            sheet.update(f"A{row}:H{row}", [[
                event["event_name"],
                event["date"],
                event["venue"],
                event["city"],
                event["category"],
                event["url"],
                "Upcoming",
                today
            ]])
        else:
            sheet.append_row([
                event["event_name"],
                event["date"],
                event["venue"],
                event["city"],
                event["category"],
                event["url"],
                "Upcoming",
                today
            ])

    # Mark expired (basic logic)
    for i, row in enumerate(existing, start=2):
        if row["date"] != "Upcoming":
            try:
                event_date = parser.parse(row["date"]).date()
                if event_date < datetime.today().date():
                    sheet.update(f"G{i}", "Expired")
            except:
                pass


def main():
    sheet = connect_sheet()
    events = fetch_events()
    update_sheet(events, sheet)
    print("Events updated successfully")


if __name__ == "__main__":
    main()
