# Capture recipes

One Python file per figure, run inside the review tree's FreeCAD (off screen) by gypsy or by hand.
A recipe opens its model from `models/`, builds the state the figure shows with CAMDriver, applies
the view rules of STYLE.md §10.3, saves the PNG to the path in `manifest.yml`, and exits. Recipes
are deterministic: same model, same FreeCAD commit, same pixels.
