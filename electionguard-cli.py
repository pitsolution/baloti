#!/usr/bin/env python
"""
ElectionGuard CLI for basic stress tests.
"""

import cli2
import json
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
    - store.pkl: a ballot store
    """
    data = dict(
        quorum=quorum,
        number_of_guardians=number_of_guardians,
        manifest=manifest,
    )
    description(path=manifest)
    with open('build.json', 'w+') as f:
        f.write(json.dumps(data))
    print('build.json written')

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
    mediator = KeyCeremonyMediator(details)
    for guardian in guardians:
        mediator.announce(guardian)
    orchestrated = mediator.orchestrate()
    verified = mediator.verify()
    joint_public_key = mediator.publish_joint_key()
    with open('jointkey.pkl', 'wb+') as f:
        f.write(pickle.dumps(joint_public_key))
    print('jointkey.pkl written')

    from electionguard.election_builder import ElectionBuilder
    builder = ElectionBuilder(
        number_of_guardians=number_of_guardians,
        quorum=quorum,
        description=description(),
    )
    builder.set_public_key(joint_public_key)
    metadata, context = builder.build()
    with open('metadata.pkl', 'wb+') as f:
        f.write(pickle.dumps(metadata))
    print('metadata.pkl written')

    with open('context.pkl', 'wb+') as f:
        f.write(pickle.dumps(context))
    print('context.pkl written')

    from electionguard.encrypt import EncryptionDevice
    devices = [
        EncryptionDevice(f'device-{i}')
        for i in range(number_of_devices)
    ]
    with open('devices.pkl', 'wb+') as f:
        f.write(pickle.dumps(devices))
    print('devices.pkl written')

    from electionguard.ballot_store import BallotStore
    with open('store.pkl', 'wb+') as f:
        f.write(pickle.dumps(BallotStore()))
    print('store.pkl written')


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
                    vote='True',
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
        ballot_style=ballot_style.object_id,
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
def cast(style: int=0, selections: int=1, device: int=0):
    """
    Cast a ballot, writes to store.pkl
    """
    from electionguard.ballot_box import BallotBox
    encrypted_ballot = encrypt(
        style=style,
        selections=selections,
        device=device,
    )
    store = load('store')
    ballot_box = BallotBox(
        load('metadata'),
        load('context'),
        store,
    )
    ballot_box.cast(encrypted_ballot)
    with open('store.pkl', 'wb') as f:
        f.write(pickle.dumps(store))
    print(f'casted ballot #{len(store.all())} to store.pkl')


@cli.cmd
def tally():
    """Compute the tally"""
    from electionguard.tally import CiphertextTally
    metadata = load('metadata')
    context = load('context')
    tally = CiphertextTally('tally', metadata, context)
    for ballot in load('store').all():
        assert tally.append(ballot)

    from electionguard.decryption_mediator import DecryptionMediator
    decryption_mediator = DecryptionMediator(metadata, context, tally)
    guardians = load('guardians')
    for guardian in guardians:
        decryption_share = decryption_mediator.announce(guardian)
    plaintext_tally = decryption_mediator.get_plaintext_tally()

    for contest_key, contest in plaintext_tally.contests.items():
        print(f'Results for contest: {contest_key}')
        for selection_key, selection in contest.selections.items():
            print(f'{selection_key}: {selection.tally}')


@cli.cmd
def benchmark():
    """
    Find out the max number of ballots your machine supports.

    We're spawning this script cast and tally commands in subprocesses to avoid
    memleaks.

    It will chain and time these commands until something fails (ie. OOM kill)
    """
    while True:
        subprocess.check_call(f'{sys.argv[0]} cast', shell=True)
        subprocess.check_call(f'{sys.argv[0]} tally', shell=True)


@cli.cmd(color='green')
def description(path='election-manifest.json'):
    """
    Return the ElectionDescription for the current directory.

    This will parse election-manifest.json and fail if the manifest is invalid,
    otherwise print ElectionDescription.
    """
    from electionguard.election import ElectionDescription
    with open(path, 'r') as manifest:
        string_representation = manifest.read()
    return ElectionDescription.from_json(string_representation)


if __name__ == '__main__':
    cli.entry_point()
