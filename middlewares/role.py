# Role checking is handled at the router level via RoleFilter (filters/role_filter.py).
# A middleware-level role check would fire before the session is injected,
# making DB lookups impossible. Use RoleFilter on routers instead.
#
# This file is intentionally minimal — kept for project structure consistency.
