"""Dump the full RBAC matrix from the candidate code for pre-cutover audit."""
import inspect

from core import auth

names = [n for n in dir(auth) if not n.startswith("_")]
have_roles = getattr(auth, "ROLE_PERMISSIONS", None)

if have_roles is not None:
    for role in sorted(have_roles):
        perms = sorted(have_roles[role])
        print(f"{role}: {len(perms)} perms")
        print("  ", " ".join(perms))
else:
    print("ROLE_PERMISSIONS not found.")

for name in ("SUPPORTED_ROLES", "SUPPORT_ONLY_READ", "RolePermissionError",
             "PermissionDeniedError"):
    obj = getattr(auth, name, None)
    if obj is not None:
        if inspect.isfunction(obj) or inspect.isclass(obj):
            print(f"{name}: <{type(obj).__name__}>")
        else:
            print(f"{name}: {obj!r}")

# Print the exact source region defining the matrices so the audit is
# reproducible from the source, not just the live import.
src = inspect.getsource(auth)
print("\n=== source snippet around ROLE_PERMISSIONS ===")
for i, line in enumerate(src.splitlines(), 1):
    if "ROLE_PERMISSIONS" in line or "SUPPORT_ONLY" in line or line.strip().startswith(
        ("admin", '"admin"', "'admin'")):
        start = max(0, i - 3)
        end = min(len(src.splitlines()), i + 3)
        for j in range(start, end):
            print(f"{j+1}: {src.splitlines()[j]}")
        print("---")
        break
