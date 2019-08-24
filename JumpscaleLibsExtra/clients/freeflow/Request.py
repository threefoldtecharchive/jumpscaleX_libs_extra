import requests


class Request(object):
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    @property
    def headers(self):
        if not hasattr(self, "_headers"):
            self._headers = {"Content-Type": "application/json", "Authorization": "Bearer {0}".format(self.api_key)}

        return self._headers

    @property
    def session(self):
        if not hasattr(self, "_session"):
            self._session = requests.Session()
            self._session.headers.update(self.headers)
        return self._session

    def respond(self, response, formatter=None):
        if response.status_code == 404:
            return {"code": 404, "message": "{} not found".format(response.url), "name": "Not Found"}
        if response.status_code == 401:
            return {"code": 401, "message": "Check your API key", "name": "Not Authorized"}
        if response.status_code == 500:
            return {"code": 500, "message": "", "name": "Internal Server Error"}

        result = response.json()
        if formatter:
            return formatter(result)
        return result

    def ensure_path(self, path):
        if not path.startswith("/"):
            path = "/{}".format(path)
        return path

    def get(self, path, formatter=None, **kwargs):
        url = "{0}{1}".format(self.base_url, self.ensure_path(path))

        if kwargs:
            url = "{}?".format(url)
            for arg, value in kwargs.items():
                url = url + "{}={}&".format(arg, value)
            url = url.strip("&")

        return self.respond(self.session.get(url), formatter)

    def post(self, path, payload, formatter=None):
        return self.respond(
            self.session.post("{0}{1}".format(self.base_url, self.ensure_path(path)), json.dumps(payload)), formatter
        )

    def put(self, path, payload, formatter=None):
        return self.respond(
            self.session.put("{0}{1}".format(self.base_url, self.ensure_path(path)), json.dumps(payload)), formatter
        )

    def patch(self, path, payload, formatter=None):
        return self.respond(
            self.session.patch("{0}{1}".format(self.base_url, self.ensure_path(path)), json.dumps(payload)), formatter
        )

    def delete(self, path, formatter=None):
        return self.respond(self.session.delete("{0}{1}".format(self.base_url, self.ensure_path(path))), formatter)
