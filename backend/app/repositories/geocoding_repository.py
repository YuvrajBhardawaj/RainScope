import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GeocodingRepository:
    ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"

    def search(self, query: str) -> list[dict]:
        params = urlencode({"name": query, "count": 8, "language": "en", "format": "json"})
        request = Request(
            f"{self.ENDPOINT}?{params}",
            headers={"User-Agent": "RainScope/0.1 (precipitation forecast project)"},
        )
        try:
            with urlopen(request, timeout=5.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError("The geocoding service could not be reached") from error
        return payload.get("results", [])
