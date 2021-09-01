#!/usr/bin/env python3
"""
ElectionGuard CLI for basic stress tests.

0. Start by creating an election-manifest.json in the current working
   directory.
1. Run the electionguard-cli.py build command with the number of stores and
   guardians that you want.
2. Then, either run the benchmark command and let it run for a while, either
   run the cast and tally commands manually.
"""

import asyncio
import cli2
import datetime
import json
import multiprocessing
import os
import pickle
import random
import subprocess
import sys
import time
import uuid

from multiprocessing import freeze_support
freeze_support()  # Mac M1 support


class TimedCommand(cli2.Command):
    def __call__(self, *argv):
        start = time.time_ns()
        result = super().__call__(*argv)
        end = time.time_ns()
        total = end - start
        print(f'{self.target.__name__} seconds: {total / 1_000_000_000}')
        return result


cli = cli2.Group(doc=__doc__, cmdclass=TimedCommand)


@cli.cmd
def builder(quorum=1, number_of_guardians=1):
    """
    Return ElectionBuilder for the cturrent directory.

    Note that you need to have a valid election-manifest.json.
    """
    from electionguard.election_builder import ElectionBuilder
    return ElectionBuilder(
        number_of_guardians=number_of_guardians,
        quorum=quorum,
        description=description(),
    )


@cli.cmd
def build(
        quorum: int=1,
        number_of_guardians: int=1,
        number_of_devices: int=1,
        number_of_stores: int=None,
        manifest='election-manifest.json',
    ):
    """
    Create files necessary to run an election.

    - build.json: stores path to manifest, quorum, and number_of_guardians
    - guardians.pkl: list of pickled guardians
    - jointkey.pkl: joint public key
    - metadata.pkl: builder metadata
    - context.pkl: builder context
    - devices.pkl: encryption devices
    - store-*.pkl: one store pkl for number_of_stores, defaults to the number
                   of cores
    """
    if not number_of_stores:
        number_of_stores = multiprocessing.cpu_count()
    data = dict(
        quorum=quorum,
        number_of_guardians=number_of_guardians,
        number_of_stores=number_of_stores,
        manifest=manifest,
    )
    description(path=manifest)
    with open('build.pkl', 'wb+') as f:
        f.write(pickle.dumps(data))
    print('build.pkl written')

    from electionguard.guardian import Guardian
    guardians = [
        Guardian(f'guardian_{i}', i, number_of_guardians, quorum)
        for i in range(number_of_guardians)
    ]
    with open('guardians.pkl', 'wb+') as f:
        f.write(pickle.dumps(guardians))
    print('guardians.pkl written')

    from electionguard.key_ceremony import CeremonyDetails
    from electionguard.key_ceremony_mediator import KeyCeremonyMediator
    details = CeremonyDetails(number_of_guardians, quorum)
    mediator = KeyCeremonyMediator('mediator', details)
    for guardian in guardians:
        mediator.announce(guardian.share_public_keys())
    joint_public_key = mediator.publish_joint_key()
    with open('jointkey.pkl', 'wb+') as f:
        f.write(pickle.dumps(joint_public_key))
    print('jointkey.pkl written')

    from electionguard.election_builder import ElectionBuilder
    builder = ElectionBuilder(
        number_of_guardians=number_of_guardians,
        quorum=quorum,
        manifest=description(),
    )
    builder.set_public_key(joint_public_key.joint_public_key)
    builder.set_commitment_hash(joint_public_key.commitment_hash)
    metadata, context = builder.build()
    with open('metadata.pkl', 'wb+') as f:
        f.write(pickle.dumps(metadata))
    print('metadata.pkl written')

    with open('context.pkl', 'wb+') as f:
        f.write(pickle.dumps(context))
    print('context.pkl written')

    from electionguard.encrypt import EncryptionDevice, EncryptionMediator, generate_device_uuid
    import uuid
    devices = [
        EncryptionDevice(
            generate_device_uuid(),
            12345,
            67890,
            str(uuid.uuid4())
        )
        for i in range(number_of_devices)
    ]
    with open('devices.pkl', 'wb+') as f:
        f.write(pickle.dumps(devices))
    print('devices.pkl written')

    from electionguard.data_store import DataStore
    for i in range(number_of_stores):
        with open(f'store-{i}.pkl', 'wb+') as f:
            f.write(pickle.dumps(DataStore()))
        print(f'store-{i}.pkl written')


@cli.cmd
def ballot(style: int=0, selections: int=1):
    """
    Create a random plaintext ballot.
    """
    from electionguard.ballot import (
        PlaintextBallot,
        PlaintextBallotContest,
        PlaintextBallotSelection,
    )

    election_description = description()
    ballot_style = election_description.ballot_styles[style]

    ballot_contests = []
    for unit in ballot_style.geopolitical_unit_ids:
        contest = None
        for contest in election_description.contests:
            if contest.electoral_district_id == unit:
                break
            else:
                continue

        ballot_selections = []
        for i in range(selections):
            choice = random.randint(0, len(contest.ballot_selections) - 1)
            selection = contest.ballot_selections[choice]
            ballot_selections.append(
                PlaintextBallotSelection(
                    object_id=selection.object_id,
                    vote=1,
                    is_placeholder_selection=False,
                    extended_data=None,
                )
            )

        ballot_contests.append(
            PlaintextBallotContest(
                object_id=contest.object_id,
                ballot_selections=ballot_selections,
            )
        )

    ballot = PlaintextBallot(
        object_id=uuid.uuid4(),
        style_id=ballot_style.object_id,
        contests=ballot_contests,
    )
    return ballot


