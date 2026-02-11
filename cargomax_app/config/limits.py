"""
Configurable operational limits for validation.

These can be overridden per ship or class in future.
"""

from __future__ import annotations

# Minimum acceptable GM (m) - typical regulatory minimum ~0.15
MIN_GM_M = 0.15

# Livestock: stricter GM (AMSA MO43 / IMO livestock guidelines)
MIN_GM_LIVESTOCK_M = 0.20

# Livestock: max roll period (s) for animal welfare
MAX_ROLL_PERIOD_S = 15.0

# Livestock: min freeboard (m) to avoid deck immersion
MIN_FREEBORD_M = 0.3

# Livestock: default mass per head (t) for stability – cattle ~0.5, sheep ~0.08
MASS_PER_HEAD_T = 0.5

# Maximum acceptable trim as fraction of LOA (e.g. 0.02 = 2%)
MAX_TRIM_FRACTION = 0.02

# Maximum draft as fraction of design draft (1.0 = at design)
MAX_DRAFT_FRACTION = 1.05

# Max SWBM as fraction of design (placeholder - use ship-specific if available)
MAX_SWBM_FRACTION = 1.0

# Phase 3: Propeller immersion minimum (%) – typically 60–80% required
MIN_PROP_IMMERSION_PCT = 60.0

# Phase 3: Minimum visibility (m) – bridge to bow waterline
MIN_VISIBILITY_M = 1.0

# Phase 3: Minimum air draft (m) – clearance above waterline
MIN_AIR_DRAFT_M = 5.0

# Free surface correction factor for slack tanks (reduces effective GM)
# I_small_square / disp for typical tank; simplified multiplier
FREE_SURFACE_FACTOR = 0.5  # conservative reduction per slack tank

# Floating-point tolerance
EPS = 1e-9
