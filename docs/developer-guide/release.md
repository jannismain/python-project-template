# Releasing a new version

As this repository is hosted on three different remotes to reach different target audiences ([GitHub](https://github.com/jannismain/python-project-template), [GitLab](https://gitlab.com/jannismain/python-project-template)), it is convenient to have their respective main branches all available under different names in your local repository:

```
git remote add origin git@github.com:jannismain/python-project-template.git
git checkout main
git remote add gitlab git@gitlab.com:jannismain/python-project-template.git
git branch --set-upstream-to=gitlab/main main-gitlab
```

Each of those remotes host a version of the project template with links updated to point to that remote. Therefore, updates cannot be simply pushed to those remotes but need to be merged into their main branches, so that the platform-specific changes remain intact.

With those preparations in place, a new release can be created like this:

1. Commit everything that should be part of the release to be `main` branch of the GitHub repository. That includes updating the CHANGELOG and bumping the version number.
2. Merge those changes into the `main` branches of the other remotes.

    ```
    git co main-gitlab
    git merge main --ff-only --ff
    ```

3. Trigger the release process on the public `main` branch

    ```
    make release
    ```
