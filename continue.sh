#!/bin/bash
################################################################################
#
# Scrip Created by http://CryptoLions.io
# https://github.com/CryptoLions/EOS-Jungle-Testnet
#
###############################################################################


DATADIR="../../data"

sh -c 'pkill nodeos'
echo -e "Starting Nodeos \n";

# start to continue
nodeos --max-irreversible-block-age 108000 --data-dir $DATADIR --config-dir $DATADIR "$@" > $DATADIR/stdout.txt 2> $DATADIR/stderr.txt &  echo $! > $DATADIR/nodeos.pid

# start to replay
#$NODEOSBINDIR/nodeos --replay-blockchain --wasm-runtime wavm --max-irreversible-block-age 108000 --data-dir $DATADIR --config-dir $DATADIR "$@" > $DATADIR/stdout.txt 2> $DATADIR/stderr.txt &  echo $! > $DATADIR/nodeos.pid


#nodeos --genesis-json /mnt/c/github/fsc/eos-tools/genesis.json --max-irreversible-block-age 108000 --data-dir /mnt/c/github/fsc/eos-tools --config-dir /mnt/c/github/fsc/eos-tools