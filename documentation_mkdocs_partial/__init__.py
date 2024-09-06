import re

PACKAGE_NAME_RESTRICTED_CHARS = re.compile(r"[^A-Za-z0-9+_-]")
MODULE_NAME_RESTRICTED_CHARS = re.compile(r"[^a-z0-9+_]")
PACKAGE_NAME = re.compile(r"^[A-Za-z0-9+_-]+$")
