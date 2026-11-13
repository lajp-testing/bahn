"""Randomised first-option prices for demand research."""
import hashlib
from ..parts import Part
from ..policies.base import build as base

class Grid(Part):
    def prices(self, request, desk):
        digest = hashlib.sha256(request['id'].encode()).digest()
        markup = 1 + (digest[0] % 21) * .05
        option = request['options'][0]
        return {option['kind']: round(option['listPriceCents'] * markup)}

def build(ctx, **params):
    parts = base(ctx, **params)
    parts.quoter = Grid()
    return parts
