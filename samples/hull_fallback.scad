// Known scad123d mesh-fallback case (hull of 3+ spheres).
// Use this to see converter warnings and faceted drawing edges.
hull() {
    translate([-8, 0, 0]) sphere(r = 5);
    translate([8, 0, 0]) sphere(r = 9);
    translate([0, 16, 0]) sphere(r = 7);
}
