# Azure auto-deploy

Pushes to `Canh` trigger the Azure deployment workflow. The workflow validates the public Compose topology, sends an immutable Git bundle to the VM through the restricted deployment key, and verifies `/backend/ready` after the release.

Secrets and server environment values remain on the Azure VM; do not commit them.
