"""Small server-owned decoration catalogue; prices are always Kopi Coins."""
SLOTS = [
    {'id': 'window', 'title': 'Window', 'x': 252, 'y': 90},
    {'id': 'door', 'title': 'Door', 'x': 20, 'y': 84},
]
ITEMS = [
    {'id': 'window_plant', 'title': 'Window plant', 'price': 8, 'art': 'plant',
     'description': 'A little greenery for your BTO.', 'slots': ['window', 'door']},
    {'id': 'kopi_cup', 'title': 'Kopi cup', 'price': 5, 'art': 'cup',
     'description': 'A kopi-break keepsake for home.', 'slots': ['window', 'door']},
    {'id': 'tile_display', 'title': 'Tile display', 'price': 12, 'art': 'tile',
     'description': 'A shophouse-inspired tile on a stand.', 'slots': ['window', 'door']},
]
BY_ITEM = {item['id']: item for item in ITEMS}
BY_SLOT = {slot['id']: slot for slot in SLOTS}