def load(pkl):
    with open(f'{pkl}.pkl', 'rb') as f:
        return pickle.loads(f.read())


@cli.cmd
def encrypt(style: int=0, selections: int=1, device: int=0):
    """
    Encrypt a ballot
    """
    from electionguard.encrypt import EncryptionMediator
    plaintext_ballot = ballot(style=style, selections=selections)
    encrypter = EncryptionMediator(
        load('metadata'),
        load('context'),
        load('devices')[device],
    )
    return encrypter.encrypt(plaintext_ballot)


@cli.cmd
def cast(ballot_style: int=0, selections: int=1, store: int=None, device: int=0):
    """
    Cast a ballot, writes to store pkl file
    """
    from electionguard.ballot_box import BallotBox
    print(f'casting {selections} to store-{store}')
    encrypted_ballot = encrypt(
        style=ballot_style,
        selections=selections,
        device=device,
    )
    if store is None:
        build = load('build')
        store = random.randint(0, build['number_of_stores'] - 1)

    ballot_store = load(f'store-{store}')
    ballot_box = BallotBox(
        load('metadata'),
        load('context'),
        ballot_store,
    )
    ballot_box.cast(encrypted_ballot)
    with open(f'store-{store}.pkl', 'wb') as f:
        f.write(pickle.dumps(ballot_store))
    print(f'casted ballot #{len(ballot_store.all())} of store-{store}.pkl')


@cli.cmd
def tally():
    """Compute the tally"""
    from electionguard.tally import CiphertextTally
    metadata = load('metadata')
    context = load('context')
    build = load('build')
    tally = CiphertextTally('tally', metadata, context)

    print(f'Adding ballots to the tally...')
    start = datetime.datetime.now()
    total = 0
    for i in range(build['number_of_stores']):
        for ballot in load(f'store-{i}').all():
            assert tally.append(ballot)
            total += 1
    delta = datetime.datetime.now() - start
    print(f'Adding {total} ballots to the tally took {delta.total_seconds()} seconds')

    start = datetime.datetime.now()
    print(f'Computing tally for {total} ballots')
    from electionguard.decryption_mediator import DecryptionMediator
    from electionguard.ballot_box import get_ballots
    from electionguard.ballot import BallotBoxState

    submitted_ballots_list = []
    for i in  range(build['number_of_stores']):
        submitted_ballots = get_ballots(load(f'store-{i}'), BallotBoxState.CAST)
        submitted_ballots_list += list(submitted_ballots.values())

    decryption_mediator = DecryptionMediator('decryption-mediator', context)

    guardians = load('guardians')
    for guardian in guardians:
        guardian_key = guardian.share_election_public_key()
        tally_share = guardian.compute_tally_share(tally, context)
        ballot_shares = guardian.compute_ballot_shares(
            submitted_ballots_list, context
        )
        decryption_mediator.announce(guardian_key, tally_share, ballot_shares)

    plaintext_tally = decryption_mediator.get_plaintext_tally(tally)
    print(f'Tallying {total} ballots took {delta.total_seconds()} seconds')

    for contest_key, contest in plaintext_tally.contests.items():
        print(f'Results for contest: {contest_key}')
        for selection_key, selection in contest.selections.items():
            print(f'{selection_key}: {selection.tally}')


@cli.cmd
async def benchmark(votes: int=50):
    """
    Find out the max number of ballots your machine supports.

    We're spawning this script cast and tally commands in subprocesses to avoid
    memleaks.

    It will chain and time these commands until something fails (ie. OOM kill)
    """
    data = load('build')
    i = votes
    total = 0
    while True:
        start = datetime.datetime.now()
        print(f'Casting {data["number_of_stores"]} in parallel')
        procs = [
            (await asyncio.create_subprocess_shell(
                f'{sys.argv[0]} cast store={store}',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )).communicate()
            for store in range(data['number_of_stores'])
        ]
        results = await asyncio.gather(*procs)
        delta = datetime.datetime.now() - start
        print(f'Casting {data["number_of_stores"]} in parallel took {delta.total_seconds()} seconds')

        i -= data['number_of_stores']
        total += data['number_of_stores']
        if i <= 0:
            subprocess.check_call(f'{sys.argv[0]} tally', shell=True)
            i = votes


@cli.cmd(color='green')
def description(path='election-manifest.json'):
    """
    Return the ElectionDescription for the current directory.

    This will parse election-manifest.json and fail if the manifest is invalid,
    otherwise print ElectionDescription.
    """
    from electionguard.manifest import Manifest
    with open(path, 'r') as manifest:
        string_representation = manifest.read()
    return Manifest.from_json(string_representation)


if __name__ == '__main__':
    cli.entry_point()
