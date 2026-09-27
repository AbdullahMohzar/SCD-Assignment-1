# ADR 0003: Immutable Deployments via Git Commit SHA References

## Status
Accepted

## Context
In containerized environments, deploying images tagged with mutable identifiers such as `:latest`, `:dev`, or `:prod` introduces severe operational risks:
1. **Ambiguity**: An operator or incident responder cannot definitively answer "What exact code is currently running in production?" from a tag alone.
2. **Non-Reproducibility**: Kubernetes nodes cache images based on `imagePullPolicy`. Two pods in the same Deployment replica set can pull different container layers if `:latest` was rebuilt upstream, resulting in split-brain behavior.
3. **Rollback Hazards**: Reverting an outage by re-applying a manifest that references `:latest` does not roll back to the prior code state.

## Decision
We enforce immutable deployments across all delivery pipelines:
1. **Commit SHA Tagging**: Every build job in CI/CD tags container images with the exact 40-character Git commit SHA (`${{ github.sha }}`) alongside semantic versions for tagged releases.
2. **Kustomize Image Rewriting**: In `cd.yml`, Kustomize automatically patches manifests using `kustomize edit set image` to insert the immutable SHA reference before applying overlays to the cluster.
3. **Auditability**: Running `kubectl get deployment backend -o jsonpath='{.spec.template.spec.containers[0].image}'` returns an immutable SHA that can be pasted directly into `git show <SHA>` to audit the exact source tree running in production.

## Consequences
- **Positive**:
  - Deterministic rollouts and predictable rolling updates.
  - Trivial declarative rollbacks: re-applying a previous commit SHA manifest immediately reverts the running workload.
  - Strict traceability from production container to Git pull request and author.
- **Negative**:
  - Container registries accumulate multiple image tags over time, necessitating automated lifecycle retention rules.
