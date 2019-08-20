#!/bin/bash
rm -rf ./config/*

echo -n "Enter the number of independent ip machines you want to create:"
read NUM_NODEOS

if [ $NUM_NODEOS -lt 1 ]; then
  echo "The minimum number of independent ip machines cannot be less than 1"
  exit
fi

for (( c=1; c<=$NUM_NODEOS; c++ ))
do
    echo -n "Enter the address of the $c machine:"
	read IP
	echo -n "Enter the port of the $c machine:"
	read PORT
	echo IP: $IP >> ./config/ip_ports
	echo PORT: $PORT >> ./config/ip_ports
	dirname=./config/$IP
	if [ ! -d $dirname  ];then
	  mkdir $dirname
	fi
	
	echo -n "Enter the number of BPs you want to create on this machine:"
	read NUM_BPS

	if [ $NUM_BPS -lt 1 ]; then
	  echo "The minimum number of BPs cannot be less than 3 on this machine"
	  exit
	fi
	
	touch ./config/bp_keys

	> ./config/bp_keys

	echo "(1/3) Generating $NUM_BPS keys for BP account..."
	for (( d=0; d<$NUM_BPS; d++ ))
	do
		cleos create key --to-console >> ./config/$IP/bp_keys
	done
	echo "$NUM_BPS BP keys generated"

done

echo -n "Enter the number of voters you want to create on this machine:"
	read NUM_VOTERS

if [ $NUM_VOTERS -lt 3 ]; then
  echo "NUM_VOTERS must greater than 3 since every voters have 50M EOS staked"
  exit
fi

touch ./config/voter_keys

> ./config/voter_keys

echo

echo "(2/3) Generating $NUM_VOTERS keys for voter accounts..."
for (( c=0; c<$NUM_VOTERS; c++ ))
do
	cleos create key --to-console >> ./config/voter_keys
done
echo "$NUM_VOTERS voter keys generated"
echo

echo "(3/3) Generating configs under /data/ dir..."
python3 generate.py

echo "All set!"
echo "Now you can exec ./boot.sh to boot the network up!"

