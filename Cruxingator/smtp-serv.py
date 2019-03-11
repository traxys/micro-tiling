# import asyncio
from aiosmtpd.controller import Controller
import time
import json
import gnupg
import split

def decode(string):
    f = open("kanji")
    kanji = json.loads(f.read())
    return ''.join(map(lambda k: ord(kanji.index(k)), string))


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
        segments = message.split("|")[1].strip()
        new_segments = []
        for (x1, y1), (x2, y2) in segments:
            new_segments.append(split.Segment(split.Vect(x1, y1),
                                              split.Vect(x2, y2)))
        cut_segments = split.cut(new_segments)

        return '250 Message accepted for delivery'


controller = Controller(Handler())
controller.start()

while True:
    time.sleep(1)