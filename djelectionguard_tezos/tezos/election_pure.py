import smartpy as sp


class ElectionGuard(sp.Contract):
    def __init__(self, admin):
        self.init(
            admin=admin,
            manifest_url='',
            manifest_hash='',
            open='',
            close='',
            artifacts_url='',
            artifacts_hash='',
        )

    @sp.entry_point
    def open(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.open = params.open
        self.data.manifest_url = params.manifest_url
        self.data.manifest_hash = params.manifest_hash

    @sp.entry_point
    def close(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.close = params

    @sp.entry_point
    def artifacts(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.artifacts_url = params.artifacts_url
        self.data.artifacts_hash = params.artifacts_hash

