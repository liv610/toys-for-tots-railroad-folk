// Toy Town 3D, Stage A: the layout, as data. Everything the blockout draws comes from here, so the plan can be
// adjusted in one place and the later stages (detailed station, square, life) build on the same coordinates.
//
// Units are metres at human scale (the existing toy shop: 5.3 m wide, 8.7 m to its gable; eye height 1.65 m).
// Axes: x east, y up, z south (toward the visitor arriving from the map). The station faces south onto the square.
// rot is a rotation about y in degrees: 0 faces south (+z), 90 faces east (+x), -90 faces west.

export const LAYOUT = {
  station: {
    // front face of the main hall at z = -18; the hall runs north to z = -44
    front: -18, back: -44,
    hall: { x0: -8.5, x1: 8.5, wallH: 7.5, vaultR: 8.5 },          // barrel vault springing at 7.5 m: crown ~16 m
    wings: { w: 6, h: 9.5 },                                        // side wings either side of the hall
    towers: { size: 3.6, h: 13.5 },                                 // towers stop below the vault's crown, as in the illustration                                 // corner towers framing the great arch
    porch: { x0: -4.2, x1: 4.2, depth: 4.2, h: 6.2, gable: 2.8 },   // the clock porch over the visitor entrance
    steps: { n: 5, rise: 0.17, tread: 0.55 },
  },
  // platforms and tracks inside the hall: the west pair (red, blue) and the east line (green) end at buffers
  // either side of a central concourse, so no track crosses another and none reaches the square
  platforms: [
    { x0: -14.5, x1: -2.5, z: -36.2, w: 2.6 },     // west island between red and blue
    { x0: 2.5, x1: 14.5, z: -33.5, w: 3.0 },       // east platform beside green
  ],
  concourse: { x0: -3, x1: 3, z0: -40, z1: -18.5 },
  rails: {
    red:   { color: 0xc0392b, pts: [[-95, -52], [-70, -46], [-45, -40], [-26, -38.6], [-14.5, -38.6], [-3.5, -38.6]] },
    blue:  { color: 0x2f5fb3, pts: [[-95, 22], [-70, 18], [-45, 6], [-31, -6], [-25.5, -20], [-22, -31], [-17, -33.8], [-14.5, -33.8], [-3.5, -33.8]] },
    green: { color: 0x2e8b57, pts: [[95, -10], [70, -18], [48, -27], [34, -31], [22, -31], [14.5, -31], [3.5, -31]] },
  },
  square: {
    // an organic outline: cobbles from the station steps to the low wall, between the two rows of buildings
    outline: [[-10.5, -13], [10.5, -13], [11.5, -6], [12.5, 2], [12, 8.5], [6, 9.5], [-6, 9.5], [-12, 8.5], [-12.5, 1], [-11.5, -6]],
    tree: [-2.2, -1.2], marines: [[2.8, -2.4], [4.0, -2.1]],
    lamps: [[-7.5, -10], [7.5, -10], [-9.5, 4.5], [9.5, 4.5]],
    wagons: [[-6.5, 1.5, 20], [6.8, 2.6, -15]],
    benches: [[-9.5, -3, 90], [9.5, -3, -90]],
    wall: { z: 9.6, gap: [-2.2, 2.2], h: 1.0 },
  },
  // the toy shop from the existing scene (clipped out of its street), and the other buildings as blocks
  toyshop: { x: -15.2, z: 2.6, rot: 48 },
  buildings: [
    // west side, stepping back toward the station
    { name: 'Yellow house', x: -17.2, z: -5.6, rot: 78, w: 5.0, d: 5.2, h: 8.5, roofH: 4.6, wall: 0xe0b24a, roof: 0x8e3a30 },
    { name: 'Narrow pink house', x: -16.4, z: -11.4, rot: 72, w: 3.6, d: 5.0, h: 10.5, roofH: 3.0, wall: 0xe596ad, roof: 0x8e3a30 },
    { name: 'Cream house (red gable)', x: -11.6, z: -15.2, rot: 28, w: 5.4, d: 4.6, h: 7.0, roofH: 3.4, wall: 0xf0e0b6, roof: 0x8e3428 },
    // east side
    { name: 'Toy donation storefront', x: 15.6, z: 1.4, rot: -50, w: 6.6, d: 6.0, h: 7.0, roofH: 3.6, wall: 0xe8bd52, roof: 0x5a5a8e, sign: true },
    { name: 'Red house', x: 17.6, z: -7.2, rot: -78, w: 5.2, d: 5.4, h: 10.0, roofH: 4.4, wall: 0xb8382c, roof: 0x7e2a26 },
    { name: 'Pink house (purple roof)', x: 11.8, z: -14.6, rot: -30, w: 4.8, d: 4.4, h: 7.4, roofH: 2.8, wall: 0xe597ad, roof: 0x5a5a8e },
  ],
  river: { pts: [[36, -95], [32, -60], [28.5, -34], [27, -12], [26, 6], [23, 22], [16, 40], [6, 70]], w: 6.5 },
  bridge: { x: 26.4, z: 7.6, rot: 8, len: 11, w: 3.4, archR: 3.2 },          // the stone bridge, path east from the square
  trestle: { x: 28.4, z: -31.4, len: 12, w: 2.6 },                            // the red rail bridge carrying green over the river
  paths: [
    { name: 'east path to the bridge', pts: [[11.5, 6.8], [16, 7.6], [21, 7.8]], w: 3.0 },
    { name: 'south path down to the fields', pts: [[0, 10], [0.5, 16], [-3, 26], [-10, 38]], w: 3.2 },
    { name: 'west alley behind the houses', pts: [[-12, -2], [-19.5, -3], [-24, 2]], w: 1.8 },
  ],
};

// camera stops for review (and, later, the guided tour)
export const VIEWS = {
  overview: { name: '1  Elevated: how the town fits together', pos: [34, 46, 74], target: [0, 2, -12], fov: 40 },
  square:   { name: '2  Visitor in the square, looking at the station', pos: [4.2, 1.65, 8.2], target: [-0.6, 6.2, -18], fov: 62 },
  toyshop:  { name: '3  Beside the toy shop, looking across the square', pos: [-10.2, 1.65, 8.2], target: [10, 3.0, -2], fov: 64 },
  entrance: { name: '4  Approaching the station entrance', pos: [2.6, 1.65, -3.0], target: [-0.2, 5.0, -18], fov: 60 },
  rails:    { name: '5  The rails: red and blue arriving from the west', pos: [-46, 14, -8], target: [-10, 3, -34], fov: 45 },
  cutaway:  { name: '6  Cutaway: platforms inside the station', pos: [0, 62, 6], target: [0, 0, -30], fov: 45, cutaway: true },
};
