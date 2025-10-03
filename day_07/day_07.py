import geopandas as gp
from bs4 import BeautifulSoup
import requests
import pandas as pd

world = gp.read_file("data/world.geojson")

world_gdf = gp.GeoDataFrame(world)

url = "https://cphof.org/contests"
url_part = "https://cphof.org"
response = requests.get(url)
html = response.content
soup = BeautifulSoup(html, "html.parser")

table = soup.find(
    "table", class_="table table-bordered table-striped table-hover w-auto"
)

rows = table.find_all("tr")
data = []

for row in rows:
    cols = row.find_all(["td", "th"])
    cols_text = [ele.text.strip() for ele in cols]
    data.append(cols_text)

df = pd.DataFrame(data[1:], columns=data[0])

links = []
if table:
    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all(["td", "th"])
        for cell in cells:
            anchor_tag = cell.find("a")
            if anchor_tag and "href" in anchor_tag.attrs:
                links.append(f"{url_part}{anchor_tag['href']}")

df["links"] = links

winners = []
headers = None

for i, link in enumerate(links):
    response = requests.get(link)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find(
        "table", class_="table table-bordered table-striped table-hover w-auto"
    )
    winners_table = soup.find(
        "table", class_="table table-bordered table-striped table-hover w-auto"
    )
    if winners_table:
        winner_rows = winners_table.find_all("tr")
        winner_data = [
            [ele.text.strip() for ele in row.find_all(["td", "th"])]
            for row in winner_rows
        ]

        if headers is None:
            headers = winner_data[0]

        for row in winner_data[1:]:
            if len(row) < len(headers):
                row.extend([""] * (len(headers) - len(row)))
            elif len(row) > len(headers):
                row = row[: len(headers)]

            row.extend(
                [
                    df.loc[i, "Date"],
                    df.loc[i, "Contest"],
                    df.loc[i, "Location"],
                ]
            )
            winners.append(row)

custom_headers = [
    "rank",
    "programmer_country",
    "programmer_name",
    "score",
    "penalty",
    "prize",
    "date",
    "contest",
    "contest_location",
]

winners_df = pd.DataFrame(winners, columns=custom_headers)

best_countries = winners_df["programmer_country"].value_counts().reset_index()
best_countries.columns = ["Country", "Count"]

# geo_join = world.merge(
#     best_countries, left_on="COUNTRY", right_on="programmer_country", how="left"
# )

# winners_df.to_csv("data/best_coders.csv", index=False)

best_countries.to_csv("data/number_of_coders.csv", index=False)

# geo_join.to_file("data/coder_geo.gpkg", layer="my_layer", driver="GPKG")
