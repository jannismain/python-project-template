{{ includex('README.md', start_match='Prerequisites', end_match='<!-- usage-end -->')}}

??? note "Using [pipx]"

    ```{.sh .copy}
    pipx run init-python-project
    ```

[pipx]: https://pypa.github.io/pipx/

??? note "Using [copier]"

    The underlying template is built using [copier]. This means you can also use the copier template directly like this:

    ```{.sh .copy}
    copier copy --trust https://github.com/jannismain/python-project-template.git my_new_project
    ```

    *Note: `--trust` is required because the template uses [tasks] to setup your git repository for you.*

[tasks]: https://github.com/jannismain/python-project-template/blob/6ac1d970b001aac6b63277677baf3ec7c9622a7c/copier.yaml#L184
[copier]: https://github.com/copier-org/copier
