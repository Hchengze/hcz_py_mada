"""Prototype seismic imaging algorithms."""

from .kirchhoff import ImagingError, kirchhoff_time_migration, kirchhoff_time_migration_array

__all__ = [
    "ImagingError",
    "kirchhoff_time_migration",
    "kirchhoff_time_migration_array",
]

