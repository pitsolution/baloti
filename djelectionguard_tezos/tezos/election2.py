import smartpy as sp


class ElectionGuard(sp.Contract):
    def __init__(self, admin, cofactor, generator, large_prime, small_prime,
                 crypto_base_hash, crypto_extended_base_hash, elgamal_public_key,
                 manifest_url, manifest_hash):
        self.init(
            admin=admin,
            cofactor=cofactor,
            generator=generator,
            large_prime=large_prime,
            small_prime=small_prime,
            crypto_base_hash=crypto_base_hash,
            crypto_extended_base_hash=crypto_extended_base_hash,
            elgamal_public_key=elgamal_public_key,
            manifest_hash=manifest_hash,
            manifest_url=manifest_url,
            open='',
            close='',
            artifacts_url='',
            artifacts_hash='',
            tally={},
        )

    @sp.entry_point
    def open(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.open = params.open

    @sp.entry_point
    def close(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.close = params.close

    @sp.entry_point
    def publish(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.artifacts_url = params.url
        self.data.artifacts_hash = params.hash

    @sp.entry_point
    def tally(self, params):
        self.data.tally[params.candidate] = params.score


@sp.add_test(name="ElectionGuard")
def test():
    scenario = sp.test_scenario()
    alice = sp.test_account("alice")

    scenario.h1("Election create")
    contract = ElectionGuard(
        alice.address,
        "cofactor goes here",
        "generator goes here",
        "large prime goes here",
        "small prime goes here",
        "crypto base hash goes here",
        "crypto extended hash goes here",
        "elgamal public key goes here",
        "http://manfest/url",
        "manifest hash goes here",
    )
    scenario += contract
    scenario.h1('Election open')
    scenario += contract.open(open='2020-01-01T12:30').run(sender=alice)
    scenario.h1('Election close')
    scenario += contract.close(close='2020-01-01T18:30').run(sender=alice)
    scenario.h1('Election publish artifacts')
    scenario += contract.publish(url='http://path', hash='12312312').run(sender=alice)
    scenario.h1('Election publish tally for first candidate')
    scenario += contract.tally(candidate='123-322', score=12).run(sender=alice)
    scenario.h1('Election publish tally for second candidate')
    scenario += contract.tally(candidate='123-552', score=2).run(sender=alice)
