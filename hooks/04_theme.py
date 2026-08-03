"""Stage 04 -- theme tokens.

No events of its own: theme.build_css() is called by stage 05, the only stage
that can actually publish a file. The number is kept so the pipeline reads in
order, and so there is an obvious home if theming ever needs an event.
"""
