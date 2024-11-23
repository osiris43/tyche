from polygon import RESTClient

# docs
# https://polygon.io/docs/options/get_v3_reference_options_contracts__options_ticker
# https://polygon-api-client.readthedocs.io/en/latest/Contracts.html

# client = RESTClient("XXXXXX") # hardcoded api_key is used
client = RESTClient()  # POLYGON_API_KEY environment variable is used

contract = client.get_options_contract("O:APGE241220C00070000")

# print raw values
print(contract)

from polygon import RESTClient

# docs
# https://polygon.io/docs/options/get_v3_snapshot_options__underlyingasset___optioncontract
# https://polygon-api-client.readthedocs.io/en/latest/Snapshot.html

# client = RESTClient("XXXXXX") # hardcoded api_key is used
client = RESTClient()  # POLYGON_API_KEY environment variable is used

snapshot = client.get_snapshot_option("GRAB", "O:GRAB241220C00005000")

# print raw values
print(snapshot)
