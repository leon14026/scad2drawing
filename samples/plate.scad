// Simple prismatic part with through-holes — a fair auto-drawing target.
$fn = 48;

plate_x = 80;
plate_y = 50;
plate_z = 8;
hole_d = 6;
margin = 10;

difference() {
    cube([plate_x, plate_y, plate_z], center = true);
    for (x = [-1, 1], y = [-1, 1])
        translate([
            x * (plate_x / 2 - margin),
            y * (plate_y / 2 - margin),
            0
        ])
            cylinder(h = plate_z + 2, d = hole_d, center = true);
}
