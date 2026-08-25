# Infrastructure

Empty by design at the M1 checkpoint. Infrastructure work starts only with author-owned M3
`kind` decisions; cloud/Terraform remains outside the active M1–M4 scope.

Implementation order:

1. local service dependencies;
2. `kind` cluster and native Kubernetes resources;
3. observability and rollout components;
4. Terraform bootstrap state;
5. Terraform AWS environment.

No cloud configuration enters this directory until the local release/recovery slice works and
the budget plus destroy gates in `configs/platform.toml` are set.
