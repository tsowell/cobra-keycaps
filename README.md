(Vezi [README-ro.md](README-ro.md) pentru o traducere greșită în română.)

# Cobra keycaps

This is a custom keycap design for the Cobra computer.  The design is generated
by a hacky Python script which parses a template file from WASD Keyboards and
generates each individual keycap design based on a keycap template.

`keyboard_cobra.svg` is the resulting design.

## Components

### Keyboard template

The keyboard template, `keyboard_base.svg`, was produced from WASD Keyboards's
template file, `wasd-inkscape-104-04.20.2021.svg`.  It was produced by
following the instructions in their template to hide the "message" layout and
set the background colors for each keycap, and by creating a "Cobra" layout for
the Python script to write to.

### Keycap template

The keycap template, `template.svg`, is a jumbled mess of template objects for
the Python script to extract and use in keycap layouts.

### The Python script

Including alternate layouts I used for accent keycaps, there are 10 basic key
layouts using different combinations of objects from the keycap template.  The
`main()` function in `mkkb.py` defines the text/color contents of each key in
each layout, maps those attributes onto objects in the keycap template, and
finally copies those objects into each individual keycap in the keyboard
template.

## Usage

`python mkkb.py`

File arguments are defined at the top of the script.

## Problems

The Cobra keyboard has a different layout from WASD's normal 104-key layout,
and I failed to account for the different profiles on each row.  So the red
accent keycaps I put on the numpad make no sense at all.

Also, the apostrophe on the D key should be backslash.
