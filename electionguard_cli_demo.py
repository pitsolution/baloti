import json
import uuid
import pickle
import os

from multiprocessing import freeze_support


if __name__ == '__main__':
    freeze_support()

    number_of_guardians = 1
    qorum = 1

    from electionguard.election import ElectionDescription
    with open('election-manifest.json', 'r') as manifest:
        string_representation = manifest.read()
        election_description = ElectionDescription.from_json(string_representation)

    from electionguard.election_builder import ElectionBuilder
    builder = ElectionBuilder(
        number_of_guardians=number_of_guardians,
        quorum=qorum,
        description=election_description,
    )

    from electionguard.guardian import Guardian
    guardians = [Guardian('guardian', 0, number_of_guardians, qorum)]
    guardians_pickled = pickle.dumps(guardians)

    # Create Joint Public key
    from electionguard.key_ceremony import CeremonyDetails
    from electionguard.key_ceremony_mediator import KeyCeremonyMediator
    details = CeremonyDetails(number_of_guardians, qorum)
    mediator = KeyCeremonyMediator(details)
    for guardian in guardians:
        mediator.announce(guardian)
    orchestrated = mediator.orchestrate()
    verified = mediator.verify()
    joint_public_key = mediator.publish_joint_key()
    builder.set_public_key(joint_public_key)
    metadata, context = builder.build()

    # Generate a random master nonce value to use as a secret when encrypting the ballot
    from electionguard.encrypt import EncryptionDevice, EncryptionMediator
    device = EncryptionDevice("polling-place-one")
    encrypter = EncryptionMediator(metadata, context, device)

    # Create a store for all our boxes
    from electionguard.ballot_store import BallotStore
    store = BallotStore()

    # We will use only one box
    from electionguard.ballot_box import BallotBox
    ballot_box = BallotBox(metadata, context, store)

    # Only one contest for now
    contest = election_description.contests[0]

    # And only one ballot style
    ballot_style = election_description.ballot_styles[0]

    # Let's cast ballots on the fly
    from electionguard.ballot import PlaintextBallot, PlaintextBallotContest, PlaintextBallotSelection

    print(f'Your are going to cast your ballot for contest: {contest.name}')
    print('Choices are:')
    for i, selection in enumerate(contest.ballot_selections):
        candidate = None
        for candidate in election_description.candidates:
            if candidate.object_id == selection.candidate_id:
                break
        if candidate.object_id != selection.candidate_id:
            print('Candidate not found in selection: {selection.candidate_id}')
            continue
        print(f'{i}) {candidate.ballot_name.text[0].value}')


    while True:
        choice = input('Next voter choice or ENTER to finish: ')
        if not choice.isdigit():
            break

        choice = int(choice)
        for i, selection in enumerate(contest.ballot_selections):
            if i == choice:
                ballot = PlaintextBallot(
                    object_id=uuid.uuid4(),
                    ballot_style=ballot_style.object_id,
                    contests=[
                        PlaintextBallotContest(
                            object_id=contest.object_id,
                            ballot_selections=[
                                PlaintextBallotSelection(
                                    object_id=selection.object_id,
                                    vote='True',
                                    is_placeholder_selection=False,
                                    extended_data=None,
                                )
                            ]
                        )
                    ]
                )
                encrypted_ballot = encrypter.encrypt(ballot)
                ballot_box.cast(encrypted_ballot)
                break

    # Append from box to tally
    from electionguard.tally import CiphertextTally
    tally = CiphertextTally('tally-0', metadata, context)
    for ballot in store.all():
        assert tally.append(ballot)

    from electionguard.decryption_mediator import DecryptionMediator
    decryption_mediator = DecryptionMediator(metadata, context, tally)

    # guardians are back
    guardians = pickle.loads(guardians_pickled)

    # Decrypt the tally with available guardian keys
    decryption_share = decryption_mediator.announce(guardians[0])

    plaintext_tally = decryption_mediator.get_plaintext_tally()

    # we use only one single contest in this script
    contest_tally = plaintext_tally.contests['unniversity-leader']

    print('Results:')
    for i, selection in enumerate(contest.ballot_selections):
        for candidate in election_description.candidates:
            if candidate.object_id == selection.candidate_id:
                tally_selection = contest_tally.selections[selection.object_id]
                print(f'{i}) {candidate.ballot_name.text[0].value}: {tally_selection.tally}')
