#!/usr/bin/python
import os
import random
from shutil import copyfile, copytree
from config import IP
from constant import (BIOS_DOCKER_COMPOSE,
                      CMD_PREFIX,
                      CMD_PREFIX_KEOSD,
                      SYSTEM_ACCOUNTS,
                      DOCKER_IMAGE)

WALLET_SCRIPT = os.path.abspath(os.path.join(os.getcwd(), "scripts/bios/create_wallet.sh"))
BIOS_KEYS = os.path.abspath(os.path.join(os.getcwd(), 'config/bios_keys'))
IP_PORTS = os.path.abspath(os.path.join(os.getcwd(), 'config/ip_ports'))

def cmd_wrapper(cmd, prefix=CMD_PREFIX):
    return " ".join([prefix, cmd, '\n'])

def process_keys(f, as_list=True):
    keys = []
    key_pair = {}
    key_pairs = []
    with open(f) as key_file:
        for line in key_file:
            name, key = line.strip().split(': ')
            if not name in key_pair:
                key_pair[name] = key
            if len(key_pair.keys()) == 2:
                #key_line = 'private-key = ["%s", "%s"]'
                key_line = 'signature-provider=%s=KEY:%s'
                keys.append(key_line % (key_pair['Public key'], key_pair['Private key']))
                key_pairs.append(key_pair)
                key_pair = {}
    return keys if as_list else key_pairs


def process_ips(f, as_list=True):
    keys = []
    key_pair = {}
    key_pairs = []
    with open(f) as key_file:
        for line in key_file:
            name, key = line.strip().split(': ')
            if not name in key_pair:
                key_pair[name] = key
            if len(key_pair.keys()) == 2:
                key_line = '%s:%s'
                keys.append(key_line % (key_pair['IP'], key_pair['PORT']))
                key_pairs.append(key_pair)
                key_pair = {}
    return keys if as_list else key_pairs


def generate():
    genesis = open('./config/genesis.json', 'w')
    pub_key = process_keys(BIOS_KEYS, as_list=False)[0]['Public key']
    content = open('./genesis-tmpl').read().replace('PUBKEY', pub_key)
    # print content, pub_key
    genesis.write(content)
    genesis.close()

    d = './scripts/bios'
    if not os.path.exists(d):
        os.mkdir(d)
    else:
        os.system("rm -rf " + './scripts/bios')
        os.mkdir(d)

    dest_genesis = os.path.abspath(os.path.join(os.getcwd(), 'scripts/bios/genesis.json'))
    copyfile('./genesis.json', dest_genesis)

    ip_ports = process_ips(IP_PORTS, as_list=False)
    index = 0
    prods = []
    for ip_key in ip_ports:
        current_ip = ip_key['IP']
        current_port = ip_key['PORT']

        d = './scripts/' + current_ip
        if not os.path.exists(d):
            os.mkdir(d)
        else:
            os.system("rm " + './scripts/' + current_ip + '/*')

        dest_genesis = os.path.abspath(os.path.join(os.getcwd(), 'scripts/' + current_ip + '/genesis.json'))
        copyfile('./genesis.json', dest_genesis)

        config_dest = os.path.abspath(os.path.join(os.getcwd(), 'scripts/' + current_ip + '/config.ini'))
        config_tmpl = open('./config.ini').read()

        bios_config_dest = os.path.abspath(os.path.join(os.getcwd(), 'scripts/bios/config.ini'))

        peers = []
        
        for ip_key2 in ip_ports:
            current_ip2 = ip_key2['IP']
            current_port2 = ip_key2['PORT']

            if current_ip2 != current_ip:
                peers.append('p2p-peer-address = %s:%s' % (current_ip2, current_port2))

        keys = process_keys(os.path.join('./config', current_ip + '/bp_keys'))

        account_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/bios/03_create_accounts.sh')), 'a')
        reg_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/' +current_ip + '/02_reg_producers.sh')), 'w')


        for i in range(0, len(keys)):
            bp_name = 'bp%d' % index
            index = index + 1
            prods.append(bp_name)
            pub = keys[i].split('=')[1]
            pri = keys[i].split('=')[2][:3]
            cmd = 'system newaccount eosio {bp_name} {pub} {pub} --stake-net "1000000.0000 EOS" --stake-cpu "1000000.0000 EOS" --buy-ram-kbytes "128000"'
            account_script.write(cmd_wrapper(cmd.format(pub=pub, bp_name=bp_name)))
            cmd = 'system regproducer {bp_name} {pub}'
            reg_script.write(cmd_wrapper(cmd.format(pub=pub, bp_name=bp_name)))

        account_script.close()
        reg_script.close()

        config = config_tmpl.format(bp_name=bp_name, port=current_port, http_port='8888', keys='\n'.join(keys),
                                    peers='\n'.join(peers), stale_production='false')
        with open(config_dest, 'w') as dest:
            dest.write(config)

        generate_import_script(current_ip)
        generate_wallet_script(current_ip)
        copyfile('./start.sh', './scripts/' + current_ip + '/start.sh')
        copyfile('./continue.sh', './scripts/' + current_ip + '/continue.sh')

    generate_import_script('bios')
    generate_voters('bios', prods)
    bios_keys = process_keys(BIOS_KEYS)
    # generate bios node config
    bios_config = config_tmpl.format(bp_name='eosio', port='9876', http_port='8888', keys=bios_keys[0], peers='', stale_production='true')
    with open(bios_config_dest, 'w') as dest:
        dest.write(bios_config)

    generate_wallet_script('bios')



