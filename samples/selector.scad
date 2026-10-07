// Component selector, matching the Onshape SOP pattern.
//   scad2drawing convert samples/selector.scad -D part=frame
//   scad2drawing convert samples/selector.scad -D part=shaft
//   scad2drawing convert samples/selector.scad -D part=assembly

part = "assembly";

module frame() {
    difference() {
        cube([60, 20, 12], center = true);
        rotate([0, 90, 0])
            cylinder(h = 70, d = 8, center = true, $fn = 48);
    }
}

module shaft() {
    rotate([0, 90, 0])
        cylinder(h = 80, d = 7.8, center = true, $fn = 48);
}

module assembly() {
    frame();
    shaft();
}

if (part == "assembly") assembly();
else if (part == "frame") frame();
else if (part == "shaft") shaft();
else assert(false, str("unknown part=", part));
