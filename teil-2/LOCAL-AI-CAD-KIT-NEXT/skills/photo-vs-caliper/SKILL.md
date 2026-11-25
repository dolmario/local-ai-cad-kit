---
name: photo-vs-caliper
description: Rules for measuring a part from a photo on the printed ArUco markerboard and for deciding when the caliper must take over. Use whenever a photo is the source of a dimension, before any dimension from a photo is used in CAD.
---

# Photo measurement vs caliper

- The photo tool (`photo-measure`) straightens the photo with the board markers. On the plate plane the typical error is about 0.1 to 0.2 mm in our tests.
- **Height matters.** A part that stands h mm above the plate looks larger from above by about C / (C - h), with C = camera height (about 300 to 350 mm for a phone held above the board). A 2 mm height error is about 0.2 mm on a 30 mm feature. Ask for the part height (caliper) whenever the feature is not flat on the plate.
- Edge-based tools widen thin shapes by about 0.2 to 0.3 mm per side (blur, shadows). Treat photo widths as estimates and ask for a caliper value.
- Always ask where exactly the user measured ("shaft" and "shoulder next to the head" are different places).
- Always show the control image (`kontrollbild`) path and ask the user to look at it before you use the numbers.
- If the tool returns an error, say what it says and what to change in the photo (flat board, even light, all markers visible, straight from above). Never fill in a value.
- The user can run `pruefen/platte_pruefen.py <photo>` to see how accurate the board and photo are.

Use the kit path from LOCAL_AI_CAD_KIT or workspace kit-path.txt. Reuse caliper values and control-image acceptance already supplied in this conversation; do not ask the same question again. Photo estimates and real fit remain distinct.
