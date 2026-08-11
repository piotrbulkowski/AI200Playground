# CLAUDE.md

Guidance for Claude Code when working in this repo. See `specs/` for the actual project design —
this file is only for things that aren't obvious from the specs or the code itself.

## Git

**The user commits manually.** Never run `git add` / `git commit` / `git push` in this repo
unless explicitly asked in that specific turn.

## Environment gotchas (Windows / PowerShell)

* **uv, terraform** are not preinstalled — installed this session via the official `irm
  https://astral.sh/uv/install.ps1 | iex` script and `winget install Hashicorp.Terraform`.
* **PATH refresh**: newly-installed CLI tools (uv, terraform) update the registry PATH but the
  current PowerShell tool session won't see it until you rebuild `$env:Path` from the registry:
  `$m = [System.Environment]::GetEnvironmentVariable("Path","Machine"); $u =
  [System.Environment]::GetEnvironmentVariable("Path","User"); $env:Path = "$m;$u"`. Do this at
  the start of any PowerShell call that invokes a tool installed earlier in the same session.
* **Docker Desktop** is not always running. `docker compose up` fails with a pipe-not-found error
  if the engine isn't up; start it with `Start-Process "C:\Program Files\Docker\Docker\Docker
  Desktop.exe"` and poll `docker info` until it succeeds before using `docker`/`docker compose`.
* **curl + git-bash + Windows paths**: `curl -F "file=@/c/Repos/...` (MSYS-style path) fails with
  `curl: (26) Failed to open/read local data` because curl.exe doesn't get MSYS's automatic path
  translation for paths embedded inside a compound `-F` argument. Use a Windows-style path instead:
  `-F "file=@C:/Repos/AI200Playground/..."`.
* **`az login`**: never run this yourself — it's an interactive auth step tied to the user's
  identity. If `az account show`/`az account list` shows only a tenant-level account with no
  subscription, that's a sign the user needs to re-authenticate; ask them, don't run it for them.

## Azure SDK gotchas

* **`azure-identity`'s async `DefaultAzureCredential`** requires `aiohttp` as an explicit
  dependency — without it, the first token request fails with `ImportError: aiohttp package is
  not installed` deep inside `azure.core.pipeline.transport`. It's in `pyproject.toml` now; if a
  similar async Azure SDK client gets added later (Cosmos, Service Bus, etc.), check whether it
  needs the same thing.
* **`DefaultAzureCredential`'s credential chain can be very slow** (minutes, not seconds) when
  probing against a storage account/resource that doesn't exist yet or when the managed-identity
  IMDS probe times out in a non-Azure environment. A hung request during local dev against
  not-yet-provisioned infra is very likely this, not a real bug — give it several minutes before
  assuming something is broken.

## Terraform gotchas

* Commit `infra/.terraform.lock.hcl` (reproducible provider versions) but not `infra/.terraform/`,
  `*.tfstate*`, or `terraform.tfvars` — already reflected in `.gitignore`.

## Python / pytest gotchas

* **`src` layout without an installed package** (`[tool.uv] package = false`): pytest can't
  import `src.*` unless `pythonpath = ["."]` is set under `[tool.pytest.ini_options]` in
  `pyproject.toml` — otherwise every test module import fails with `ModuleNotFoundError: No
  module named 'src'`.
* **pydantic-settings + `list[str]` fields from env vars**: by default pydantic-settings tries to
  `json.loads()` any "complex" field type read from an env var or `.env` file, so a plain
  comma-separated value (`ALLOWED_CONTENT_TYPES=a,b,c`) blows up with a `SettingsError` wrapping a
  `JSONDecodeError`. Fix: annotate the field `Annotated[list[str], NoDecode]` (from
  `pydantic_settings`) so the raw string reaches a `mode="before"` validator instead of pydantic's
  own JSON decoding — see `src/config.py`.
* **`addopts = "-m 'not integration'"` + command-line `-m integration` compose correctly** —
  pytest's `-m` is a normal (non-append) argparse option, so a value passed on the command line
  overrides the one baked into `addopts` rather than conflicting with it. This is how `uv run
  pytest` (fast tests only) and `uv run pytest -m integration` (real Azure/Postgres) both work
  from the same config.
* **Timestamp ties in tests**: two `Document.new()` calls in quick succession can get the exact
  same `datetime.now(UTC)` value depending on clock resolution, which silently breaks tests that
  assert on `ORDER BY created_at` behavior. Set `created_at` explicitly in such tests rather than
  relying on real-clock gaps between statements.
* **Ruff**: `B008` (flake8-bugbear) flags FastAPI's `Depends(...)` used as an argument default —
  that's the idiomatic FastAPI pattern, not a bug, so it's ignored project-wide in
  `[tool.ruff.lint]`. `UP042` prefers `enum.StrEnum` over `class X(str, Enum)` on Python 3.12+.

## Local dev environment state

* Local Postgres (Docker Compose) has both `ai200_dev` and `ai200_test` databases;
  `docker/postgres-init/001-create-test-db.sql` creates `ai200_test` automatically but only on a
  **fresh** `postgres-data` volume. If that volume predates the init script, create the database
  by hand once (see README).
* Real Azure resources exist: Storage Account `ai200playgrounddev` in `rg-ai200playground`
  (West Europe), containers `documents` and `documents-test`, RBAC role assignment already
  granted. Don't re-provision from scratch assuming nothing exists — check with `az` first.
