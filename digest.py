import requests
import datetime

# List of repositories to track
repos = [
    "cardano-foundation/cf-lob-platform",
    "cardano-foundation/cardano-ibc-incubator",
    "cardano-foundation/cardano-rosetta-java",
    "cardano-foundation/cardano-devkit",
    "cardano-foundation/cf-cardano-ballot",
    "cardano-foundation/cip113-programmable-tokens",
    "cardano-foundation/cardano-mobile-connect-demo"
    "cardano-foundation/cip30-data-signature-parser",
    "cardano-foundation/cardano-connect-with-wallet",
    "cardano-foundation/cf-adahandle-resolver",
    "cardano-foundation/cf-java-rewards-calculation",
    "bloxbean/cardano-client-lib",
    "bloxbean/yaci-devkit",
    "bloxbean/yaci",
    "bloxbean/yaci-store"
]

# GitHub API base URL
github_api_base = "https://api.github.com/repos/"

# Calculate the start and end dates for the previous calendar month
now = datetime.datetime.now(datetime.timezone.utc)
first_day_current_month = datetime.datetime(now.year, now.month, 1)
end_date = first_day_current_month - datetime.timedelta(days=1)
start_date = datetime.datetime(end_date.year, end_date.month, 1)

# GitHub API headers
headers = {
    "Accept": "application/vnd.github.v3+json"
}

# Function to fetch GitHub activity within the previous calendar month
def fetch_github_activity(repo):
    activity = {"issues_opened": [], "issues_closed": [], "pr_merged": []}

    # Fetch PRs and include only those that are merged within the period
    prs_url = f"{github_api_base}{repo}/pulls?state=all&per_page=100"
    response = requests.get(prs_url, headers=headers)
    if response.status_code == 200:
        prs = response.json()
        for pr in prs:
            merged_at = pr.get("merged_at")
            if merged_at:
                merged_date = datetime.datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")
                if start_date <= merged_date <= end_date:
                    pr_link = pr["html_url"]
                    pr_number = pr["number"]
                    pr_title = pr["title"]
                    activity["pr_merged"].append(f"- [#{pr_number} - {pr_title}]({pr_link})")

    # Fetch issues (excluding PRs)
    issues_url = f"{github_api_base}{repo}/issues?state=all&per_page=100"
    response = requests.get(issues_url, headers=headers)
    if response.status_code == 200:
        issues = response.json()
        for issue in issues:
            # Skip items that are actually PRs
            if "pull_request" in issue:
                continue

            created_at = datetime.datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            closed_at = issue.get("closed_at")
            issue_link = issue["html_url"]
            issue_number = issue["number"]
            issue_title = issue["title"]

            if start_date <= created_at <= end_date:
                activity["issues_opened"].append(f"- [#{issue_number} - {issue_title}]({issue_link})")

            if closed_at:
                closed_date = datetime.datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")
                if start_date <= closed_date <= end_date:
                    activity["issues_closed"].append(f"- [#{issue_number} - {issue_title}]({issue_link})")

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
