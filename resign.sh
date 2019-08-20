for account in eosio.bpay eosio.msig eosio.names eosio.ram eosio.ramfee eosio.saving eosio.stake eosio.token eosio.vpay eosio.wrap
do
  cleos push action eosio updateauth '{"account": "'$account'", "permission": "active", "parent": "owner", "auth":{"threshold": 1, "keys": [], "waits": [], "accounts": [{"weight": 1, "permission": {"actor": "eosio", "permission": active}}]}}' -p ${account}@active
  cleos push action eosio updateauth '{"account": "'$account'", "permission": "owner", "parent": "",       "auth":{"threshold": 1, "keys": [], "waits": [], "accounts": [{"weight": 1, "permission": {"actor": "eosio", "permission": active}}]}}' -p ${account}@owner
  sleep 1;
done
cleos push action eosio updateauth '{"account": "eosio", "permission": "active", "parent": "owner", "auth":{"threshold": 1, "keys": [], "waits": [], "accounts": [{"weight": 1, "permission": {"actor": "eosio.prods", "permission": active}}]}}' -p eosio@active
cleos push action eosio updateauth '{"account": "eosio", "permission": "owner", "parent": "",       "auth":{"threshold": 1, "keys": [], "waits": [], "accounts": [{"weight": 1, "permission": {"actor": "eosio.prods", "permission": active}}]}}' -p eosio@owner
