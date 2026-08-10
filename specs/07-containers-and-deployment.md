# Phase 7 — Containerization & Deployment

## Goal

Get the API and worker running as containers, deployed to Azure Container Apps with real autoscaling, then add AKS as an optional second deployment target for the worker. This phase has the highest density of exam-tested minutiae in the whole project — the callouts below are worth building deliberately, not skimming.

## AI-200 topics covered

Docker, Azure Container Registry (incl. ACR Tasks), Azure Container Apps (ingress, revisions, custom domains, secrets, image pull auth), KEDA, AKS (manifests, troubleshooting).

## What you'll build

* Docker images for the API and the worker (at minimum).
* Images pushed to Azure Container Registry, versioned, with **ACR Tasks** automating rebuilds.
* API and worker deployed to **Azure Container Apps** with separate configs — the worker is not publicly reachable, the API is.
* **KEDA** scaling the worker on Service Bus queue depth, including true scale-to-zero when the queue is empty.
* An optional **AKS** deployment of the worker using plain Kubernetes manifests, once Container Apps works end-to-end.

## Requirements

* Configure environment variables, secrets, revisions, ingress, and scaling separately for API vs. worker.
* The worker's Container Apps ingress must be internal-only or disabled — it has no business being publicly reachable.
* ACR must authenticate to itself via Managed Identity, not stored admin credentials (see exam callout).
* Provide AKS manifests for deployment, service (if needed), config, and secrets/identity integration, plus a written diagnostic runbook (pod status, pod logs, events, connectivity).

## What the exam actually asks

**ACR Tasks**

* Automated rebuild triggers you should actually configure and test, one at a time: a **source-commit trigger** (rebuild on app code push), a **base-image-update trigger** (rebuild when the underlying OS/runtime image changes — this is the one people forget exists), and a **timer/schedule trigger** (periodic rebuilds). Building inside ACR itself (rather than a separate CI runner) is the point of ACR Tasks — it removes the dependency on external build infrastructure or a developer's machine.

**Container Apps**

* **Cost-minimizing autoscaling on an empty queue needs two settings together**, not one: (1) a scaling rule that actually monitors your Service Bus queue length (a KEDA `azure-servicebus` scale rule), and (2) allowing the replica count to go to **zero** when idle (`minReplicas: 0`) — a scaling rule alone doesn't save you money if the floor is still 1+ replicas. Configure both and prove it: drain the queue, watch replicas hit zero; add load, watch them scale up.
* **A stable test URL across revisions comes from a revision label, not the default revision URL.** Container Apps in multiple-revision mode lets you assign a label to a specific revision; the label gets its own stable URL you can keep handing to test users while you deploy new revisions underneath it. Build this: deploy revision 1, label it, deploy revision 2 without moving the label, confirm the label's URL still serves revision 1 until you explicitly repoint it.
* **Image pull auth without static credentials = Managed Identity + `AcrPull` role**, not the registry's admin username/password. Enable a system-assigned managed identity on the Container App, grant it the `AcrPull` role on the registry, and turn off admin credentials on the registry entirely to prove you don't need them.
* **Custom domain flow**: verify domain ownership (TXT record), point a CNAME/A record at the Container Apps environment, add the hostname to the app, then bind a certificate (managed certificate or your own upload) before HTTPS works. Do this as a real exercise if you have a domain available; otherwise write up the sequence and why each step has to precede the next.
* Real-time log streaming: `az containerapp logs show --follow` (the equivalent for App Service containers is `az webapp log tail` — know both command families exist, the exam has asked about each).

**KEDA**

* Configure a full `ScaledObject` for the worker, not just the trigger: trigger type (`azure-servicebus`), the queue name, a message-count threshold, `pollingInterval`, and `minReplicaCount`/`maxReplicaCount`. Document what each setting actually controls and what happens if you set `maxReplicaCount` too low relative to real traffic (queue backs up — this is one of the troubleshooting exercises in Phase 10).
* **`minReplicaCount: 0` is right for the batch worker, wrong for the customer-facing API.** Scale-to-zero saves cost but introduces cold-start latency on the next request — fine for an async worker nobody's waiting on, not fine for `/ask`. When a requirement pairs "minimize compute cost" with "maintain low-latency user experience even under bursty traffic," that's asking for two different scaling configs on two different components (worker: `minReplicaCount: 0`, scaled by queue length; API: `minReplicaCount: 1`+, scaled by HTTP concurrency) — not one setting applied everywhere. Configure both and note the tradeoff in your docs.

**AKS**

* Deploy the batch/worker workload using **declarative YAML manifests** applied via `kubectl apply -f`, not imperative `kubectl run`/`kubectl create` commands or `az aks` one-offs. The exam consistently prefers the GitOps-friendly declarative path.
* **Troubleshooting matrix — memorize the mapping, then verify it by breaking things for real:**
  | Symptom | First diagnostic step |
  |---|---|
  | A service can't reach another service | Inspect the Kubernetes **service endpoints** (confirms whether the target service has any healthy backing pods) |
  | A pod restarts repeatedly | Inspect the **container logs** |
  | Readiness probe failures | Inspect **Kubernetes events** |
  Reproduce each: point a service at the wrong selector (no endpoints), crash a container on startup (log the crash reason), misconfigure a readiness probe path (watch the event stream flag it).

**Azure Functions hosting (relevant here because it's a deployment/hosting-plan decision)**

* If a Function needs **event-driven scaling and custom Linux container images**, that requirement points at the **Premium (Elastic Premium)** plan, not Consumption — Consumption doesn't support custom containers the same way and caps execution duration much more tightly. Premium/Dedicated plans support long-running or effectively unbounded execution (configurable via `functionTimeout` in `host.json`), whereas Consumption defaults to a short timeout (minutes, not hours). If you build any Function beyond the simple event handler in Phase 4, note which plan it needs and why.

**App Service — a concept note, not a build target**

A meaningful chunk of exam questions describe App Service hosting a container instead of Container Apps. The concepts transfer directly, so even though this project deploys to Container Apps/AKS, spend one short session doing the App Service equivalents via CLI so you're not caught out by exam phrasing:
* Image pull auth via managed identity (same `AcrPull` pattern as Container Apps).
* Environment variables: non-sensitive values as plain App Settings, secrets as App Settings holding a `@Microsoft.KeyVault(SecretUri=...)` reference (identical syntax to Azure Functions — see [08-security-and-config.md](08-security-and-config.md)).
* `az webapp log tail` for real-time container console logs.

## Exercises

* **KEDA** (see [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md)): the queue grows faster than the worker drains it — fix the autoscaling config.
* Break a Kubernetes service selector, a pod's startup command, and a readiness probe path, one at a time — confirm each maps to the diagnostic step in the table above.

## Definition of done

* API and worker run as separate, independently-configured Container Apps; the worker isn't publicly reachable.
* ACR Tasks rebuild on commit, on base-image update, and on a schedule.
* KEDA scales the worker from zero based on queue depth.
* A revision label provides a stable test URL independent of the "latest" revision.
* Image pulls use managed identity, not admin credentials.
* The worker has an AKS deployment path with manifests and a written diagnostic runbook.
* `/docs/ai-200/container-apps.md`, `/docs/ai-200/keda.md`, and `/docs/ai-200/aks.md` are written per the template, each ending with an "AI-200 skills covered" list.

Next: [08-security-and-config.md](08-security-and-config.md).
