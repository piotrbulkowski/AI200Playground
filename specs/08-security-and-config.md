# Phase 8 — Key Vault, Managed Identity, App Configuration

## Goal

Remove every secret from the codebase and repo, replace credentials with Managed Identity everywhere it's viable, and externalize non-secret configuration through App Configuration. This is the phase the exam tests most pedantically — the "which of these four almost-identical solutions is actually correct" question style shows up constantly here, so the callouts below lean on worked examples rather than abstract rules.

## AI-200 topics covered

Key Vault (RBAC, secret retrieval, rotation), Managed Identity, Azure App Configuration (including dynamic/labeled config and Key Vault references).

## What you'll build

* No connection strings, API keys, passwords, or tokens anywhere in the repo — ever, including in Dockerfiles or committed config.
* System-assigned Managed Identity on the API and worker, used for Key Vault, Blob Storage, ACR pulls (Phase 7), and Cosmos DB where the SDK supports identity-based auth.
* Secrets retrieved from Key Vault at runtime via SDK or via a `@Microsoft.KeyVault(...)` app-setting reference — not baked into an image or exported at deploy time.
* Non-secret runtime settings (default `VECTOR_STORE`, top-K, cache TTL, feature flags, chunk size, retry count) served from **Azure App Configuration**, with per-environment values via **labels**.
* A secret-rotation scenario: rotate a secret in Key Vault and confirm the running app picks up the new value without a redeploy.
* A config loader that works identically against the local dev environment and Azure without code changes (see exam callout on `DefaultAzureCredential`).

## Requirements

* Document, in `/docs/ai-200/key-vault.md`, the distinction between **application configuration** (non-secret, changeable, App Configuration's job), **secret** (Key Vault's job), and **managed identity** (the credential-free way something authenticates to fetch either). This distinction is asked about directly and confused constantly.
* Document required RBAC role assignments for every identity you create.

## What the exam actually asks

**Key Vault access sequencing** — the exam consistently wants this exact order, and gives partial-credit distractors for skipping or reordering a step:
1. Enable a **system-assigned managed identity** on the compute resource (Function App, Container App, etc.).
2. Grant that identity the **`Key Vault Secrets User`** RBAC role **at vault scope** — not `Key Vault Administrator` (too broad — that's for managing the vault itself, not reading secrets) and not scoped at the subscription level (too broad a blast radius for what's needed).
3. Reference or retrieve the secret — either an app setting using `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>/)`, or an SDK call at runtime.
Build this three-step sequence for real, then deliberately break each step once (wrong role, wrong scope, missing identity) and confirm you get the failure you'd expect — that's your Key Vault/Managed Identity troubleshooting exercise in Phase 10.

* **Prefer RBAC role assignment over the legacy Key Vault access policy model.** If a question offers both as options for a "secure and maintainable" solution, RBAC is the one that also plays well with retrieving the *latest* secret version at runtime without a redeploy — combine it with an SDK call at runtime (not exporting the secret's value at deploy time, which freezes a stale copy).

* **The "does this solution meet the goal" pattern shows up a lot — build the checklist, then test your own implementation against it:**
  * *Is the secret ever written into a file that gets committed to git* (a Dockerfile, a checked-in `.env`, a parameter file in source control)? If yes, it fails "kept outside git history" — regardless of how it's used at runtime. Hardcoding an API key as an `ENV` line in a Dockerfile fails for exactly this reason, even though the container *can* read it at runtime.
  * *Is the secret available to the running container/app without a manual step at deploy time?* A secret that only lives in a CI/CD platform's secret store (e.g. a GitHub Actions repository secret) doesn't automatically reach a running Azure resource unless something explicitly wires it through at deploy time — don't assume "it's a secret store somewhere" is sufficient by itself.
  * *Is it Key Vault + a reference (app setting or SDK call) + managed identity?* That combination is close to always the "Yes" answer in these scenarios.
  Run your own secret-handling code through this checklist before considering the phase done.

* **Function Key Vault reference syntax, exactly:** `@Microsoft.KeyVault(SecretUri=https://<vault-name>.vault.azure.net/secrets/<secret-name>/)` as the value of an app setting. Not a custom `KeyVault:vault;Secret:name` shorthand, not a connection-string-style `AZUREKVCONNSTR_` prefix — those aren't real. Set this up for at least one real secret used by the Function from Phase 4.

**App Configuration**

* **Per-environment values use Labels**, not resource tags, key prefixes, or content types. A single key (e.g. `ChunkSize`) can have a `development`-labeled value and a `production`-labeled value; your app selects by label at startup based on its current environment/profile (Phase "configuration profiles" in the overview).
* **Secure dynamic configuration = App Configuration + Key Vault references + managed identity for *both*, plus a refresh/polling interval** so config changes propagate without a redeploy. Don't use a service principal secret for this — that reintroduces the exact long-lived credential you're trying to eliminate.
* **`DefaultAzureCredential` is what makes the same code work locally and in Azure without changes**: locally it falls through to your `az login` session (or VS Code/environment credentials), in Azure it picks up the Managed Identity — same code path either way. Build your App Configuration client with `DefaultAzureCredential` from the start and prove it works both ways (run locally against a real App Configuration resource, then run the same image in a Container App).

## Exercises

* **Key Vault troubleshooting** (see [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md)): the app can't fetch a secret after deployment — diagnose whether it's the identity, the role, or the scope.
* Rotate a secret in Key Vault while the app is running and confirm the new value is picked up without redeploying.
* Run every item in the "does this meet the goal" checklist above against your own implementation and fix anything that fails.

## Definition of done

* Zero secrets in the repository, at any point in git history.
* Managed Identity is used for Key Vault, Blob Storage, ACR pulls, and Cosmos DB (where supported).
* A secret rotation is demonstrated without redeploying.
* App Configuration serves non-secret settings, with at least one value that differs by label across environments.
* `/docs/ai-200/key-vault.md` and an App Configuration doc are written per the template, ending with "AI-200 skills covered" lists.

Next: [09-observability.md](09-observability.md).
