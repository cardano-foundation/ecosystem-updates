import os
import requests
import datetime

# List of repositories to track
repos = [
    # cardano-foundation
    "cardano-foundation/cf-lob-platform",
    "cardano-foundation/cardano-ibc-incubator",
    "cardano-foundation/cardano-rosetta-java",
    "cardano-foundation/cardano-graphql",
    "cardano-foundation/cardano-devkit",
    "cardano-foundation/cf-cardano-ballot",
    "cardano-foundation/cip113-programmable-tokens",
    "cardano-foundation/cardano-mobile-connect-demo",
    "cardano-foundation/cip30-data-signature-parser",
    "cardano-foundation/cardano-connect-with-wallet",
    "cardano-foundation/cf-adahandle-resolver",
    "cardano-foundation/cf-java-rewards-calculation",
    "cardano-foundation/x402",
    "cardano-foundation/cardano-templates",
    "cardano-foundation/cf-reeve-application",
    "cardano-foundation/cf-reeve-platform",
    "cardano-foundation/cf-reeve-frontend",
    "cardano-foundation/cf-reeve-indexer",
    "cardano-foundation/cf-reeve-docs",
    "cardano-foundation/hermes-relayer",
    "cardano-foundation/cf-summit-evoting",
    "cardano-foundation/cf-summit-evoting-status",
    "cardano-foundation/cf-cip1694-ballot-status",
    "cardano-foundation/cf-cardano-ballot-ui",
    "cardano-foundation/ecosystem-updates",
    "cardano-foundation/cardano-dev-skills",
    "cardano-foundation/cardano-token-registry",
    "cardano-foundation/cardano-x402-facilitator",
    "cardano-foundation/cf-explorer-status",
    "cardano-foundation/cf-token-metadata-registry",
    "cardano-foundation/cf-token-metadata-registry-status",
    "cardano-foundation/fn-bafin-cardano-sc",
    "cardano-foundation/cip113-programmable-tokens-platform",
    "cardano-foundation/cardano-dune-analytics",
    "cardano-foundation/originatenavio",
    "cardano-foundation/cardano-dpp-standards",
    "cardano-foundation/cardano-tool-compass",
    "cardano-foundation/cardano-learn-and-hack",
    "cardano-foundation/uverify-backend",
    "cardano-foundation/cf-ledger-sync",
    "cardano-foundation/cf-ledger-consumer",
    "cardano-foundation/cf-ledger-crawler",
    "cardano-foundation/cf-ls-sync-data-verification",
    "cardano-foundation/yaci-address-balance-monitor",
    "cardano-foundation/cf-bolnisi-prototype",
    "cardano-foundation/cf-georgian-wine-resolver",
    "cardano-foundation/cardano-economic-parameter-insights",
    "cardano-foundation/cardano-ibc-summit-demo",
    "cardano-foundation/cf-gsoc-ideas-page-2025",
    "cardano-foundation/merkle-tree-java",
    "cardano-foundation/cardano-news-api",
    "cardano-foundation/cardano-store-poc-hoodies",
    "cardano-foundation/cardano-explorer-app",
    "cardano-foundation/hydra-java",
    "cardano-foundation/hydra-voting-poc",
    "cardano-foundation/aiken-lucid-yaci-dev-kit-starter-kit",
    "cardano-foundation/cardano-verify-datasignature",
    "cardano-foundation/cf-cddl-parser",
    "cardano-foundation/cardano-graphql-yaci",
    

    # bloxbean
    "bloxbean/cardano-client-lib",
    "bloxbean/cardano-client-bindings",
    "bloxbean/cardano-client-examples",
    "bloxbean/cardano-client-lib-docs",
    "bloxbean/yaci",
    "bloxbean/yaci-devkit",
    "bloxbean/yaci-store",
    "bloxbean/yaci-store-plugins",
    "bloxbean/yaci-cardano-test-sample",
    "bloxbean/yano",
    "bloxbean/julc",
    "bloxbean/julc-examples",
    "bloxbean/julc-helloworld",
    "bloxbean/zeroj",
    "bloxbean/zeroj-usecases",
    "bloxbean/devkit-hackathon-demo",
]

# GitHub API base URL
github_api_base = "https://api.github.com/repos/"

# Calculate the start and end dates for the previous calendar month
now = datetime.datetime.now(datetime.timezone.utc)
first_day_current_month = datetime.datetime(now.year, now.month, 1)
end_date = first_day_current_month - datetime.timedelta(days=1)
start_date = datetime.datetime(end_date.year, end_date.month, 1)

