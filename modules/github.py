import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _safe_text(locator, default: Optional[str] = None) -> Optional[str]:
    """Return visible text safely without raising when a locator is missing."""
    if locator.count() == 0:
        return default
    try:
        value = locator.first.inner_text().strip()
    except Exception:
        return default
    return value or default


def _safe_attribute(locator, attribute: str, default: Optional[str] = None) -> Optional[str]:
    """Return an attribute value safely without raising when a locator is missing."""
    if locator.count() == 0:
        return default
    try:
        value = locator.first.get_attribute(attribute)
    except Exception:
        return default
    return value.strip() if isinstance(value, str) and value.strip() else default


def _extract_repository_section(page, heading_text: str) -> List[Dict[str, Any]]:
    """Extract repository cards from a named section with Playwright locators."""
    heading = page.locator("h2", has_text=heading_text).first
    if heading.count() == 0:
        return []

    # This uses the heading as the anchor point, then walks up to the nearest container.
    # It is more resilient than reaching into a brittle hard-coded selector.
    container = heading.locator("xpath=ancestor::*[self::section or self::div or self::article][1]").first
    if container.count() == 0:
        return []

    links = container.locator("a[data-hovercard-type='repository']")
    repositories: List[Dict[str, Any]] = []

    for index in range(links.count()):
        link = links.nth(index)
        repo_name = _safe_text(link)
        href = _safe_attribute(link, "href")
        if not repo_name:
            continue

        repo_url = f"https://github.com{href}" if href and not href.startswith("http") else href
        card = link.locator("xpath=ancestor::*[self::article or self::div][1]").first
        repositories.append(
            {
                "name": repo_name,
                "url": repo_url,
                "description": _safe_text(card.locator("p")),
                "language": _safe_text(card.locator("span[itemprop='programmingLanguage']")),
                "stars": _safe_text(card.locator("a[href*='stargazers']")),
                "forks": _safe_text(card.locator("a[href*='network/members']")),
            }
        )

    return repositories


def _write_reports(username: str, data: Dict[str, Any], screenshot_path: Path) -> None:
    """Save JSON and HTML reports for the investigation output."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / f"{username}.json"
    html_path = reports_dir / f"{username}.html"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>GitHub Recon for {username}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #111827; }}
    h1 {{ margin-bottom: 0.25rem; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }}
    th, td {{ border: 1px solid #d1d5db; padding: 0.5rem; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .status {{ font-weight: bold; }}
  </style>
</head>
<body>
  <h1>GitHub Recon for {username}</h1>
  <p><strong>Status:</strong> <span class=\"status\">{data.get('profile_exists', False) and 'Found' or 'Not Found'}</span></p>
  <h2>Profile</h2>
  <table>
    <tr><th>Field</th><th>Value</th></tr>
    <tr><td>Username</td><td>{data.get('username', '')}</td></tr>
    <tr><td>Display name</td><td>{data.get('display_name', '')}</td></tr>
    <tr><td>Bio</td><td>{data.get('bio', '')}</td></tr>
    <tr><td>Company</td><td>{data.get('company', '')}</td></tr>
    <tr><td>Location</td><td>{data.get('location', '')}</td></tr>
    <tr><td>Join date</td><td>{data.get('join_date', '')}</td></tr>
    <tr><td>Followers</td><td>{data.get('followers', '')}</td></tr>
    <tr><td>Following</td><td>{data.get('following', '')}</td></tr>
    <tr><td>Repositories</td><td>{data.get('repositories', '')}</td></tr>
    <tr><td>Avatar URL</td><td>{data.get('avatar_url', '')}</td></tr>
    <tr><td>Profile URL</td><td>{data.get('profile_url', '')}</td></tr>
    <tr><td>Screenshot</td><td>{screenshot_path}</td></tr>
  </table>
</body>
</html>
"""
    html_path.write_text(html_content, encoding="utf-8")


