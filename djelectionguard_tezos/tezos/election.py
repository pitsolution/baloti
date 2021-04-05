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
    def open(self, date, manifest_url, manifest_hash):
        sp.verify(sp.sender == self.data.admin)
        self.data.open = date
        self.data.manifest_url = manifest_url
        self.data.manifest_hash = manifest_hash

    @sp.entry_point
    def close(self, date):
        sp.verify(sp.sender == self.data.admin)
        self.data.close = date

    @sp.entry_point
    def artifacts(self, url, hash):
        sp.verify(sp.sender == self.data.admin)
        self.data.artifacts_url = url
        self.data.artifacts_hash = hash


@sp.add_test(name="ElectionGuard")
def test():
    scenario = sp.test_scenario()
    alice = sp.test_account("alice")

    scenario.h1("Election create")
    contract = ElectionGuard(alice.address)
    scenario += contract
    scenario.h1('Election open')
    scenario += contract.open(date='2020-21-23', manifest_url='http://test', manifest_hash='d34db33f').run(sender=alice)
    scenario.h1('Election close')
    scenario += contract.close('2020-21-23').run(sender=alice)
    scenario.h1('Election artifacts')
    scenario += contract.artifacts(url='http://test', hash='d34db33f').run(sender=alice)