# The period covers everything up to (but not including) the first day of the current month,
# so activity during the whole last day of the previous month is included
def in_period(date):
    return start_date <= date < first_day_current_month

def parse_date(value):
    return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")

# GitHub API headers
headers = {
    "Accept": "application/vnd.github.v3+json"
}

# Authenticate to avoid the 60 requests/hour limit for anonymous requests
github_token = os.environ.get("GITHUB_TOKEN")
if github_token:
    headers["Authorization"] = f"Bearer {github_token}"
else:
    print("Warning: GITHUB_TOKEN is not set, requests are limited to 60 per hour and the digest may be incomplete")

# Fetch a page of results; returns None if the repository does not exist
def fetch_page(url, params=None):
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 404:
        return None
    # Fail loudly on rate limits and other errors instead of silently producing an incomplete digest
    response.raise_for_status()
    return response

# Function to fetch GitHub activity within the previous calendar month
def fetch_github_activity(repo):
    activity = {"issues_opened": [], "issues_closed": [], "pr_merged": []}

    # Fetch PRs, most recently updated first, and include only those that are merged within the period.
    # A PR merged within the period was updated at or after the start date, so stop once older ones are reached.
    url = f"{github_api_base}{repo}/pulls"
    params = {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100}
    while url:
        response = fetch_page(url, params)
        if response is None:
            print(f"Warning: repository {repo} not found, skipping")
            return activity
        prs = response.json()
        for pr in prs:
            merged_at = pr.get("merged_at")
            if merged_at and in_period(parse_date(merged_at)):
                pr_link = pr["html_url"]
                pr_number = pr["number"]
                pr_title = pr["title"]
                activity["pr_merged"].append(f"- [#{pr_number} - {pr_title}]({pr_link})")
        if not prs or parse_date(prs[-1]["updated_at"]) < start_date:
            break
        # The "next" link already contains the query parameters
        url = response.links.get("next", {}).get("url")
        params = None

    # Fetch issues (excluding PRs) updated since the start of the period
    url = f"{github_api_base}{repo}/issues"
    params = {"state": "all", "since": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "per_page": 100}
    while url:
        response = fetch_page(url, params)
        if response is None:
            break
        for issue in response.json():
            # Skip items that are actually PRs
            if "pull_request" in issue:
                continue

            created_at = parse_date(issue["created_at"])
            closed_at = issue.get("closed_at")
            issue_link = issue["html_url"]
            issue_number = issue["number"]
            issue_title = issue["title"]

            if in_period(created_at):
                activity["issues_opened"].append(f"- [#{issue_number} - {issue_title}]({issue_link})")

            if closed_at and in_period(parse_date(closed_at)):
                activity["issues_closed"].append(f"- [#{issue_number} - {issue_title}]({issue_link})")
        url = response.links.get("next", {}).get("url")
        params = None

    return activity

# Fetch activity for each repository
repo_activities = {repo: fetch_github_activity(repo) for repo in repos}

# Create digest text
digest_content = "# Monthly Digest: Ecosystem Tooling - GitHub Activities\n\n"
digest_content += f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n\n"

# Only include repositories with activity in the digest
repos_found = False
for repo, activity in repo_activities.items():
    if not (activity["issues_opened"] or activity["pr_merged"] or activity["issues_closed"]):
        continue  # Skip repositories with no updates

    repos_found = True
    repo_link = f"https://github.com/{repo}"
    # Add a bullet icon before each repository
    digest_content += f"## 🔹 [{repo}]({repo_link})\n\n"

    if activity["issues_opened"]:
        digest_content += "**Issues opened:**\n" + "\n".join(activity["issues_opened"]) + "\n\n"
    if activity["pr_merged"]:
        digest_content += "**PRs merged & closed:**\n" + "\n".join(activity["pr_merged"]) + "\n\n"
    if activity["issues_closed"]:
        digest_content += "**Issues closed:**\n" + "\n".join(activity["issues_closed"]) + "\n\n"

if not repos_found:
    digest_content += "No significant activity in this period.\n"

# Add a closing phrase with a nice message and an emoji
digest_content += "\n---\n\nLet's keep building! 🚀\n"

# Generate file name with month and year (e.g., github_digest_February_2025.md)
filename = f"github_digest_{end_date.strftime('%B_%Y')}.md"
with open(filename, "w") as file:
    file.write(digest_content)

print(f"Monthly digest saved to {filename}")
