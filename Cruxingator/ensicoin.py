"""Wrapper around ensicoincoin-cli
"""
import subprocess
import os

def generate_keys():
    """Generates a pair of (**private_key**, **public_key**)
    """
    output = subprocess.check_output(['ensicoincoin-cli', 'createwallet'])
    priv_key, pub_key = output.decode('ASCII').split('\n')[:2]

    priv_key = priv_key.split(':')[1].strip()
    pub_key = pub_key.split(':')[1].strip()

    print(priv_key, pub_key)

    return (priv_key, pub_key)


def wait_for_pubkey(pubKey):
    """Blocks until a transaction is issued by *pubKey*
    """
    output = subprocess.check_output(['ensicoincoin-cli', 'waitforpubkey', '--pubkey', pubKey])
    lines = output.decode('ASCII').split('\n')
    flags = lines[1:len(lines) - 1]

    return (lines[0], flags)


def wait_for_flag(flag):
    """Blocks until a transaction is issued containing *flag*
    """
    output = subprocess.check_output(['ensicoincoin-cli', 'waitforflag', '--flag', flag])
    flags = output.decode('ASCII').split('\n')[1:]
    flags = flags[:len(flags) - 1]

    return flags


def send_to(value, outpoint_hash, outpoint_index, privkey_from, spent_output_value, pubkey_to, flags, uid):
    """Sends a transaction
    """
    args = ['ensicoincoin-cli', 'sendto',
            '--outpointhash', outpoint_hash,
            '--outpointindex', str(outpoint_index),
            '--value', str(value),
            '--flagsfile', uid + '.txt']

    if pubkey_to != '':
        args.append('--pubkey')
        args.append(pubkey_to)

    if privkey_from != '':
        args.append('--privkey')
        args.append(privkey_from)
        args.append('--spentoutputvalue')
        args.append(str(spent_output_value))

    print(args)

    f = open(uid + '.txt', 'w')

    for flag in flags:
        f.write(flag + '\n')

    f.close()

    output = subprocess.check_output(args)

    print(output)

    os.remove(uid + '.txt')

    return output.decode('ASCII').split('\n')[0]
