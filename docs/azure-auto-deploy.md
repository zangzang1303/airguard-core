# Azure auto-deploy

Pushes to the `Canh` branch trigger `.github/workflows/deploy-azure.yml`.
The workflow validates the public Compose file, verifies the Azure VM ED25519 host fingerprint,
and connects with the repository secret `AZURE_DEPLOY_SSH_KEY`.

The deploy key is intentionally restricted in the VM `authorized_keys` entry:

- `restrict` disables forwarding, PTY allocation, X11 and user RC execution.
- `command="/usr/local/sbin/airguard-deploy"` ignores arbitrary remote commands and runs only the
  root-owned deployment wrapper.
- The workflow sends a Git bundle for its exact `GITHUB_SHA`; the wrapper verifies that the bundle
  head matches this SHA and refuses non-fast-forward updates. The private team repository therefore
  needs no credential on the VM.
- The wrapper refuses a dirty checkout, rebuilds the public Compose stack, preserves named volumes
  and verifies the public readiness endpoint.

Normal release flow:

```powershell
git add <files>
git commit -m "feat: describe the change"
git push origin Canh
```

Do not commit `.env`, private keys or tokens. Environment changes remain a separate manual action
in `/home/azureuser/airguard-demo.env` on the VM.

If the deploy key must be rotated, generate a new dedicated key, replace the restricted
`authorized_keys` line, update `AZURE_DEPLOY_SSH_KEY`, verify one workflow run, and revoke the old
line.
