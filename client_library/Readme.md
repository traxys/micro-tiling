# Micro Tiling Client 

This client library is calling the REST API assuring that a job finishes

## Dependencies

- progressbar `pip install progressbar2` (optional, for command line use)
- requests `pip install requests`

## Usage

### As a client

`client.py <MICRO_TILING API ADDRESS> <ENSICOIN_ADRESS>`

### As a library

There are two ways to use the client :
- `generate_state(host, ensicoin_address)` which returns a mosaic as a svg file
- `manage_state(host, ensicoin_adrress, result: list)` being an iterator returning the state periodicaly, and writing the mosaic into `result`
