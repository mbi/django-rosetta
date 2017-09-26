from django import dispatch
entry_changed = dispatch.Signal(
    providing_args=["user", "old_msgstr", "old_fuzzy", "pofile", "language_code",]
)

pre_save = dispatch.Signal(
    providing_args=["language_code","request",]
)

post_save = dispatch.Signal(
    providing_args=["language_code","request",]
)
