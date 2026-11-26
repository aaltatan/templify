# Installation

templify needs **Python 3.12 or newer**. Install it as a tool, so the `templify` command
is available everywhere without touching your other Python projects:

=== "uv"

    ```text
    uv tool install templify-cli
    ```

=== "pipx"

    ```text
    pipx install templify-cli
    ```

=== "pip"

    ```text
    pip install templify-cli
    ```

The package is called `templify-cli`, and the command it installs is `templify`.
Everything installs as prebuilt wheels. Word templates are filled directly, so you do
**not** need Microsoft Word or LibreOffice installed.

Check that it works:

```text
templify --help
```

## Shell completion

Tab completion for commands, options and `types --namespace`:

```text
templify --install-completion
```

Restart the shell after installing it.

## Upgrade and uninstall

=== "uv"

    ```text
    uv tool upgrade templify-cli
    uv tool uninstall templify-cli
    ```

=== "pipx"

    ```text
    pipx upgrade templify-cli
    pipx uninstall templify-cli
    ```

Upgrading from an older version? See [Upgrading](reference/upgrading.md) for the
renamed commands and options.

## Run from a clone

```text
git clone https://github.com/aaltatan/templify
cd templify
uv sync
uv run templify --help
```

## The example files

Every `templify` command in this documentation runs against the files in the
[`examples/`](https://github.com/aaltatan/templify/tree/main/examples) folder of the
repository. Clone the repository (or download the folder) and run the commands from
inside it:

```text
cd templify/examples
```
