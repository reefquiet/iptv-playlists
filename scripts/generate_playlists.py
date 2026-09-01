import json
import urllib.request
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

CHANNELS_URL = "https://iptv-org.github.io/api/channels.json"
STREAMS_URL = "https://iptv-org.github.io/api/streams.json"
LOGOS_URL = "https://iptv-org.github.io/api/logos.json"

# İlk etapta yayına alacağımız ülkeler.
COUNTRIES = {
    "tr": "Türkiye",
    "de": "Almanya",
    "gb": "Birleşik Krallık",
    "us": "Amerika Birleşik Devletleri",
    "fr": "Fransa",
    "it": "İtalya",
    "es": "İspanya",
    "pt": "Portekiz",
    "nl": "Hollanda",
    "be": "Belçika",
    "at": "Avusturya",
    "ch": "İsviçre",
    "pl": "Polonya",
    "se": "İsveç",
    "no": "Norveç",
    "dk": "Danimarka",
    "fi": "Finlandiya",
    "cz": "Çekya",
    "gr": "Yunanistan",
    "ro": "Romanya",
    "bg": "Bulgaristan",
}

CATEGORY_MAP = {
    "general": "Genel",
    "news": "Haber",
    "sports": "Spor",
    "documentary": "Belgesel",
    "movies": "Film",
    "series": "Dizi",
    "music": "Müzik",
    "kids": "Çocuk",
    "entertainment": "Eğlence",
    "culture": "Kültür",
    "religious": "Din",
    "shop": "Alışveriş",
    "travel": "Seyahat",
    "science": "Bilim",
    "education": "Eğitim",
    "weather": "Hava Durumu",
    "business": "İş",
    "lifestyle": "Yaşam",
    "outdoor": "Outdoor",
    "family": "Aile",
    "animation": "Animasyon",
    "classic": "Klasik",
    "comedy": "Komedi",
    "cooking": "Yemek",
}


def download_json(url):
    print(f"Downloading: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "reefquiet-iptv-playlists/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def valid_stream_url(url):
    if not url:
        return False

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.netloc:
            return False

        return True

    except Exception:
        return False


def choose_category(categories):
    if not categories:
        return "general"

    for category in categories:
        if category in CATEGORY_MAP:
            return category

    return "general"


def main():

    channels = download_json(CHANNELS_URL)
    streams = download_json(STREAMS_URL)
    logos = download_json(LOGOS_URL)

    print(f"Channels: {len(channels)}")
    print(f"Streams: {len(streams)}")
    print(f"Logos: {len(logos)}")

    # --------------------------------------------------
    # STREAMS
    # --------------------------------------------------

    streams_by_channel = defaultdict(list)

    for stream in streams:

        channel_id = stream.get("channel")
        url = stream.get("url")

        if not channel_id:
            continue

        if not valid_stream_url(url):
            continue

        streams_by_channel[channel_id].append(url)

    # --------------------------------------------------
    # LOGOS
    # --------------------------------------------------

    logo_map = {}

    for logo in logos:

        channel_id = logo.get("channel")
        url = logo.get("url")

        if not channel_id:
            continue

        if not valid_stream_url(url):
            continue

        if channel_id not in logo_map:
            logo_map[channel_id] = url

    output_dir = Path("countries")
    output_dir.mkdir(exist_ok=True)

    # --------------------------------------------------
    # COUNTRIES
    # --------------------------------------------------

    for country_code, country_name in COUNTRIES.items():

        print()
        print("=" * 50)
        print(f"{country_name} ({country_code})")
        print("=" * 50)

        country_channels = []

        for channel in channels:

            channel_country = channel.get("country", "")

            if channel_country.lower() != country_code:
                continue

            if channel.get("is_nsfw"):
                continue

            channel_id = channel.get("id")

            if not channel_id:
                continue

            channel_streams = streams_by_channel.get(
                channel_id,
                []
            )

            if not channel_streams:
                continue

            # Şimdilik kanal başına bir stream.
            stream_url = channel_streams[0]

            name = channel.get(
                "name",
                channel_id
            )

            categories = channel.get(
                "categories",
                []
            )

            category = choose_category(categories)

            country_channels.append({
                "id": channel_id,
                "name": name,
                "logo": logo_map.get(
                    channel_id,
                    ""
                ),
                "category": category,
                "url": stream_url,
            })

        # --------------------------------------------------
        # DUPLICATE CLEANUP
        # --------------------------------------------------

        unique_channels = {}

        for channel in country_channels:

            key = channel["id"]

            if key not in unique_channels:
                unique_channels[key] = channel

        country_channels = list(
            unique_channels.values()
        )

        # --------------------------------------------------
        # SORT
        # --------------------------------------------------

        country_channels.sort(
            key=lambda channel: (
                CATEGORY_MAP.get(
                    channel["category"],
                    "Genel"
                ),
                channel["name"].lower()
            )
        )

        # --------------------------------------------------
        # WRITE M3U
        # --------------------------------------------------

        output_file = (
            output_dir /
            f"{country_code}.m3u"
        )

        with output_file.open(
            "w",
            encoding="utf-8"
        ) as file:

            file.write("#EXTM3U\n")

            for channel in country_channels:

                category_name = CATEGORY_MAP.get(
                    channel["category"],
                    "Genel"
                )

                attributes = [
                    f'tvg-id="{channel["id"]}"',
                    f'tvg-name="{channel["name"]}"',
                ]

                if channel["logo"]:
                    attributes.append(
                        f'tvg-logo="{channel["logo"]}"'
                    )

                attributes.append(
                    f'group-title="{category_name}"'
                )

                file.write(
                    "#EXTINF:-1 "
                    + " ".join(attributes)
                    + f',{channel["name"]}\n'
                )

                file.write(
                    channel["url"]
                    + "\n"
                )

        print(
            f"Created: {output_file}"
        )

        print(
            f"Channels: {len(country_channels)}"
        )


if __name__ == "__main__":
    main()
