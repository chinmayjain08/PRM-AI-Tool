"""
Central HTTP client. All server communication goes through here.
Stores the JWT token after login.
Raises ServerError on bad HTTP responses.
Screens never import 'requests' directly.
"""

import requests


class ServerError(Exception):
    """Raised when the server returns an error response."""
    pass


class HttpClient:
    _token:    str = ""
    _base_url: str = "http://localhost:8000"

    @classmethod
    def set_token(cls, token: str) -> None:
        cls._token = token

    @classmethod
    def _headers(cls) -> dict:
        return {"Authorization": f"Bearer {cls._token}"} if cls._token else {}

    @classmethod
    def get(cls, endpoint: str, params: dict = None) -> dict:
        try:
            response = requests.get(f"{cls._base_url}{endpoint}", headers=cls._headers(), params=params)
            return cls._handle_response(response)
        except requests.RequestException as error:
            raise ServerError(f"Connection failed: {str(error)}")

    @classmethod
    def post(cls, endpoint: str, body: dict = None) -> dict:
        try:
            response = requests.post(f"{cls._base_url}{endpoint}", headers=cls._headers(), json=body)
            return cls._handle_response(response)
        except requests.RequestException as error:
            raise ServerError(f"Connection failed: {str(error)}")

    @classmethod
    def put(cls, endpoint: str, body: dict = None) -> dict:
        try:
            response = requests.put(f"{cls._base_url}{endpoint}", headers=cls._headers(), json=body)
            return cls._handle_response(response)
        except requests.RequestException as error:
            raise ServerError(f"Connection failed: {str(error)}")

    @classmethod
    def delete(cls, endpoint: str, params: dict = None) -> dict:
        try:
            response = requests.delete(f"{cls._base_url}{endpoint}", headers=cls._headers(), params=params)
            return cls._handle_response(response)
        except requests.RequestException as error:
            raise ServerError(f"Connection failed: {str(error)}")

    @classmethod
    def _handle_response(cls, response: requests.Response) -> dict:
        if response.ok:
            try:
                return response.json()
            except ValueError:
                return {}
        try:
            detail = response.json().get("detail", f"Server error {response.status_code}")
            if isinstance(detail, list):
                # Pydantic validation errors can be a list of dicts
                messages = []
                for error in detail:
                    loc = " -> ".join(str(l) for l in error.get("loc", []))
                    msg = error.get("msg", "Validation error")
                    messages.append(f"{loc}: {msg}")
                detail = "; ".join(messages)
            raise ServerError(detail)
        except (ValueError, AttributeError):
            raise ServerError(response.text or f"Server error {response.status_code}")
