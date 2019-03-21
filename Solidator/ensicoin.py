"""Wrapper around ensicoincoin-cli
"""
import subprocess


def generate_keys():
    """Generates a pair of (**private_key**, **public_key**)
    """
    output = subprocess.check_output(['ensicoincoin-cli', 'createwallet'])
    priv_key, pub_key = output.decode('ASCII').split('\n')[:2]

    priv_key = priv_key.split(':')[1].strip()
    pub_key = pub_key.split(':')[1].strip()

    return (priv_key, pub_key)


def wait_for_pubkey(pubKey):
    """Blocks until a transaction is issued by *pubKey*
    """
    print('waiting for pubkey: ' + pubKey)

    output = subprocess.check_output(['ensicoincoin-cli', 'waitforpubkey', '--pubkey', pubKey])
    
    print('received', output)

    lines = output.decode('ASCII').split('\n')
    flags = lines[1:len(lines) - 1]

    print(flags)

    for (i, flag) in enumerate(flags):
        if flag[0] == "'":
            flag = flag[1:]
        if flag[len(flag)-1] == "'":
            flag = flag[:-1]
        
        flags[i] = flag

    print(lines, flags)

    return (lines[0], flags)


def wait_for_flag(flag):
    """Blocks until a transaction is issued containing *flag*
    """
    output = subprocess.check_output(['ensicoincoin-cli', 'waitforflag', '--flag', flag])
    flags = output.decode('ASCII').split('\n')[1:]
    flags = flags[:len(flags) - 1]

    return flags


def send_to(value, outpoint_hash, outpoint_index, privkey_from, spent_output_value, pubkey_to, flags):
    """Sends a transaction
    """
    args = ['ensicoincoin-cli', 'sendto',
            '--outpointhash', outpoint_hash,
            '--outpointindex', str(outpoint_index),
            '--value', str(value)]

    for flag in flags:
        args.append('--flag')
        args.append(flag)

    if pubkey_to != '':
        args.append('--pubkey')
        args.append(pubkey_to)

    if privkey_from != '':
        args.append('--privkey')
        args.append(privkey_from)
        args.append('--spentoutputvalue')
        args.append(str(spent_output_value))

    output = subprocess.check_output(args)

    return output.decode('ASCII').split('\n')[0]
