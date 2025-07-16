# Git Repo automatic mirror
This script is made to be able to mirror all repositories from a primary host to a secondary one. It has been written to mirror all repos in a GitHub group to a clone in a private Gitlab environment. It should work for an individual account and other host with little to no work.

In order to use this script you need to get an API token for both GitHub and GitLab: [github token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens), [gitlab token](https://docs.gitlab.com/user/profile/personal_access_tokens/).

Make sure to store these variables in a .env file. The gitignore in this project will not commit the .env, so if you keep it in your own instance you should avoid revealing your private token.
