"""The lane part of a dealer's switching price: a level offset per delivery town.

Made by tracks/t2/towns.py from the six level 8 scans: for each first-option request the
switching ratio minus its world-and-day mean, then per delivery town the mean leftover
shrunk by n / (n + 30). The same leftover appears in every scanned world (FINDINGS.md).
"""
DELIVERY = {"espoo": -0.0716, "hameenlinna": 0.0554, "helsinki": -0.0568, "hyvinkaa": -0.1362, "joensuu": 0.0222, "jyvaskyla": 0.0125, "kajaani": 0.0824, "kemi": 0.0486, "kokkola": 0.0501, "kotka": 0.0399, "kouvola": 0.0951, "kuopio": 0.1019, "lahti": 0.0464, "lappeenranta": 0.0906, "lempaala": 0.019, "mikkeli": 0.0864, "oulu": 0.0233, "pori": 0.0944, "porvoo": 0.0058, "raisio": 0.0532, "rauma": 0.0482, "rovaniemi": 0.0895, "salo": 0.0304, "savonlinna": 0.0657, "seinajoki": 0.0374, "tampere": 0.0239, "turku": 0.0257, "vaasa": 0.0561, "vantaa": -0.1112, "ylivieska": 0.1421}
