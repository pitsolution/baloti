Storage: sp.TRecord(admin = sp.TAddress, manifest_url = sp.TString).layout(("admin", "manifest_url"))
Params: sp.TVariant(manifest = sp.TRecord(url = sp.TString).layout("url")).layout("manifest")