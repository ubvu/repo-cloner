"""
This script is made to be able to mirror all repositories
from a primary host to a secondary one. It has been
written to mirror all repos in a GitHub group to a clone
in a private Gitlab environment. It should work for an
individual account and other host with little to no work.
"""

import os
import random
import time

import pandas as pd
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

# **** EDIT HERE ****
# Change this to match the variable names in your .env file
GITHUB_TOKEN = os.getenv("GITHUB-TOKEN")
GITHUB_OWNER = os.getenv("GITHUB-USER")
GITHUB_API_URL = os.getenv("GITHUB-API-URL")
GITHUB_GROUP_NAME = os.getenv("GITHUB-GROUP")
GITLAB_TOKEN = os.getenv("GITLAB-TOKEN")
GITLAB_OWNER = os.getenv("GITLAB-USER")
GITLAB_API_URL = os.getenv("GITLAB-API-URL")
GITLAB_GROUP_NAME = os.getenv("GITLAB-GROUP")
GITLAB_GROUP_ID = "GITLAB_GROUP_ID"

# **** DO NOT EDIT HERE ****

# Headers for API requests
headers_gh = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}
headers_gl = {
    "PRIVATE-TOKEN": f"{GITLAB_TOKEN}",
    "Content-Type": "application/json",
}


# Get list of repositories in original group
def get_github_repos(org, headers):
    page = 1
    repos = []
    while True:
        url = f"{GITHUB_API_URL}/orgs/{org}/repos?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            repos += data
            if (
                "link" in response.headers
                and "next" in response.headers["link"]
            ):
                page += 1
                time.sleep(
                    6 / random.randint(2, 6)
                )  # Delay to avoid hitting rate limits
            else:
                break
        else:
            print(f"Failed to get GitHub repos: {response.status_code}")
            break
    return repos


# Get repository details from original host
def get_github_repo_details(repo_name, headers):
    url = f"{GITHUB_API_URL}/repos/{GITHUB_OWNER}/{repo_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get details for {repo_name}: {response.status_code}")
        return None


def get_gitlab_group_id(group_name, headers):
    page = 1
    while True:
        url = f"{GITLAB_API_URL}/api/v4/groups?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            groups = response.json()
            # print(groups)
            for group in groups:
                if group["name"] == group_name:
                    set_key(".env", group["id"], os.environ["GITLAB-GROUP-ID"])
                    return group["id"]
            if (
                "link" in response.headers
                and "next" in response.headers["link"]
            ):
                page += 1
                time.sleep(
                    6 / random.randint(2, 6)
                )  # Delay to avoid hitting rate limits
            else:
                break
        else:
            print(f"Failed to get GitLab groups: {response.status_code}")
            return None
    print(f"Group {group_name} not found in GitLab")
    return None


# Mirror each original repo to its new home
def mirror_to_gitlab(github_repos, headers):
    for repo in github_repos:
        repo_name = repo["name"]
        repo_url = repo["html_url"]
        repo_description = repo["description"] if repo["description"] else ""
        repo_visibility = repo["private"]  # True for private, False for public

        # Create a new project in the GitLab environment
        gitlab_project_url = f"{GITLAB_API_URL}/api/v4/projects"
        gitlab_project_data = {
            "name": repo_name,
            "description": repo_description,
            "visibility_level": "private" if repo_visibility else "public",
            "namespace_id": get_gitlab_group_id(GITLAB_GROUP_NAME, headers),
            "mirror": True,
            "import_url": repo_url + ".git",
        }

        response = requests.post(
            gitlab_project_url, headers=headers, json=gitlab_project_data
        )
        if response.status_code == 201:
            print(f"Successfully mirrored {repo_name} to GitLab")
        else:
            print(f"Failed to mirror {repo_name}: {response.status_code}")
            print(response)


if __name__ == "__main__":
    # Gather all the repo names from your github group/account
    github_repos = get_github_repos(GITHUB_OWNER, headers_gh)
    github_repos = pd.DataFrame.from_records(github_repos)
    print(len(github_repos))
    # These are compared to the previous scrape to avoid copies
    try:
        existing_gitlab_repos = pd.read_csv("existing_repos.csv")
    except (pd.errors.EmptyDataError, FileNotFoundError):
        existing_gitlab_repos = pd.DataFrame(
            columns=list(github_repos.columns)
        )
    new_repos = github_repos[
        ~github_repos["id"].isin(existing_gitlab_repos["id"])
    ]
    # print(new_repos)
    if len(new_repos) > 0:
        # Cut out private repos and test on limited group
        new_repos = new_repos[
            (new_repos["private"]) & (new_repos["name"] == "private_test")
        ]
        for _index, repo in new_repos.iterrows():
            # repo_details = get_github_repo_details(repo["name"])
            # print("*" * 30, repo)
            mirror_to_gitlab([repo], headers_gl)
            # TODO: Test that upload works, create dummy private proj
        # Add new repos to existing repos file
        existing_gitlab_repos = pd.concat([new_repos, existing_gitlab_repos])
        existing_gitlab_repos.to_csv("existing_repos.csv")
    else:
        print("No repositories found in GitHub group")