def _render_terminal_output(username: str, github_data: Dict[str, Any]) -> None:
    """Render the investigation results in a structured Rich terminal UI."""
    console = Console()
    status_text = Text("✓ Found", style="green") if github_data.get("profile_exists") else Text("✗ Not Found", style="red")
    console.print(Panel.fit(f"[bold cyan]GitHub Recon[/bold cyan]\n[bold]{username}[/bold]", border_style="cyan"))

    if github_data.get("profile_exists"):
        console.print(Panel.fit(f"Target profile: {status_text}", border_style="green"))
    else:
        console.print(Panel.fit(f"Target profile: {status_text}", border_style="red"))

    profile_table = Table(title="Profile Details", box=box.SIMPLE_HEAVY, show_header=True)
    profile_table.add_column("Field", style="bold")
    profile_table.add_column("Value")
    profile_table.add_row("Username", github_data.get("username") or "—")
    profile_table.add_row("Display name", github_data.get("display_name") or "—")
    profile_table.add_row("Bio", github_data.get("bio") or "—")
    profile_table.add_row("Company", github_data.get("company") or "—")
    profile_table.add_row("Location", github_data.get("location") or "—")
    profile_table.add_row("Join date", github_data.get("join_date") or "—")
    profile_table.add_row("Followers", str(github_data.get("followers") or "—"))
    profile_table.add_row("Following", str(github_data.get("following") or "—"))
    profile_table.add_row("Repositories", str(github_data.get("repositories") or "—"))
    profile_table.add_row("Avatar URL", github_data.get("avatar_url") or "—")
    profile_table.add_row("Profile URL", github_data.get("profile_url") or "—")
    console.print(profile_table)

    if github_data.get("organizations"):
        org_table = Table(title="Organizations", box=box.SIMPLE_HEAVY)
        org_table.add_column("Name")
        for organization in github_data.get("organizations", []):
            org_table.add_row(organization)
        console.print(org_table)

    if github_data.get("external_links"):
        links_table = Table(title="External Links", box=box.SIMPLE_HEAVY)
        links_table.add_column("Link")
        for link in github_data.get("external_links", []):
            links_table.add_row(link)
        console.print(links_table)

    repos = github_data.get("repositories_list", [])
    if repos:
        repo_table = Table(title="Repositories", box=box.SIMPLE_HEAVY)
        repo_table.add_column("Name")
        repo_table.add_column("Language")
        repo_table.add_column("Stars")
        repo_table.add_column("Forks")
        repo_table.add_column("URL")
        for repo in repos:
            repo_table.add_row(
                repo.get("name") or "—",
                repo.get("language") or "—",
                repo.get("stars") or "—",
                repo.get("forks") or "—",
                repo.get("url") or "—",
            )
        console.print(repo_table)

    summary = Table(title="Summary", box=box.SIMPLE_HEAVY)
    summary.add_column("Metric", style="bold")
    summary.add_column("Value")
    summary.add_row("Repositories", str(len(repos)))
    summary.add_row("Organizations", str(len(github_data.get("organizations", []))))
    summary.add_row("External links", str(len(github_data.get("external_links", []))))
    summary.add_row("Screenshot saved", "✓" if github_data.get("screenshot_saved") else "✗")
    summary.add_row("Reports saved", "✓" if github_data.get("reports_saved") else "✗")
    console.print(summary)


def check_github(username: str) -> Dict[str, Any]:
    """Collect GitHub profile intelligence and render a professional OSINT report."""
    username = (username or "").strip()
    github_data: Dict[str, Any] = {
        "profile_exists": False,
        "username": username,
        "display_name": None,
        "bio": None,
        "company": None,
        "location": None,
        "join_date": None,
        "followers": None,
        "following": None,
        "repositories": None,
        "avatar_url": None,
        "profile_url": None,
        "external_links": [],
        "organizations": [],
        "repositories_list": [],
        "screenshot_saved": False,
        "reports_saved": False,
    }

    url = f"https://github.com/{username}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(60000)

        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
        except Exception:
            page.goto(url, wait_until="commit")

        page_title = page.title().lower()
        not_found = "page not found" in page_title or "not found" in page_title

        if not_found:
            github_data["profile_exists"] = False
        else:
            github_data["profile_exists"] = True
            github_data["display_name"] = _safe_text(page.locator("h1.vcard-names span.p-name").first) or _safe_text(page.locator("h1 span.p-name").first)
            github_data["bio"] = _safe_text(page.locator(".p-note"))
            github_data["company"] = _safe_text(page.locator(".p-org"))
            github_data["location"] = _safe_text(page.locator(".p-label"))

            join_date = None
            detail_items = page.locator("ul.vcard-details li")
            for index in range(detail_items.count()):
                detail_text = _safe_text(detail_items.nth(index))
                if detail_text and "joined" in detail_text.lower():
                    join_date = detail_text
                    break
            github_data["join_date"] = join_date
            github_data["followers"] = _safe_text(page.locator("a[href$='?tab=followers'] span").first)
            github_data["following"] = _safe_text(page.locator("a[href$='?tab=following'] span").first)
            github_data["repositories"] = _safe_text(page.locator("a[href$='?tab=repositories'] span").first)
            github_data["avatar_url"] = _safe_attribute(page.locator("img.avatar-user"), "src")
            github_data["profile_url"] = url

            external_links: List[str] = []
            for index in range(page.locator("a[href]").count()):
                link = page.locator("a[href]").nth(index)
                value = _safe_attribute(link, "href")
                if not value:
                    continue
                if value.startswith("http") and "github.com" not in value and "mailto:" not in value:
                    external_links.append(value)
            github_data["external_links"] = list(dict.fromkeys(external_links))

            organizations = []
            for index in range(page.locator("a[href*='/orgs/']").count()):
                org_name = _safe_text(page.locator("a[href*='/orgs/']").nth(index))
                if org_name:
                    organizations.append(org_name)
            github_data["organizations"] = organizations

            pinned_repositories = _extract_repository_section(page, "Pinned")
            popular_repositories = _extract_repository_section(page, "Popular repositories") if not pinned_repositories else []
            github_data["repositories_list"] = pinned_repositories or popular_repositories

            screenshot_path = Path("screenshots") / f"{username}.png"
            screenshot_path.parent.mkdir(exist_ok=True)
            page.screenshot(path=str(screenshot_path), full_page=True)
            github_data["screenshot_saved"] = screenshot_path.exists()

        browser.close()

    _write_reports(username, github_data, Path("screenshots") / f"{username}.png")
    github_data["reports_saved"] = (Path("reports") / f"{username}.json").exists() and (Path("reports") / f"{username}.html").exists()
    _render_terminal_output(username, github_data)
    return github_data
