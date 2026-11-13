"""Experimental quoter with the starter's other parts."""
from ..policies.base import build as base
from ..quote import LearningQuoter


def build(ctx, cost_factor=1.0, **params):
    parts = base(ctx, **params)
    parts.quoter = LearningQuoter(cost_factor=cost_factor)
    return parts
