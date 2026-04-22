# Change DEVICE to 'A' or 'B' before running
DEVICE = 'B'

DEVICES = {
    'A': {
        'uart_id': 0,
        'tx': 0,
        'rx': 1,
        'address': 1,
    },
    'B': {
        'uart_id': 0,
        'tx': 12,
        'rx': 13,
        'address': 2,
    },
}

NETWORK  = 6
BAND     = 915000000