from django import dispatch
entry_changed = dispatch.Signal(
    providing_args=["user", "old_msgstr", "old_fuzzy", "old_obsolete", "pofile", "language_code",]
)

post_save = dispatch.Signal(
    providing_args=["language_code","request",]
)
