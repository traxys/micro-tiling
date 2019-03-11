# import asyncio
from aiosmtpd.controller import Controller
import time
import json
import gnupg
import split
import database
import ensicoin
import os
import socket


SOLIDATOR_ADDRESS = os.environ["SOLIDATOR_ADDRESS"]
SOLIDATOR_PORT = os.environ["SOLIDATOR_PORT"]


def decrypt(string):
    gpg = gnupg.GPG(gnupghome='.')

    sec_file = open("keys/sec.gpg", "r")
    gpg.import_keys(sec_file.read())
    sec_file.close()

    pass_file = open("keys/passphrase", "r")
    passphrase = json.loads(pass_file.read())
    pass_file.close()

    decrypt = gpg.decrypt(string, passphrase=passphrase, always_trust=True)
    return str(decrypt)


class Handler:
    async def handle_RCPT(self,
                          server,
                          session,
                          envelope,
                          address,
                          rcpt_options):
        if not address.endswith('@micro-tiling.tk'):
            return '550 not relaying to that domain'

        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        message = envelope.content.decode('utf8', errors='replace')
        message = decrypt(message)

        job_id = message.split("|")[0]
        database.update_state(database.open_db(), 20, job_id)
        segments = message.split("|")[1].strip()
        new_segments = []
        for (x1, y1), (x2, y2) in segments:
            new_segments.append(split.Segment(split.Vect(x1, y1),
                                              split.Vect(x2, y2)))
        database.update_state(database.open_db(), 21, job_id)
        cut_segments = split.cut(new_segments)
        database.update_state(database.open_db(), 22, job_id)

        pk1, sk1 = ensicoin.generate_keys()
        database.open_db().write("/{}/address", sk1)
        pk2, sk2 = ensicoin.generate_keys()

        solidator_socket = socket.create_connection((SOLIDATOR_ADDRESS,
                                                     SOLIDATOR_PORT))
        solidator_socket.send(pk2.encode())
        hashtx, _ = ensicoin.wait_for_pubkey(pk1)
        ensicoin.send_to(10,
                         hashtx,
                         0,
                         sk1,
                         1,
                         pk2,
                         [job_id,
                          json.dumps(cut_segments)])

        return '250 Message accepted for delivery'


controller = Controller(Handler())
controller.start()

while True:
    time.sleep(1)
