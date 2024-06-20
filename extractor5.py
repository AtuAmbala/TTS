import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import concurrent.futures
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
GITHUB_API_URL = "https://api.github.com"
REPO = "freeCodeCamp/freeCodeCamp"
#TOKEN = os.getenv("GITHUB_TOKEN")  # Use environment variable
TOKEN = "GITHUB_TOKEN"

if not TOKEN:
    raise ValueError("GitHub token not found. Set the GITHUB_TOKEN environment variable.")

# Headers for authentication
headers = {
    "Authorization": f"token {TOKEN}"
}

def check_rate_limit(headers):
    url = f"{GITHUB_API_URL}/rate_limit"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    remaining = data['rate']['remaining']
    reset = data['rate']['reset']
    return remaining, reset

def wait_for_rate_limit_reset(headers):
    remaining, reset = check_rate_limit(headers)
    if remaining == 0:
        reset_time = datetime.fromtimestamp(reset)
        sleep_time = (reset_time - datetime.now()).total_seconds() + 10  # Adding a buffer
        logging.warning(f"Rate limit reached. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)

def get_pull_requests(repo, headers, max_requests=20000):
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls"
    params = {
        "state": "closed",
        "per_page": 100,
        "sort": "updated",
        "direction": "desc"
    }
    prs = []
    while len(prs) < max_requests:
        wait_for_rate_limit_reset(headers)
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        prs.extend(batch)
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break
    return [pr for pr in prs if pr['merged_at']][:max_requests]

def get_pull_request_details(repo, pr_number, headers):
    wait_for_rate_limit_reset(headers)
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_issue_comments(repo, pr_number, headers):
    wait_for_rate_limit_reset(headers)
    url = f"{GITHUB_API_URL}/repos/{repo}/issues/{pr_number}/comments"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_review_comments(repo, pr_number, headers):
    wait_for_rate_limit_reset(headers)
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/comments"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_reviews(repo, pr_number, headers):
    wait_for_rate_limit_reset(headers)
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/reviews"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_ci_cd_status(repo, commit_sha, headers):
    wait_for_rate_limit_reset(headers)
    url = f"{GITHUB_API_URL}/repos/{repo}/commits/{commit_sha}/check-runs"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {'check_runs': []}

def extract_metrics(pr, repo, headers):
    pr_number = pr['number']
    pr_details = get_pull_request_details(repo, pr_number, headers)
    issue_comments = get_issue_comments(repo, pr_number, headers) or []
    review_comments = get_review_comments(repo, pr_number, headers) or []
    reviews = get_reviews(repo, pr_number, headers) or []
    
    if 'merge_commit_sha' in pr_details:
        ci_cd_status = get_ci_cd_status(repo, pr_details['merge_commit_sha'], headers)
    else:
        ci_cd_status = {'check_runs': []}

    build_statuses = [run['conclusion'] for run in ci_cd_status.get('check_runs', [])]
    num_build_runs = len(build_statuses)
    num_build_failures = build_statuses.count('failure')

    comment_authors = list(set([comment["user"]["login"] for comment in issue_comments + review_comments if comment["user"]]))

    metrics = {
        "pr_number": pr_number,
        "created_at": pr_details["created_at"],
        "merged_at": pr_details["merged_at"],
        "author": pr_details["user"]["login"],
        "number_of_comments": len(issue_comments),
        "number_of_review_comments": len(review_comments),
        "number_of_commits": pr_details["commits"],
        "lines_of_code_changed": pr_details["additions"] + pr_details["deletions"],
        "number_of_files_changed": pr_details["changed_files"],
        "number_of_reviewers": len(set([review["user"]["login"] for review in reviews if review["user"]])),
        "number_of_approvals": len([review for review in reviews if review["state"] == "APPROVED"]),
        "labels": [label["name"] for label in pr_details["labels"]],
        "time_to_first_response": (datetime.strptime(issue_comments[0]["created_at"], "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(pr_details["created_at"], "%Y-%m-%dT%H:%M:%SZ")).total_seconds() if issue_comments else None,
        "number_of_assignees": len(pr_details["assignees"]),
        "review_duration": (datetime.strptime(pr_details["updated_at"], "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(pr_details["created_at"], "%Y-%m-%dT%H:%M:%SZ")).total_seconds(),
        "number_of_changes_requested": len([review for review in reviews if review["state"] == "CHANGES_REQUESTED"]),
        "number_of_build_runs": num_build_runs,
        "number_of_build_failures": num_build_failures,
        "number_of_linked_issues": len(pr_details.get("linked_issues", [])),
        "time_since_last_commit": (datetime.now() - datetime.strptime(pr_details["updated_at"], "%Y-%m-%dT%H:%M:%SZ")).total_seconds(),
        "test_coverage": pr_details.get("test_coverage"),  # Assuming test coverage is included in PR details
        "number_of_reviews_requested": len(pr_details["requested_reviewers"]),
        "number_of_revisions": pr_details["commits"],
        "number_of_milestones": 1 if pr_details["milestone"] else 0,
        "dependency_changes": any('dependency' in label["name"].lower() for label in pr_details["labels"]),
        "comment_authors": comment_authors
    }

    return metrics

def main():
    prs = get_pull_requests(REPO, headers, max_requests=20000)
    if not prs:
        print("No pull requests found.")
        return

    logging.info(f"Fetched {len(prs)} pull requests.")

    metrics_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_pr = {executor.submit(extract_metrics, pr, REPO, headers): pr for pr in prs}
        for future in concurrent.futures.as_completed(future_to_pr):
            pr = future_to_pr[future]
            try:
                metrics = future.result()
                metrics_list.append(metrics)
            except Exception as exc:
                logging.error(f'PR {pr["number"]} generated an exception: {exc}')

    df = pd.DataFrame(metrics_list)
    print(df.head())  # Print the DataFrame to ensure data is correctly captured
    df.to_csv("pull_request_metrics.csv", index=False)
    print("Data has been saved to pull_request_metrics.csv")

if __name__ == "__main__":
    main()
