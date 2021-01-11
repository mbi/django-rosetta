from django import dispatch

entry_changed = dispatch.Signal()
post_save = dispatch.Signal()
