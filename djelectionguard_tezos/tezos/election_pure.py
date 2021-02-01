import smartpy as sp


class ElectionGuard(sp.Contract):
    def __init__(self, admin):
        self.init(
            admin=admin,
            manifest_url='',
        )

    @sp.entry_point
    def manifest(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.manifest_url = params.url

@sp.add_test(name="StoreValue")
def test():
    scenario = sp.test_scenario()
    alice = sp.test_account("alice")

    scenario.h1("Election create")
    contract = StoreValue(alice.address)
    scenario += contract
    scenario.h1('Election manifest')
    scenario += contract.manifest(url='http://test').run(sender=alice)