def generate_import_script(current_ip):
    keys = []
    bp_keys_path = os.path.abspath(os.path.join(os.getcwd(), 'config', current_ip + '/bp_keys'))
    voter_keys_path = os.path.abspath(os.path.join(os.getcwd(), 'config/voter_keys'))
    if current_ip == 'bios':
        for f in [BIOS_KEYS, voter_keys_path]:
            keys.extend(process_keys(f, as_list=False))
    else:
        for f in [bp_keys_path]:
            keys.extend(process_keys(f, as_list=False))

    import_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/' +current_ip + '/01_import_keys.sh')), 'w')

    for key_pair in keys:
        pub = key_pair['Public key']
        priv = key_pair['Private key']
        cmd = 'wallet import --private-key=%s || true' % priv
        import_script.write(cmd_wrapper(cmd))
    import_script.close()


def generate_voters(current_ip, prods):
    voter_keys_path = os.path.abspath(os.path.join(os.getcwd(), 'config/voter_keys'))
    voter_keys = process_keys(voter_keys_path, as_list=False)
    account_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/' + current_ip + '/03_create_accounts.sh')), 'a')


    token_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/' + current_ip + '/04_issue_voter_token.sh')), 'w')
    delegate_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/' + current_ip + '/05_delegate_voter_token.sh')), 'w')
    vote_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/' + current_ip + '/06_vote.sh')), 'w')
    i = 0
    for key_pair in voter_keys:
        i += 1
        account = 'voter%d' % i
        pub = key_pair['Public key']
        priv = key_pair['Private key']
        cmd = 'system newaccount eosio {bp_name} {pub} {pub} --stake-net "1000000.0000 EOS" --stake-cpu "1000000.0000 EOS" --buy-ram-kbytes "128000"'
        account_script.write(cmd_wrapper(cmd.format(pub=pub, bp_name=account)))
        cmd = """push action eosio.token issue '{"to":"%s","quantity":"60000000.0000 EOS","memo":"issue"}' -p eosio""" % account
        token_script.write(cmd_wrapper(cmd))
        random.shuffle(prods)
        if len(prods) > 2:
            bps = ' '.join(list(set(prods[:len(prods)-2])))
        else:
            bps = ' '.join(prods)
        cmd = 'system voteproducer prods %s %s' % (account, bps)
        vote_script.write(cmd_wrapper(cmd))
        cmd = 'system delegatebw %s %s "25000000 EOS" "25000000 EOS"' % (account, account)
        delegate_script.write(cmd_wrapper(cmd))
    account_script.close()
    token_script.close()
    vote_script.close()
    delegate_script.close()


def generate_eosio_token():
    eosio_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/bios/02_create_token.sh')), 'a')
    cmd = cmd_wrapper('set contract eosio.token contracts/eosio.token')
    cmd += cmd_wrapper("""push action eosio.token create '{"issuer":"eosio", "maximum_supply": "1000000000.0000 EOS", "can_freeze": 0, "can_recall": 0, "can_whitelist": 0}' -p eosio.token""")
    cmd += cmd_wrapper("""push action eosio.token issue '{"to":"eosio","quantity":"100000000.0000 EOS","memo":"issue"}' -p eosio""")
    cmd += cmd_wrapper("set contract eosio.msig contracts/eosio.msig")
    cmd += cmd_wrapper("""push action eosio setpriv '{"account": "eosio.msig", "is_priv": 1}' -p eosio""")
    cmd += cmd_wrapper("set contract eosio contracts/eosio.system")
    cmd += cmd_wrapper("set contract eosio.wrap contracts/eosio.wrap")
    cmd += cmd_wrapper("""push action eosio setpriv '{"account": "eosio.wrap", "is_priv": 1}' -p eosio""")
    cmd += cmd_wrapper("""push action eosio init '[0,"4,EOS"]' -p eosio@active""")
    eosio_script.write(cmd)
    eosio_script.close()


def generate_sys_accounts():
    # generate sys account
    eosio_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/bios/02_create_token.sh')), 'w')

    eosio_script.write(cmd_wrapper('set contract eosio contracts/eosio.bios'))

    pub = process_keys(BIOS_KEYS, as_list=False)[0]['Public key']
    for account in SYSTEM_ACCOUNTS:
        cmd = 'create account eosio {account} {pub} {pub}'
        eosio_script.write(cmd_wrapper(cmd.format(pub=pub, account=account)))
    eosio_script.close()


def generate_wallet_script(current_ip):
    wallet_script = open(os.path.abspath(os.path.join(os.getcwd(), 'scripts/' + current_ip + '/00_create_wallet.sh')), 'w')
    wallet_script.write(cmd_wrapper("sh -c 'rm /opt/eosio/bin/data-dir/default.wallet'", ""))
    wallet_script.write(cmd_wrapper("sh -c 'rm ~/eosio-wallet/default.wallet'", ""))
    wallet_script.write(cmd_wrapper("cleos wallet create -n default --to-console > wallet_password", ""))
    wallet_script.close()


def generate_boot_script():
    os.system("rm 0*.sh")
    if not os.path.exists('./data'):
        os.mkdir('./data')
    if not os.path.exists('./scripts'):
        os.mkdir('./scripts')

if __name__ == '__main__':
    generate()
    generate_boot_script()
    generate_sys_accounts()
    generate_eosio_token()
    copyfile('./start.sh', './scripts/bios/start.sh')
    copyfile('./bios_keys', './config/bios_keys')
    copytree('./contracts/build/contracts', './scripts/bios/contracts')


    os.system("chmod u+x *.sh")
