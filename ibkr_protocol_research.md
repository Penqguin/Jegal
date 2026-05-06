# IBKR TWS API Protocol Notes

## Protocol Overview
The IBKR TWS API uses a proprietary, binary-safe, length-prefixed TCP protocol. Messages are generally structured as:
`[Length-Prefix][Payload]`

The length prefix is 4 bytes (big-endian).

## Handshake
1. Client connects via TCP.
2. Client sends the "API\0" prefix.
3. Client sends the initial "v100" handshake string.
4. Gateway responds with API version and server time.

## Message Format
Messages are strings of field values separated by null bytes (`\0`).
Example: `REQUEST_TYPE\0FIELD1\0FIELD2\0...`

## Key Requests
- `reqAccountUpdates(subscribe, accountCode)`
- `placeOrder(orderId, contract, order)`
