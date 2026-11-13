"""Track 4: base policy with a conservative note reader."""
from . import base
from ..notes import TrackNotes


def build(ctx, **params):
    parts = base.build(ctx, **params)
    parts.notes = TrackNotes()
    return parts
