import json
import urllib.request
from pathlib import Path

CHANNELS_URL = "https://iptv-org.github.io/api/channels.json"
STREAMS_URL = "https://iptv-org.github.io/api/streams.json"
LOGOS_URL = "https://iptv-org.github.io/api/logos.json"

COUNTRIES = {
    "tr": "Türkiye",
    "de": "Almanya",
    "gb": "Birleşik Krallık",
    "us": "Amerika Birleşik Devletleri",
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
    print(f"Downloading {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "reefquiet/iptv-playlists"
        }
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    print("Loading IPTV data...")

    channels = download_json(CHANNELS_URL)
    streams = download_json(STREAMS_URL)
    logos = download_json(LOGOS_URL)

    # Kanal ID -> stream
    stream_map = {}

    for stream in streams:
        channel_id = stream.get("channel")

        if not channel_id:
            continue

        url = stream.get("url")

        if not url:
            continue

        # İlk geçerli stream'i kullan
        if channel_id not in stream_map:
            stream_map[channel_id] = url

    # Kanal ID -> logo
    logo_map = {}

    for logo in logos:
        channel_id = logo.get("channel")
        url = logo.get("url")

        if channel_id and url and channel_id not in logo_map:
            logo_map[channel_id] = url

    output_dir = Path("countries")
    output_dir.mkdir(parents=True, exist_ok=True)

    for country_code, country_name in COUNTRIES.items():

        print(f"\nCreating {country_name} ({country_code})")

        country_channels = []

        for channel in channels:

            if channel.get("country", "").lower() != country_code:
                continue

            if channel.get("is_nsfw"):
                continue

            channel_id = channel.get("id")

            if not channel_id:
                continue

            stream_url = stream_map.get(channel_id)

            if not stream_url:
                continue

            categories = channel.get("categories", [])

            category = "general"

            for cat in categories:
                if cat in CATEGORY_MAP:
                    category = cat
                    break

            country_channels.append({
                "id": channel_id,
                "name": channel.get("name", channel_id),
                "logo": logo_map.get(channel_id, ""),
                "category": category,
                "url": stream_url,
            })

        # Kanal adına göre sırala
        country_channels.sort(
            key=lambda x: (
                CATEGORY_MAP.get(x["category"], "Genel"),
                x["name"].lower()
            )
        )

        output_file = output_dir / f"{country_code}.m3u"

        with output_file.open("w", encoding="utf-8") as file:

            file.write("#EXTM3U\n")

            for channel in country_channels:

                category_name = CATEGORY_MAP.get(
                    channel["category"],
                    "Genel"
                )

                logo = channel["logo"]

                attributes = [
                    f'tvg-id="{channel["id"]}"',
                    f'tvg-name="{channel["name"]}"',
                ]

                if logo:
                    attributes.append(
                        f'tvg-logo="{logo}"'
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
            f"Created {output_file}: "
            f"{len(country_channels)} channels"
        )


if __name__ == "__main__":
    main()
