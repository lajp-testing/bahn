"""The lane model: the part of a request's switching price its own features predict.

Fitted by tracks/t2/predict.py on the six level 8 scans (6,139 first-option requests,
one option per request): the target is an option's switching ratio minus its world-and-day
mean, the fit a ridge regression on standardised features (penalty 100), chosen by
leave-one-world-out R squared (0.13 out of sample, 0.20 in sample; the target's stdev is
0.21 and the predictions' 0.09). Nearly all of it is the delivery town's lane part; the
rest is the dealer, the typical fee against the list price, the list price itself, the
number of options, the lane's km and the option's kind. The mean prediction over the
scans is 0, so this is a pure leftover around the level the quoter keeps.
"""
import math

DELIVERY = {"espoo": -0.16254, "helsinki": -0.14269, "hyvinkaa": -0.22765, "jyvaskyla": -0.0597,
            "kokkola": -0.01286, "kuopio": 0.05402, "lahti": -0.0227, "lempaala": -0.0563,
            "mikkeli": 0.02604, "oulu": -0.03217, "pori": 0.03336, "porvoo": -0.08422,
            "raisio": -0.01902, "rovaniemi": 0.06264, "tampere": -0.05129, "turku": -0.04568,
            "vaasa": 0.01124, "vantaa": -0.20618, "ylivieska": 0.10709}
DEALER = {"D01": 0.02673, "D02": 0.02572, "D03": 0.00793, "D04": 0.00067,
          "D05": -0.02981, "D06": 0.00923}
OTHER_DEALER = -0.03615
KIND = {"same_day": 0.00001, "next_day": -0.0002, "within_3_days": 0.13961}
INTERCEPT = 0.32578


def leftover(request: dict, option: dict, ctx) -> float:
    """The predicted switching-ratio leftover for one option, in list prices (mean 0 over the scans)."""
    leg = request["legs"][0]
    return (INTERCEPT
            + 0.03781 * request["referenceFeeCents"] / option["listPriceCents"]
            - 0.00205 * math.log(request["referenceFeeCents"])
            - 0.01303 * len(request["options"])
            - 0.02694 * math.log(option["listPriceCents"])
            - 0.00001 * ctx.km(leg["pickup"]["placeId"], leg["delivery"]["placeId"])
            + DELIVERY.get(leg["delivery"]["placeId"], 0.0)
            + DEALER.get(request["dealerId"], OTHER_DEALER)
            + KIND.get(option["kind"], 0.0))
