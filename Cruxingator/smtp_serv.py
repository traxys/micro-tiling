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


SOLIDATOR_ADDRESS = "localhost"
if "SOLIDATOR_ADDRESS" in os.environ:
    SOLIDATOR_ADDRESS = os.environ["SOLIDATOR_ADDRESS"]

SOLIDATOR_PORT = 2442
if "SOLIDATOR_PORT" in os.environ:
    SOLIDATOR_PORT = int(os.environ["SOLIDATOR_PORT"])


def decrypt(string):
    """Decrypts the *string* using gpg
    """
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
    """Handles SMTP requests
    """
    async def handle_RCPT(self,
                          server,
                          session,
                          envelope,
                          address,
                          rcpt_options):
        """Refuse all mails not in @micro-tiling.tk
        """
        print('handle_RCPT')
        
        if not address.endswith('@micro-tiling.tk'):
            return '550 not relaying to that domain'

        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        """Handles the content of a mail
        """
        print('handle_DATA')

        message = envelope.content.decode('utf8', errors='replace')
        message = decrypt(message)

        job_id = message.split("|")[0].strip()
        database.update_state(database.open_db(), 20, job_id)
        segments = json.loads(message.split("|")[1].strip())

        print('segments', segments)

        new_segments = []
        for (x1, y1), (x2, y2) in segments:
            new_segments.append(split.Segment(split.Vect(x1, y1),
                                              split.Vect(x2, y2)))
        database.update_state(database.open_db(), 21, job_id)
        cut_segments = split.cut(new_segments)
        database.update_state(database.open_db(), 22, job_id)

        print('job_id: ', job_id)

        sk1, pk1 = ensicoin.generate_keys()
        database.open_db().write("/{}/address".format(job_id), pk1)
        sk2, pk2 = ensicoin.generate_keys()

        print('connecting to solidator')

        solidator_socket = socket.create_connection((SOLIDATOR_ADDRESS,
                                                     SOLIDATOR_PORT))
        
        print('sending pk2')

        solidator_socket.send(pk2.encode())
        database.update_state(database.open_db(), 23, job_id)
        
        print('waiting for payment')
        
        hashtx, _ = ensicoin.wait_for_pubkey(pk1)

        print('hashtx: ', hashtx)

        ensicoin.send_to(10,
                         hashtx,
                         0,
                         sk1,
                         42,
                         pk2,
                         [job_id,
                          "'" + json.dumps(split.generate_id_tuple(cut_segments)) + "'"], job_id)

        print('payment sent')

        database.update_state(database.open_db(), 24, job_id)

        return '250 Message accepted for delivery'


if __name__ == "__main__":
    controller = Controller(Handler(), hostname="0.0.0.0")
    controller.start()

    while True:
        time.sleep(1)
