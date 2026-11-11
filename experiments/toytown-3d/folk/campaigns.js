// Invented local toy drives for the demo: every town, place, address and date here is made up. Each drive sits on
// one of the map's three lines (red, blue, green) at a fraction of the way from that line's far station (0) to
// Toy Town (1), so a train can carry a visitor there along the painted rails. ZIP codes are matched by their first
// digit (the US ZIP regions, east to west), then by the second digit when a region has two drives.
(function () {
  const C = [
    { id: 'snowberry', town: 'Snowberry Harbor', zip0: '0', route: 'green', f: .03, deadline: 'Saturday, December 13',
      spots: [['Snowberry Harbor Public Library', '18 Lighthouse Lane', 'Mon to Sat, 9 am to 6 pm'], ['Gull & Anchor Hardware', '204 Wharf Street', 'Every day, 8 am to 7 pm'], ['Fire Station No. 2', '77 Pine Hill Road', 'Every day, all day']] },
    { id: 'pinecone', town: 'Pinecone Point', zip0: '0', route: 'green', f: .24, deadline: 'Friday, December 12',
      spots: [['Pinecone Point Town Hall', '1 Common Green', 'Mon to Fri, 8 am to 5 pm'], ['The Maple Leaf Diner', '43 Mill Street', 'Every day, 6 am to 3 pm'], ['Pinecone Credit Union', '310 Ridge Avenue', 'Mon to Sat, 9 am to 4 pm']] },
    { id: 'lantern', town: 'Lantern Falls', zip0: '1', route: 'green', f: .42, deadline: 'Sunday, December 14',
      spots: [['Lantern Falls YMCA', '55 Falls Road', 'Every day, 6 am to 9 pm'], ['Brightwater Books', '12 Canal Street', 'Tue to Sun, 10 am to 6 pm'], ['St. Nicholas Community Center', '900 Orchard Way', 'Mon to Fri, 10 am to 8 pm']] },
    { id: 'willow', town: 'Willow Bend', zip0: '2', route: 'green', f: .62, deadline: 'Saturday, December 13',
      spots: [['Willow Bend Rec Center', '480 River Road', 'Every day, 8 am to 8 pm'], ['Hollis Family Pharmacy', '27 Courthouse Square', 'Mon to Sat, 8 am to 9 pm'], ['Willow Bend Elementary (front office)', '3 Schoolhouse Lane', 'Mon to Fri, 8 am to 4 pm']] },
    { id: 'magnolia', town: 'Magnolia Crossing', zip0: '3', route: 'green', f: .84, deadline: 'Thursday, December 11',
      spots: [['Magnolia Crossing Fire Hall', '16 Depot Street', 'Every day, all day'], ['Sweet Tea Grocery', '1020 Highway 9', 'Every day, 7 am to 10 pm'], ['First Light Church Hall', '88 Chapel Road', 'Sun to Fri, 9 am to 5 pm']] },
    { id: 'maple', town: 'Maple Crossing', zip0: '4', route: 'red', f: .93, deadline: 'Saturday, December 13',
      spots: [['Maple Crossing Library', '230 Main Street', 'Mon to Sat, 10 am to 7 pm'], ['Buckeye Bike & Toy', '19 Market Street', 'Tue to Sun, 10 am to 6 pm'], ['Police Station lobby', '5 Civic Plaza', 'Every day, all day']] },
    { id: 'cedar', town: 'Cedar Hollow', zip0: '5', route: 'red', f: .78, deadline: 'Friday, December 12',
      spots: [['Cedar Hollow Community Center', '61 Lakeview Drive', 'Every day, 8 am to 8 pm'], ['Northwoods Hardware', '700 Birch Avenue', 'Mon to Sat, 7 am to 7 pm'], ['Cedar Hollow Fire Station', '14 Spruce Street', 'Every day, all day']] },
    { id: 'prairie', town: 'Prairie Bell', zip0: '6', route: 'blue', f: .9, deadline: 'Sunday, December 14',
      spots: [['Prairie Bell Grange Hall', '2 Harvest Road', 'Wed to Sun, 9 am to 5 pm'], ['Sunflower Market', '415 Wheat Street', 'Every day, 7 am to 9 pm'], ['Prairie Bell Public Library', '90 Main Street', 'Mon to Sat, 9 am to 6 pm']] },
    { id: 'copper', town: 'Copper Ridge', zip0: '7', route: 'blue', f: .62, deadline: 'Saturday, December 13',
      spots: [['Copper Ridge Civic Center', '300 Ridgeline Blvd', 'Every day, 8 am to 6 pm'], ['Lone Star Feed & Supply', '1200 Ranch Road 4', 'Mon to Sat, 7 am to 6 pm'], ['Copper Ridge Fire Station 1', '45 Mesa Street', 'Every day, all day']] },
    { id: 'redmesa', town: 'Red Mesa', zip0: '8', zip1: 'odd', route: 'blue', f: .3, deadline: 'Friday, December 12',
      spots: [['Red Mesa Visitor Center', '1 Canyon View Road', 'Every day, 9 am to 5 pm'], ['Turquoise Trading Post', '88 Old Route 66', 'Every day, 8 am to 8 pm'], ['Red Mesa Library', '210 Adobe Lane', 'Mon to Sat, 10 am to 6 pm']] },
    { id: 'mossy', town: 'Mossy Knoll', zip0: '8', zip1: 'even', route: 'red', f: .52, deadline: 'Saturday, December 13',
      spots: [['Mossy Knoll Lodge', '7 Tunnel Road', 'Every day, 8 am to 10 pm'], ['Aspen Grove Outfitters', '140 Summit Street', 'Every day, 9 am to 7 pm'], ['Mossy Knoll Town Office', '22 Granite Way', 'Mon to Fri, 8 am to 4 pm']] },
    { id: 'harbor', town: 'Harbor Pines', zip0: '9', zip1: 'even', route: 'red', f: .02, deadline: 'Sunday, December 14',
      spots: [['Harbor Pines Ferry Terminal', '1 Waterfront Way', 'Every day, 6 am to 9 pm'], ['Evergreen Toy Co-op', '58 Cedar Street', 'Tue to Sun, 10 am to 6 pm'], ['Harbor Pines Fire Station', '300 Harbor Hill Road', 'Every day, all day']] },
    { id: 'juniper', town: 'Juniper Flats', zip0: '9', zip1: 'odd', route: 'blue', f: .04, deadline: 'Saturday, December 13',
      spots: [['Juniper Flats Library', '75 Palm Avenue', 'Mon to Sat, 9 am to 7 pm'], ['Sunny Side Surf & Toy', '12 Boardwalk', 'Every day, 9 am to 8 pm'], ['Juniper Flats Community Center', '400 Desert Bloom Drive', 'Every day, 8 am to 8 pm']] },
  ];
  function find(zip) {
    zip = String(zip || '').trim();
    if (!/^\d{5}$/.test(zip)) return null;
    const pool = C.filter(c => c.zip0 === zip[0]);
    if (pool.length === 1) return pool[0];
    const odd = (+zip[1]) % 2 === 1;
    return pool.find(c => c.zip1 === (odd ? 'odd' : 'even')) || pool[+zip.slice(1) % pool.length];
  }
  // a tiny local tally of what visitors do (this browser only), so the demo can show its own funnel
  const KEY = 'tt_funnel_v1';
  function log(ev) { try { const t = JSON.parse(localStorage.getItem(KEY) || '{}'); t[ev] = (t[ev] || 0) + 1; localStorage.setItem(KEY, JSON.stringify(t)); } catch (e) {} }
  function tally() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function reset() { try { localStorage.removeItem(KEY); } catch (e) {} }
  window.TT_CAMPAIGNS = { list: C, find, log, tally, reset };
})();
