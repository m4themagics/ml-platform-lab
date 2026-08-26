# Infrastructure

Empty by design at the paused M1 checkpoint. There is no current infrastructure work. After an
explicit resume, infrastructure starts only with author-owned M3 `kind` decisions;
cloud/Terraform remains outside the retained M1–M4 scope.

Retained local implementation order after resume:

1. local service dependencies;
2. `kind` cluster and native Kubernetes resources;
3. observability and rollout components.

Terraform bootstrap and AWS remain separately deferred. No cloud configuration enters this
directory until the local release/recovery slice works and a new budget plus destroy gates in
`configs/platform.toml` are explicitly approved.
