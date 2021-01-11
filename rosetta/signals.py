from django import dispatch


# providing_args=["user", "old_msgstr", "old_fuzzy", "pofile", "language_code"]
entry_changed = dispatch.Signal()

# providing_args=["language_code", "request"]
post_save = dispatch.Signal()
