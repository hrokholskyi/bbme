import time

import httpx

from bbme.models import BitbucketError, Config, PRResult, RepoInfo


class BitbucketClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        # App passwords use Basic Auth (username:app_password)
        # OAuth/workspace tokens use Bearer Auth
        if config.username:
            auth = httpx.BasicAuth(config.username, config.token)
            headers = {}
        else:
            auth = None
            headers = {"Authorization": f"Bearer {config.token}"}
        self._client = httpx.Client(
            base_url=config.base_url,
            auth=auth,
            headers=headers,
            timeout=30.0,
        )

    def _request(self, method: str, url: str, **kwargs) -> dict:
        retries = 3
        for attempt in range(retries):
            try:
                resp = self._client.request(method, url, **kwargs)
                if resp.status_code == 401:
                    raise BitbucketError("Authentication failed. Check your token in config.")
                if resp.status_code == 429:
                    if attempt < retries - 1:
                        wait = 2 ** (attempt + 1)
                        time.sleep(wait)
                        continue
                    raise BitbucketError("Rate limited by Bitbucket API. Try again later.")
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                raise BitbucketError(f"Bitbucket API error {e.response.status_code}: {e.response.text}") from e
            except httpx.RequestError as e:
                raise BitbucketError(f"Request failed: {e}") from e
        raise BitbucketError("Request failed after retries")

    def _extract_repo_from_value(self, value: dict) -> tuple[str, str, str] | None:
        """Extract (workspace, slug, file_path) from a code search result.

        Tries multiple known response structures since the Bitbucket API
        docs are inconsistent about the exact nesting.
        """
        file_obj = value.get("file", {})
        file_path = file_obj.get("path", "")

        # Strategy 1: file.commit.repository (some API versions)
        repo_data = file_obj.get("commit", {}).get("repository", {})
        if repo_data:
            full_name = repo_data.get("full_name", "")
            if full_name and "/" in full_name:
                ws, slug = full_name.split("/", 1)
                return ws, slug, file_path

        # Strategy 2: top-level repository key
        repo_data = value.get("repository", {})
        if repo_data:
            full_name = repo_data.get("full_name", "")
            if full_name and "/" in full_name:
                ws, slug = full_name.split("/", 1)
                return ws, slug, file_path

        # Strategy 3: parse from file.links.self.href
        # e.g. https://api.bitbucket.org/2.0/repositories/workspace/slug/src/hash/path
        self_href = file_obj.get("links", {}).get("self", {}).get("href", "")
        if "/repositories/" in self_href:
            parts = self_href.split("/repositories/", 1)[1].split("/")
            if len(parts) >= 2:
                return parts[0], parts[1], file_path

        return None

    def search_code(self, query: str) -> list[RepoInfo]:
        workspace = self._config.workspace
        repos: dict[str, RepoInfo] = {}
        url = f"/workspaces/{workspace}/search/code"
        params = {"search_query": query, "pagelen": 100}
        first_page = True

        while True:
            data = self._request("GET", url, params=params)

            if first_page and not data.get("values"):
                # Debug: show what we got back
                size = data.get("size", 0)
                if size == 0:
                    break  # Genuinely no results

            for value in data.get("values", []):
                result = self._extract_repo_from_value(value)
                if result is None:
                    continue
                repo_ws, slug, file_path = result

                if slug not in repos:
                    full_name = f"{repo_ws}/{slug}"
                    clone_url = f"https://bitbucket.org/{full_name}.git"
                    repos[slug] = RepoInfo(
                        workspace=repo_ws,
                        slug=slug,
                        clone_url_https=clone_url,
                    )
                if file_path:
                    repos[slug].files_matched.append(file_path)

            first_page = False
            next_url = data.get("next")
            if not next_url:
                break
            # next_url is absolute; strip the base to keep using the configured base_url
            if next_url.startswith(self._config.base_url):
                url = next_url[len(self._config.base_url):]
            else:
                url = next_url
            params = {}  # params are already in the next_url

        return list(repos.values())

    def list_branches(self, repo_slug: str) -> list[str]:
        workspace = self._config.workspace
        url = f"/repositories/{workspace}/{repo_slug}/refs/branches"
        branches: list[str] = []
        params: dict = {"pagelen": 100}

        while True:
            data = self._request("GET", url, params=params)
            for branch in data.get("values", []):
                name = branch.get("name", "")
                if name:
                    branches.append(name)

            next_url = data.get("next")
            if not next_url:
                break
            if next_url.startswith(self._config.base_url):
                url = next_url[len(self._config.base_url):]
            else:
                url = next_url
            params = {}

        return branches

    def create_pull_request(
        self,
        repo_slug: str,
        title: str,
        source_branch: str,
        destination_branch: str,
        description: str = "",
    ) -> PRResult:
        workspace = self._config.workspace
        url = f"/repositories/{workspace}/{repo_slug}/pullrequests"
        body = {
            "title": title,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": destination_branch}},
            "description": description,
        }
        data = self._request("POST", url, json=body)
        pr_id = data.get("id", 0)
        pr_url = f"https://bitbucket.org/{workspace}/{repo_slug}/pull-requests/{pr_id}"
        return PRResult(
            repo_slug=repo_slug,
            pr_id=pr_id,
            url=pr_url,
            title=title,
        )

    def close(self) -> None:
        self._client.close()
