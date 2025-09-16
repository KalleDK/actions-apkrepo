# Create APK Repo

Used to generate and sign an APK repository

```yaml
- name: Build APK Repo
  uses: KalleDK/actions-apkrepo@v0.0.30
  id: build_apkrepo
  with:
    abuild_packager: ${{ vars.ABUILD_PACKAGER }}
    abuild_key_name: ${{ vars.ABUILD_KEY_NAME }}
    abuild_key_priv: ${{ secrets.ABUILD_KEY_PRIV }}
    abuild_key_pub: ${{ secrets.ABUILD_KEY_PUB }}
    abuild_repo_url: https://<username>.github.io/apk
```