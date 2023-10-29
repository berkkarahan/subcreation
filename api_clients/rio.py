import requests


def get_mplus_runs(season, region, affixes_slug, dungeon_slug, page):
    base_url = "https://raider.io/api/v1/mythic-plus/runs?"
    url = "{}season={}&region={}&affixes={}&dungeon={}&page={}".format(
        base_url,
        season,
        region,
        affixes_slug,
        dungeon_slug,
        page,
    )
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
