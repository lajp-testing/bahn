"""What the competitor asks more for a car picked up at a place, and for one delivered there: the log of the markup
that a dealer accepts, against the week's level. The handbook: one part of the competitor's lane factor "is almost
the same in every world". Fitted on 71,369 quoted requests of 30 practice weeks; written by tracks/t2/places.py."""

PICKUP = {
    "espoo": 0.01, "hameenlinna": 0.003, "helsinki": -0.007, "hyvinkaa": 0.06, "joensuu": -0.054,
    "jyvaskyla": -0.036, "kajaani": -0.048, "kemi": -0.046, "kokkola": -0.082, "kotka": -0.022,
    "kouvola": -0.024, "kuopio": -0.053, "lahti": -0.025, "lappeenranta": -0.069, "lempaala": -0.033,
    "mikkeli": -0.043, "oulu": -0.022, "pori": -0.048, "porvoo": 0.012, "raisio": -0.045,
    "rauma": -0.044, "rovaniemi": -0.02, "salo": -0.044, "savonlinna": -0.065, "seinajoki": 0.009,
    "tampere": -0.031, "turku": -0.029, "vaasa": -0.063, "vantaa": 0.018, "ylivieska": -0.07,
}

DELIVERY = {
    "espoo": -0.05, "hameenlinna": 0.049, "helsinki": -0.06, "hyvinkaa": -0.055, "joensuu": 0.047,
    "jyvaskyla": 0.042, "kajaani": 0.066, "kemi": 0.144, "kokkola": 0.069, "kotka": 0.116,
    "kouvola": 0.075, "kuopio": 0.042, "lahti": 0.058, "lappeenranta": 0.083, "lempaala": 0.023,
    "mikkeli": 0.093, "oulu": 0.006, "pori": 0.082, "porvoo": -0.011, "raisio": 0.043,
    "rauma": 0.068, "rovaniemi": 0.007, "salo": 0.051, "savonlinna": 0.119, "seinajoki": 0.095,
    "tampere": 0.039, "turku": 0.026, "vaasa": 0.016, "vantaa": -0.094, "ylivieska": 0.103,
}
