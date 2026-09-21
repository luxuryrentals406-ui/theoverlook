#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Overlook at Flathead Lake — static site generator.

    python3 tools/build.py

Writes plain .html to the project root. The output needs no build step to
host; this exists only so the header, footer and meta stay identical.

COPY RULES enforced by tools/lint.py (run after building):
  - "Begin Your Story" / "Your Story Awaits" never appear
  - "dream" appears at most once site-wide
  - the estate sleeps 28; sleeping capacity is a wedding/estate fact only and
    never appears on retreats.html
  - wedding vocabulary never appears on retreats.html, and vice versa
"""
import os, re, sys, json, datetime
import html as ihtml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shell import (SITE, BIZ, NAV, IMG, THMB, img, eyebrow, btn, tlink,
                   plist, ilist, quote, faq, hero, band, split, vmap, stickybar, marquee,
                   getting_here, switcher, rail, mosaic, honeybook_form, spec, experiences,
                   driftwood,
                   head, header, footer)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YEAR = datetime.date.today().year

# ---------------------------------------------------------------- reviews
R_OLIVIA = ("We absolutely loved our wedding at The Overlook at Flathead Lake! "
            "The venue is incredibly beautiful, and having the opportunity to stay "
            "onsite made the entire weekend feel so special. Our guests could not "
            "stop talking about how gorgeous the property was&hellip; kind, "
            "responsive, and made everything feel so easy from start to finish.",
            "Olivia Pechous", "Married at The Overlook")

R_KATIE = ("&hellip;you can tell they care so much "
           "about making their amazing venue the best it can be&hellip; I know this venue "
           "is going to take off and become one of the top venues in the Valley. The view "
           "is so beautiful and the grounds are well kept!",
           "Katie Jimenez", "Wedding Planner, Big Day Celebrations")

R_ERICA = ("The Overlook team was absolutely amazing to work with! Their attention to "
           "detail truly did not go unnoticed. From start to finish, they made sure "
           "everything ran smoothly and were incredibly responsive&hellip; The venue itself "
           "is beautiful and exceptionally well-kept&hellip; With convenient on-site "
           "accommodations, easy access to town just a short drive or walk away, and lake "
           "and mountain views, the location truly cannot be beat.",
           "Erica Christian", "Hosted an event at The Overlook")

R_KELSEY = ("We spent three nights at The Overlook at Flathead Lake, and it was easily one "
            "of the most peaceful places we&rsquo;ve ever stayed&hellip; Eric and Claudia "
            "were absolutely amazing. They were so welcoming, attentive, and quick to "
            "respond anytime we needed anything. You can tell they truly care about the "
            "experience their guests have.",
            "Kelsey Folcarelli", "Stayed three nights onsite")

R_KELSEY_RETREAT = ("It was easily one of the most peaceful places we&rsquo;ve ever "
                    "stayed&hellip; The creativity behind the treehouses is what makes "
                    "this place so special &mdash; unique, beautifully done, and "
                    "completely different from a typical vacation rental. We were already "
                    "talking about bringing a Fortitude retreat group out there because it "
                    "would be such an incredible setting for it.",
                    "Kelsey Folcarelli", "Stayed three nights onsite")

# Greg's review again, excerpted for the corporate reader: the same verbatim
# words, but the part about bringing a group rather than the part about a stay.
R_GREG_RETREAT = ("The views are unreal&hellip; it&rsquo;s clear how much care went in to "
                  "every detail. Eric, Claudia and the management were extremely helpful, "
                  "and on top of everything you could need. I&rsquo;m planning to run a "
                  "retreat group out here next year and use the venue as well.",
                  "Greg Wilson", "Onsite Guest")

R_JAMES = ("This property is absolutely stunning. It would be a privilege to get married "
           "or have an event here.",
           "James Celli", "Google review")

R_GREG = ("This is officially the best spot in Montana. The views are unreal&hellip; it&rsquo;s "
          "clear how much care went into every detail.",
          "Greg Wilson", "Onsite Guest")


# FAQ copy lives at module level: the page renders it and schema() turns the
# same list into FAQPage structured data, so the two can never drift.
FAQ_WEDDINGS = [
    ("Where is the venue located?",
     "<p>The estate sits above Flathead Lake in Lakeside, Montana, 35 minutes from "
     "Glacier Park International Airport (FCA) and about 45 minutes from Glacier "
     "National Park and Whitefish Mountain Resort.</p>"),
    ("How many guests can it hold?",
     "<p>Up to 200 guests for the celebration itself. Separately, up to 28 people "
     "sleep on the property across the five accommodations &mdash; usually the couple "
     "and their closest family and wedding party.</p>"),
    ("What does a booking include?",
     "<p>Pricing depends on the dates and the shape of the weekend, so we quote it "
     "directly rather than publish a number. A booking covers exclusive use of the "
     "grounds, the "
     "pavilion and tent, the built-in bar, onsite tables and chairs, four head "
     "tables, "
     "the fire pit, parking for 75 cars and your onsite venue coordinator. "
     "<a href='#included'>The full list is above.</a></p>"),
    ("Is lodging included or separate?",
     "<p>Lodging is booked separately from the venue fee, which keeps the starting "
     "price honest for couples whose guests are staying in Whitefish or Kalispell. "
     "<a href='estate.html'>See the five accommodations.</a></p>"),
    ("What is the payment schedule?",
     "<p>50% at signing, 25% at 120 days out, and the final 25% at 60 days out. A "
     "refundable security deposit is due 30 days before the event. Contracts are "
     "written to a 200-guest maximum with an 11:00 p.m. event end.</p>"),
    ("Do you have a preferred vendor list?",
     "<p>Yes. We keep working relationships with Flathead Valley planners, caterers, "
     "florists and photographers who know the property, and several extend a partner "
     "discount to our couples. You are not required to book from it.</p>"),
]

FAQ_RETREATS = [
    ("Is the entire property private during our retreat?",
     "<p>Yes. A full-estate buyout means no other guests and no other events on the "
     "property for the length of your booking.</p>"),
    ("How do the five accommodations get assigned?",
     "<p>We map the five accommodations to your roster once we know who is coming "
     "and how they travel. Tell us your headcount and we will come back with a "
     "specific plan for the property.</p>"),
    ("Can we host a full-day working session?",
     "<p>Yes. The pavilion and grounds are designed to flex between general session, "
     "breakouts, and dining or social use across the same day without a reset that "
     "pushes your group outside.</p>"),
    ("Do you offer team experiences or local activities?",
     "<p>Helicopter arrivals and private lake flights are available through WestSlope "
     "Helicopters, along with access to Flathead Lake recreation and Glacier National "
     "Park.</p>"),
    ("How far is the nearest airport?",
     "<p>Glacier Park International Airport (FCA) is 35 minutes away, with direct "
     "service from a number of major cities.</p>"),
    ("How do we get a custom proposal?",
     "<p>Send your dates, your group size and what the gathering needs to accomplish. "
     "You will get a tailored proposal rather than a rate sheet.</p>"),
]


# The Driftwood, the add-on estate at Woods Bay. Photographs are the owner's
# own, pulled from flatheadlakewaterfront.com — 1200px is the largest that
# site holds, so they are used at native size and never enlarged.
DRIFTWOOD_SHOTS = [
    ("exterior-dusk", "The house from the water at dusk", "water"),
    ("exterior-lawn", "The lake side from the lawn", "water"),
    ("arrival", "The approach and the motor court", "water"),
    ("aerial-cove", "The point and the cove from the air", "water"),
    ("dock-slips", "The dock and private boat slips", "water"),
    ("dock-out", "Out along the dock", "water"),
    ("boat", "The boat tied up at sunset", "water"),
    ("sunset", "Sunset from the shoreline", "water"),
    ("great-room", "The great room, opening to the lake", "living"),
    ("great-room-vault", "The vaulted great room", "living"),
    ("lounge-fire", "The second living room and fireplace", "living"),
    ("kitchen", "The kitchen and the long island", "living"),
    ("kitchen-bar", "The second kitchen and bar seating", "living"),
    ("dining-bar", "Dining and bar beside the fireplace", "living"),
    ("dining-long", "The long dining table", "living"),
    ("lounge-curved", "The curved lounge", "living"),
    ("bed-primary", "The primary bedroom under the beams", "rooms"),
    ("bed-fireplace", "A bedroom with its own fireplace", "rooms"),
    ("bed-chandelier", "An upstairs sitting room off the landing", "living"),
    ("bed-lake", "A bedroom opening onto the lake", "rooms"),
    ("bed-vault", "A bedroom under the vaulted ceiling", "rooms"),
    ("bed-twin", "A twin room", "rooms"),
    ("bed-blue", "A bedroom with a reading chair", "rooms"),
    ("bed-sliders", "A bedroom with doors to the deck", "rooms"),
    ("bath-copper", "The copper tub and the lake beyond", "rooms"),
    ("bath-lake", "A bath looking down the lake", "rooms"),
    ("deck-table", "The covered deck and dining table", "deck"),
    ("deck-loungers", "Loungers on the deck at dusk", "deck"),
    ("deck-stone", "Outdoor dining under the overhang", "deck"),
    ("deck-lakeview", "The table facing straight down the lake", "deck"),
    ("hottub", "The hot tub off the lower level", "deck"),
]


# ================================================================== HOME
def page_home():
    facts = [("15", "Private acres"), ("200", "Event guests"),
             ("28", "Sleep onsite"), ("One", "Group at a time")]
    parts = []
    for n, l in facts:
        attr = ' data-count="%s"' % n if n.isdigit() else ""
        parts.append('<div class="facts__item"><span class="facts__n"%s>%s</span>'
                     '<span class="facts__l">%s</span></div>' % (attr, n, l))
    fhtml = "".join(parts)

    cards = [
        ("weddings.html", "wedding-aerial-tent.jpg",
         "The tent and ceremony lawn from the air at golden hour", "Weddings",
         "The whole estate for a multi-day celebration &mdash; ceremony, cocktails and "
         "reception each in their own part of the property.",
         "See the wedding weekend"),
        ("retreats.html", "lounge-interior.jpg",
         "The pavilion lounge set for a small group", "Corporate &amp; Private Retreats",
         "A full-property buyout for leadership teams, boards and company gatherings. "
         "Everyone works, eats and sleeps in the same place.",
         "Plan a retreat"),
        ("estate.html", "swan-exterior.jpg",
         "The Swan, the four-bedroom main house", "The Estate",
         "Five accommodations, a heated pool, sauna, fitness room and trails across "
         "fifteen acres. This is what your group has to itself.",
         "Tour the property"),
    ]
    chtml = "".join(f"""<a class="card" href="{h}">
        <div class="card__img">{img(i, a)}</div>
        <h3>{t}</h3><p>{d}</p>
        <span class="tlink">{cta} <span>&rarr;</span></span>
      </a>""" for h, i, a, t, d, cta in cards)

    return f"""
{hero("hero-pavilion-lake.jpg",
      "The reception pavilion at dusk with Flathead Lake beyond",
      "Lakeside, Montana",
      "Fifteen private acres<br>above Flathead Lake",
      "A private Montana estate on Flathead Lake, booked exclusively for your group "
      "&mdash; for weddings and private gatherings.",
      btn("weddings.html", "Plan Your Wedding", "btn btn--light btn--lg")
      + btn("retreats.html", "Explore Corporate Retreats", "btn btn--outline-light btn--lg"),
      slides=[("venue-overview.jpg", "The ceremony lawn and tent across the grounds"),
              ("tent-front.jpg", "The reception tent from the lawn"),
              ("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate")])}

  <section class="facts">
    <div class="facts__grid rv rv--stagger">{fhtml}</div>
  </section>

  {marquee(["Lakeside, Montana", "Flathead Lake", "Fifteen private acres",
            "One group at a time", "Glacier Country", "Weddings &amp; Retreats"])}

  <section class="sect">
    <div class="wrap">
      <div class="center rv" style="margin-bottom:clamp(3rem,6vw,4.5rem)">
        {eyebrow("Two ways to use the estate")}
        <h2>One property. No overlap.</h2>
        <p class="lede measure" style="margin-top:1.4rem">Because only one group is on
          the property at a time, the estate becomes whatever that group needs it to be
          &mdash; a wedding weekend in July, a leadership offsite in October.</p>
      </div>
      <div class="cards rv rv--stagger">{chtml}</div>
    </div>
  </section>

  <section class="sect sect--tight">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2rem,4vw,3rem);max-width:46ch">
        {eyebrow("The grounds")}
        <h2>What is out there between the events</h2>
      </div>
      {mosaic([("pool-wide.jpg", "The heated pool above the lake", "Heated pool"),
               ("hottub-views.jpg", "The hot tub looking over the valley", "Hot tub"),
               ("barrel-sauna.jpg", "The cedar barrel sauna", "Barrel sauna"),
               ("pool-house-pingpong.jpg", "The games room in the pool house", "Games room"),
               ("lakeside-putting-green.jpg", "The putting green on the lawn", "Putting green"),
               ("pool-house-firepit.jpg", "The pool house and fire pit at dusk", "Pool house")])}
    </div>
  </section>

  <section class="sect sect--forest">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.8rem)">
        {eyebrow("From our guests")}
        <h2 style="max-width:16ch">What people say once they have been here</h2>
      </div>
      <div class="quotes quotes--3">
        {quote(*R_OLIVIA)}
        {quote(*R_KATIE)}
        {quote(*R_KELSEY)}
      </div>
    </div>
  </section>

  {band("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate",
        "Tell us your dates",
        "We take a limited number of weekends each season. Send us the one you have in "
        "mind and we will tell you honestly whether it is open.",
        btn("contact.html", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== WEDDINGS
def page_weddings():
    included = [
        ("The spaces", [
            "<b>3,200 sq ft</b> reception pavilion with panoramic lake views",
            "<b>40 &times; 80 ft</b> tent &mdash; clear-top or white-top, full sides",
            "Separate ceremony, cocktail and reception areas",
            "Fire pit for evening gatherings",
        ]),
        ("Capacity", [
            "<b>200</b> guests for the celebration",
            "Sleeps <b>28</b> across five accommodations",
            "<b>One</b> group on the property at a time",
        ]),
        ("Power &amp; access", [
            "<b>200 AMP</b> electrical service, permanently installed",
            "On-site water",
            "Vendor load-in within <b>50 ft</b> of the venue",
            "Parking for <b>75 cars</b> on site",
            "Starlink at the venue and in all five houses",
        ]),
        ("Already on site", [
            "Built-in bar",
            "Tables and chairs available on site",
            "<b>Four</b> head tables",
            "Dedicated onsite venue coordinator",
            "Preferred vendor partnerships, with partner discounts",
        ]),
        ("The setting", [
            "<b>15</b> private acres above Flathead Lake",
            "Estate grounds with walking trails",
            "Heated pool, hot tub, barrel sauna and putting green",
        ]),
        ("Getting here", [
            "<b>35 min</b> from Glacier Park International Airport (FCA)",
            "<b>45 min</b> from Glacier National Park",
            "<b>45 min</b> from Whitefish Mountain Resort",
        ]),
    ]

    rows = [
        ("Reception structure", "Quoted, delivered and struck around your dates.",
         "A 40&times;80 ft tent and a 3,200 sq ft pavilion, already standing."),
        ("Power &amp; utilities", "Brought in for the weekend.",
         "200 AMP service and on-site water, permanently installed."),
        ("Bar", "Built or rented, then staffed and stocked.",
         "Built-in bar, in place and ready to run."),
        ("Tables &amp; chairs", "Ordered, delivered and collected.",
         "On property, with setup handled by the venue team."),
        ("Head tables", "Part of the same rental order.",
         "Four head tables included."),
        ("Guest parking", "Arranged on site, or a shuttle from town.",
         "Parking for 75 cars on site."),
        ("Vendor access", "Depends on where a truck can reach.",
         "Load-in within 50 feet of the venue."),
        ("Setup", "Planned and built for the day, then taken down.",
         "Permanent, so the planning is about the wedding."),
        ("Where guests stay", "In town, travelling in each morning.",
         "Up to 28 people sleep on the property and walk to breakfast."),
    ]
    trows = "".join(
        f'<tr><th scope="row">{r}</th>'
        f'<td data-label="Arranged for the day">{a}</td>'
        f'<td class="col-ours" data-label="The Overlook">{b}</td></tr>'
        for r, a, b in rows)

    spots = [
        (15, 54, "Arrival",
         "They come down the drive",
         "Guests park on the property &mdash; 75 cars, no shuttle contract, no field. "
         "The approach is the first thing they see, and it is already the lake.",
         "venue-overview.jpg", "The estate grounds and tent from the lawn"),
        (52, 17, "Ceremony",
         "The lawn faces west",
         "Chairs set on the grass above the water, with the tree line on both sides. "
         "Late afternoon puts the sun behind the officiant, not in your guests&rsquo; eyes.",
         "ceremony-aisle-view.jpg", "The aisle looking toward the water"),
        (55, 39, "The walk down",
         "Stone steps, not a shuttle",
         "Ceremony and reception are a short walk apart on the same hillside. Nobody "
         "gets in a car, and the gap between the two is about the length of a drink.",
         "ceremony-tent-wide.jpg", "Ceremony seating with the tent below"),
        (84, 40, "Cocktails",
         "The grounds hold the hour",
         "The built-in bar runs while the tent is turned over. Guests spread onto the "
         "gravel and lawn instead of queuing in a corridor.",
         "bar-cheers-setup.jpg", "The built-in bar set for service"),
        (52, 68, "Reception",
         "Dinner under the tent",
         "Forty by eighty feet, clear-top or white-top with full sides. Round tables, "
         "four head tables and chairs, set before you arrive.",
         "reception-tent-full.jpg", "The reception tent set for dinner"),
    ]

    faqs = FAQ_WEDDINGS

    return f"""
{hero("ceremony-tent-wide.jpg",
      "Ceremony seating on the lawn with the tent and lake behind",
      "Weddings",
      "A weekend, not an afternoon",
      "The entire fifteen-acre estate for a multi-day wedding on Flathead Lake &mdash; "
      "yours from the rehearsal to the last morning.",
      btn("contact.html", "Check Your Date", "btn btn--light btn--lg")
      + btn("#included", "What&rsquo;s Included", "btn btn--outline-light btn--lg"),
      slides=[("ceremony-aisle-view.jpg", "The aisle looking toward the ceremony site"),
              ("venue-wide.jpg", "The estate grounds from across the lawn")],
      )}

  <section class="sect">
    <div class="wrap">
      {split(img("wedding-couple-arch.jpg", "A couple beneath the ceremony arch", "", ) ,
        f'''{eyebrow("Your wedding weekend")}
        <h2>The property empties out for you</h2>
        <p class="lede" style="margin:1.4rem 0">For the length of your booking the
          estate is closed to everyone but your people &mdash; one wedding on the
          property, and no one crossing the lawn who was not invited.</p>
        <p>That changes the shape of the day. Your ceremony happens on the lawn above
          the water. Cocktail hour moves to the grounds. Dinner and dancing take the
          pavilion and tent. Guests travel through the evening instead of sitting in one
          room watching it get flipped around them.</p>
        <p>The end time is whatever your contract says it is, agreed with you when you
          book rather than handed to you on the day.</p>''',
        wide=True)}
    </div>
  </section>

  <section class="sect sect--paper2" style="padding-block:clamp(3.5rem,8vw,6rem)">
    <div class="wrap">
      {vmap("wedding-aerial-tent.jpg",
            "Overhead view of the ceremony lawn and reception tent",
            "How the evening moves",
            "Five acres of it, in order",
            "The evening moves through the property rather than staying in one room. "
            "Select a marker to see where each part of it happens.",
            spots)}
    </div>
  </section>

  <section class="sect sect--paper2" id="included">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:52ch">
        {eyebrow("What&rsquo;s included")}
        <h2>Already standing when you arrive</h2>
        <p class="lede" style="margin-top:1.4rem">Nothing on this list is rented in for
          the weekend, quoted separately or struck on Sunday. It is the property.</p>
      </div>
      {spec(included)}
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:58ch">
        {eyebrow("Why The Overlook")}
        <h2>What is already here</h2>
        <p class="lede" style="margin-top:1.4rem">Most of a wedding is infrastructure. At
          an open site it arrives for the weekend and leaves again; here it is permanent.
          The same wedding, line by line.</p>
      </div>
      <div class="tbl-scroll rv">
        <table class="tbl">
          <thead><tr><th scope="col">&nbsp;</th><th scope="col">Arranged for the day</th>
            <th scope="col" class="col-ours">The Overlook</th></tr></thead>
          <tbody>{trows}</tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="sect sect--paper2">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:50ch">
        {eyebrow("Packages")}
        <h2>Two ways to book the weekend</h2>
      </div>
      <div class="pkg">
        <div class="pkg__card rv">
          <h3>The Overlook Wedding</h3>
          <p style="color:var(--ink-soft);margin-bottom:1.6rem">Exclusive use of the
            estate for your celebration, with the venue infrastructure in place.</p>
          {plist(["Full-property exclusivity for your booking",
                  "Pavilion, tent and built-in bar",
                  "Ceremony, cocktail and reception areas",
                  "Onsite venue coordinator",
                  "Parking for 75 cars",
                  "Lodging booked separately"])}
          {btn("contact.html?type=wedding", "Check Your Date", "btn btn--ghost")}
        </div>
        <div class="pkg__card pkg__card--feature rv">
          {eyebrow("Signature")}
          <h3>The Ultimate Flathead Lake Wedding Weekend</h3>
          <p class="pkg__price"><small>Five nights, two estates &middot; starting at</small>$100,000</p>
          <p style="color:#CFCabd;margin-bottom:1.6rem">Two estates, one group, five
            nights. The wedding itself at The Overlook, and
            <b style="font-weight:400;color:#fff">The Driftwood</b> waiting on the water
            at Woods Bay when the day is done.</p>
          {plist(["The Overlook &mdash; fifteen acres, pavilion and tent, yours alone",
                  "The Driftwood &mdash; 14,000 sq ft on the lake, private cove and boat slips",
                  "Fifty-four sleeping across the two",
                  "Helicopter transfer between them, through WestSlope",
                  "Planning support from the first call to the send-off"])}
          {btn("contact.html?type=wedding", "Request the Details", "btn btn--light")}
        </div>
      </div>
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      {split(img("swan-exterior.jpg", "The Swan main house at dusk"),
        f'''{eyebrow("Onsite lodging")}
        <h2>Nobody drives home</h2>
        <p class="lede" style="margin:1.4rem 0">Five accommodations sit on the same
          fifteen acres as the ceremony lawn &mdash; a four-bedroom main house, an
          cabin, two tiny homes and two treehouses. Twenty-eight people wake up where
          the night ended.</p>
        <p>Getting ready happens on site. So does the morning after. Lodging is quoted
          separately from the venue fee.</p>
        <div style="margin-top:2rem">{tlink("estate.html", "See all five")}</div>''',
        flip=True)}
    </div>
  </section>

  <section class="sect sect--forest">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.8rem);max-width:20ch">
        {eyebrow("Reviews")}
        <h2>In their words</h2>
      </div>
      <div class="quotes quotes--3">
        {quote(*R_OLIVIA)}{quote(*R_ERICA)}{quote(*R_KATIE)}
        {quote(*R_KELSEY)}{quote(*R_GREG)}{quote(*R_JAMES)}
      </div>
    </div>
  </section>

  {driftwood(DRIFTWOOD_SHOTS, "wedding")}

  {rail("The details", "Photographs from weddings here",
        "Drag the rail, or use the arrows. Every one of these was taken on the property.",
        [("ceremony-setup.jpg", "Chairs set on the ceremony lawn before guests arrive",
          "Chairs set before anyone arrives"),
         ("ceremony-forest.jpg", "The ceremony site among the trees",
          "The ceremony site, in the trees"),
         ("floral-arrangement-closeup.jpg", "A floral arrangement in close detail",
          "Florals, close up"),
         ("table-setting-florals.jpg", "A place setting with florals on the table",
          "A place setting"),
         ("grazing-table-spread.jpg", "A grazing table laid out for guests",
          "The grazing table"),
         ("cake-florals.jpg", "The cake dressed with florals",
          "Cake and florals"),
         ("bar-cheers-setup.jpg", "Guests raising glasses at the bar",
          "The bar, mid-toast"),
         ("food-truck-catering.jpg", "A food truck catering on the property",
          "A food truck on the lawn"),
         ("reception-long-table.jpg", "The long reception table under the tent",
          "One long table under the tent"),
         ("evening-dinner-candlelight.jpg", "Dinner by candlelight after dark",
          "Dinner, after dark"),
         ("ceremony-vertical.jpg", "The ceremony from the back of the aisle",
          "From the back of the aisle"),
         ("wedding-bw-stairs.jpg", "A couple on the stairs, in black and white",
          "On the stairs")])}

  <section class="sect">
    <div class="wrap wrap--narrow">
      <div class="rv" style="margin-bottom:2.5rem">
        {eyebrow("Questions")}
        <h2>Before you inquire</h2>
      </div>
      <div class="rv">{faq(faqs)}</div>
    </div>
  </section>

  {band("reception-mountain-view.jpg", "Reception tables set against the mountains",
        "Start your inquiry",
        "We hold a limited number of weddings each season, and every inquiry is "
        "answered personally.",
        btn("contact.html?type=wedding", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== RETREATS
def page_retreats():
    why = [
        ("Total exclusivity",
         "The entire fifteen-acre estate is booked for your group alone &mdash; the "
         "pavilion, all five houses, the pool, the sauna, the trails and the fire pit. "
         "For the length of your booking it belongs to you."),
        ("Everyone stays where you meet",
         "Your team works, eats and stays in the same place, so the conversation does "
         "not end when the session does &mdash; it carries from the pavilion to the fire "
         "pit to the kitchen island, without anyone getting in a car."),
        ("A destination, not a conference room",
         "Flathead Lake is out the window. Glacier National Park and Whitefish Mountain "
         "Resort are both about 45 minutes away. For a distributed team, that is a "
         "reason to actually get on the plane."),
        ("Built to function as a venue",
         "This is not a large rental that has to be built out for the week. The "
         "gathering space, the power, the connectivity and the grounds are permanent "
         "infrastructure."),
    ]
    whyhtml = "".join(
        f'<div class="rv"><h3>{t}</h3><p style="color:var(--ink-soft);margin-top:.9rem">{d}</p></div>'
        for t, d in why)

    space = [
        ("The Pavilion", "hero-pavilion-lake.jpg", "The pavilion looking out over Flathead Lake",
         "3,200 sq ft with panoramic lake views and dimmable lighting, adaptable from a "
         "full-group general session to a seated dinner. The tent runs clear-top or "
         "fully enclosed white-top with sides, which makes shoulder-season use viable."),
        ("The Main House &mdash; The Swan", "swan-game-room.jpg", "The game room in the Swan",
         "Three levels with a gourmet kitchen, a full bar, a game room and lake-view "
         "balconies &mdash; where breakout groups end up without being told to."),
        ("The Grounds", "pool-wide.jpg", "The heated pool and cabana above the lake",
         "Heated pool and cabana, hot tub, barrel sauna, fitness room, fire pit, putting "
         "green, lawn games and walking trails for the hours between sessions."),
        ("Connectivity", "swan-kitchen-new.jpg", "The kitchen in the Swan",
         "Starlink is installed in all five houses and at the venue itself, so a "
         "remote-first team is not hunting for signal between calls."),
    ]
    spacehtml = ""
    for i, (t, im, alt, d) in enumerate(space):
        spacehtml += f"""<div style="margin-bottom:clamp(3rem,7vw,5.5rem)">{split(
            img(im, alt, "", ),
            f'<h3>{t}</h3><p style="color:var(--ink-soft);margin-top:1.1rem;font-size:1.05rem;line-height:1.7">{d}</p>',
            flip=bool(i % 2))}</div>"""

    formats = [
        ("Leadership / Executive Retreat", "Multi-night &middot; full estate",
         "The whole group stays on property. This is the best fit for the estate and "
         "the most common booking we take."),
        ("Board or Strategy Retreat", "Two to three nights &middot; full estate",
         "Built around privacy and focus, with the pavilion held for working sessions "
         "and the houses absorbing everything else."),
        ("Company Gathering or Kickoff", "Up to 200 guests &middot; single event day",
         "The pavilion and grounds scale to a full company day, with your core team on "
         "site and additional attendees housed in Whitefish or Kalispell."),
    ]
    fhtml = "".join(f"""<div class="pkg__card rv">
        {eyebrow(sub)}<h3>{t}</h3>
        <p style="color:var(--ink-soft);margin-top:1rem">{d}</p>
      </div>""" for t, sub, d in formats)

    who = [
        "Leadership teams and founders at remote-first or hybrid companies",
        "Private equity, venture capital and wealth management firms hosting partner or LP retreats",
        "Sales organisations running kickoffs or President&rsquo;s Club incentive trips",
        "Professional-services and agency leadership teams",
        "Any team combining real strategic work with an actual change of scenery",
    ]

    faqs = FAQ_RETREATS

    return f"""
{hero("venue-overview.jpg",
      "Aerial view of the estate, pavilion and grounds above Flathead Lake",
      "Corporate &amp; Private Retreats",
      "A private Montana estate<br>for your leadership team",
      "A full-property buyout above Flathead Lake &mdash; the whole estate held for "
      "one group, with room to work and room to stop working.",
      btn("contact.html?type=corporate", "Inquire About a Retreat", "btn btn--light btn--lg"),
      slides=[("pool-wide.jpg", "The heated pool and terrace on the upper lawn"),
              ("swan-exterior.jpg", "The Swan, the four-bedroom main house")])}

  <section class="sect">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.8rem,6vw,4.5rem);max-width:54ch">
        {eyebrow("Why teams choose the Overlook")}
        <h2>Privacy first, everything else after</h2>
      </div>
      <div class="cards cards--2" style="gap:clamp(2.2rem,4vw,3.5rem)">{whyhtml}</div>
    </div>
  </section>

  <section class="sect sect--paper2">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.8rem,6vw,4.5rem);max-width:50ch">
        {eyebrow("The space")}
        <h2>What your group has to work with</h2>
      </div>
      {spacehtml}
      <div class="rv" style="border-top:1px solid var(--line);padding-top:2.5rem">
        <h3 style="margin-bottom:1.3rem">Logistics</h3>
        {ilist(["200 AMP electrical service",
                "On-site water",
                "Parking for 75 cars",
                "Vendor and load-in access within 50 feet of the venue",
                "35 minutes from Glacier Park International Airport (FCA)",
                "Starlink internet in all five houses and the venue"])}
      </div>
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:46ch">
        {eyebrow("Formats we host")}
        <h2>Three ways groups use the estate</h2>
      </div>
      <div class="pkg pkg--3">{fhtml}</div>
    </div>
  </section>

  <section class="sect sect--paper2">
    <div class="wrap">
      {split(img("lounge-interior.jpg", "Lounge seating inside the pavilion"),
        f'''{eyebrow("Who it is for")}
        <h2>Teams that book it</h2>
        <div style="margin-top:1.8rem">{plist(who)}</div>''')}
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      {split(img("heli-new.jpg", "A helicopter over the Flathead valley"),
        f'''{eyebrow("Getting here")}
        <h2>Fly in and be working by afternoon</h2>
        <p class="lede" style="margin:1.4rem 0">Glacier Park International Airport is 35
          minutes from the gate, with direct service from multiple major cities. A team
          on a morning flight is in the pavilion after lunch.</p>
        <p>West Glacier and Glacier National Park sit about 45 minutes out for groups
          extending the trip, and helicopter arrivals are available through WestSlope
          Helicopters.</p>''',
        flip=True)}
    </div>
  </section>

  <section class="sect sect--forest">
    <div class="wrap">
      <div class="rv center" style="margin-bottom:clamp(2rem,4vw,2.8rem)">
        {eyebrow("Rates")}
        <h2>Full-estate buyout</h2>
        <p class="lede measure" style="margin-top:1.4rem">One rate for the whole property
          &mdash; no per-person charge and no shared space. What it comes to depends on
          the nights you want and the season, so we quote it against your actual dates.</p>
      </div>
      <p class="rv center" style="font-size:.95rem;color:#CFCabd;max-width:62ch;margin-inline:auto;margin-bottom:2.4rem">
        Send the dates and the headcount and we will come back with a written proposal,
        usually within one business day.</p>
      <div class="rv center">
        {btn("contact.html?type=corporate", "Request a Proposal", "btn btn--light btn--lg")}
      </div>
    </div>
  </section>

  <section class="sect sect--paper2 sect--tight">
    <div class="wrap">
      <div class="split split--wide-img">
        <div class="split__media rv rv--wipe">{img("barrel-sauna.jpg", "The cedar barrel sauna")}</div>
        <div class="split__body rv">
          {eyebrow("Also here")}
          <h2>Wellness retreats</h2>
          <p class="lede" style="margin-top:1.3rem">The same estate takes yoga,
            movement and recovery weeks &mdash; the pavilion as a floor that stays set,
            a sauna and hot tub a few steps from it, and nobody else on the property.</p>
          {tlink("wellness.html", "See wellness retreats")}
        </div>
      </div>
    </div>
  </section>

  {experiences(
      "Food and time off the clock",
      "Private chefs, catering and what the group does after",
      "Teams eat together here rather than scattering to restaurants. Tell us how you "
      "want the days fed and what you want the group doing between sessions, and we "
      "will put the people in place.",
      [("swan-kitchen-new.jpg", "The kitchen in the Swan",
        "Private chefs",
        "A private chef can cook for the group in the Swan&rsquo;s kitchen &mdash; one "
        "dinner, or every meal for the length of the stay."),
       ("food-truck-catering.jpg", "A food truck catering on the property",
        "Catering on site",
        "Full-service caterers, family-style service or a food truck on the lawn. We "
        "keep working relationships with Flathead Valley caterers and can introduce you."),
       ("grazing-table-spread.jpg", "A grazing table laid out for guests",
        "Grazing tables and the bar",
        "Grazing tables, working lunches that do not stop the day, and the built-in "
        "bar, already in place and ready to run."),
       ("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate",
        "On the lake",
        "Flathead Lake is minutes down the hill, with boating, swimming and sunset "
        "cruises when the group needs to be somewhere other than the pavilion."),
       ("heli-new.jpg", "A helicopter over the Flathead valley",
        "Helicopter arrivals",
        "Helicopter arrivals and private lake flights are available through WestSlope "
        "Helicopters."),
       ("pool-hottub-wide.jpg", "The pool and hot tub above the lake",
        "The property itself",
        "Heated pool, hot tub, barrel sauna, fitness room, games room, putting green, "
        "lawn games and walking trails, a short walk from where you are working.")])}

  {driftwood(DRIFTWOOD_SHOTS, "retreat")}

  <section class="sect sect--forest">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.8rem);max-width:20ch">
        {eyebrow("From our guests")}
        <h2>What groups say after a stay</h2>
      </div>
      <div class="quotes">
        {quote(*R_KELSEY_RETREAT)}
        {quote(*R_GREG_RETREAT)}
      </div>
    </div>
  </section>

  <section class="sect">
    <div class="wrap wrap--narrow">
      <div class="rv" style="margin-bottom:2.5rem">
        {eyebrow("Questions")}
        <h2>Practical answers</h2>
      </div>
      <div class="rv">{faq(faqs)}</div>
    </div>
  </section>

  {band("pool-house-firepit.jpg", "The fire pit and pool house after dark",
        "Tell us about your team",
        "Send your dates, your group size and what the retreat needs to accomplish, and "
        "you will get a tailored proposal back.",
        btn("contact.html?type=corporate", "Request a Proposal", "btn btn--light btn--lg"))}
"""


# ================================================================== ESTATE
def page_estate():
    houses = [
        ("The Swan", "Main house &middot; sleeps 14", "swan-exterior.jpg",
         "The Swan main house exterior",
         "Four bedrooms and four baths across three levels, with a gourmet kitchen, a "
         "full bar, a game room and balconies facing the water. It is the anchor of the "
         "property and where a group naturally collects."),
        ("The Glacier", "Modern cabin", "glacier-exterior.jpg",
         "The Glacier cabin among the trees",
         "A two-storey cabin in dark board-and-batten under a single sloping roof, with "
         "a sleeping loft and a private patio, set back far enough from the main house "
         "to feel like its own address."),
        ("The Lakeside", "Two modern tiny homes", "lakeside-both-homes.jpg",
         "The two Lakeside tiny homes side by side",
         "A pair of modern tiny homes, each with a full bath, a loft and a view down "
         "toward the water. Popular with couples travelling together."),
        ("The Summit", "Elevated treehouse", "summit-exterior.jpg",
         "The Summit treehouse in the canopy",
         "An elevated treehouse in the canopy, high enough that the lake shows through "
         "the trunks in the morning."),
        ("The Ridge", "Treehouse", "ridge-exterior.jpg",
         "The Ridge treehouse at the edge of the trees",
         "The second treehouse, set along the ridge line with its own deck and a quiet "
         "approach through the woods."),
    ]
    # every photograph we hold of each building, not just the one exterior
    shots = {
        "The Swan": [
            ("swan-exterior.jpg", "The Swan main house from the drive"),
            ("swan-kitchen-new.jpg", "The kitchen in the Swan"),
            ("swan-living-new.jpg", "The living room in the Swan"),
            ("swan-bar.jpg", "The bar in the Swan"),
            ("swan-bedroom-new.jpg", "A bedroom in the Swan"),
            ("swan-bedroom-alt.jpg", "Another bedroom in the Swan"),
            ("swan-game-room.jpg", "The game room in the Swan"),
            ("swan-bunk-room.jpg", "The bunk room in the Swan"),
            ("swan-lower-level.jpg", "The lower level of the Swan"),
        ],
        "The Glacier": [
            ("glacier-exterior.jpg", "The Glacier cabin among the trees"),
            ("glacier-loft.jpg", "The sleeping loft in the Glacier"),
            ("glacier-bedroom.jpg", "The bedroom in the Glacier"),
            ("glacier-patio.jpg", "The private patio at the Glacier"),
            ("glacier-exterior-alt.jpg", "The Glacier cabin from the side"),
        ],
        "The Lakeside": [
            ("lakeside-both-homes.jpg", "The two Lakeside tiny homes side by side"),
            ("lakeside-living.jpg", "The living space in a Lakeside tiny home"),
            ("lakeside-loft.jpg", "The loft in a Lakeside tiny home"),
            ("lakeside-bedroom.jpg", "The bedroom in a Lakeside tiny home"),
            ("lakeside-bathroom.jpg", "The bathroom in a Lakeside tiny home"),
            ("lakeside-exterior.jpg", "A Lakeside tiny home from outside"),
        ],
        "The Summit": [("summit-exterior.jpg", "The Summit treehouse in the canopy")],
        "The Ridge": [("ridge-exterior.jpg", "The Ridge treehouse at the edge of the trees")],
    }
    hhtml = switcher(
        "Where everyone sleeps",
        "Five buildings, sleeps twenty-eight",
        "Choose a building to look through it. Everything here is on the same fifteen "
        "acres, a short walk from the pavilion.",
        [(t, sub, d, shots[t]) for t, sub, im, alt, d in houses])

    grounds = [
        ("Heated pool &amp; cabana", "pool-wide.jpg", "The heated pool and cabana"),
        ("The pool house", "pool-house-firepit.jpg", "The pool house and fire pit at dusk"),
        ("Games room", "pool-house-pingpong.jpg", "The games room in the pool house"),
        ("Fitness room", "pool-house-gym.jpg", "The fitness room in the pool house"),
        ("Hot tub", "hottub-views.jpg", "The hot tub looking out over the valley"),
        ("Barrel sauna", "barrel-sauna.jpg", "The cedar barrel sauna"),
        ("Poolside loungers", "pool-loungers.jpg", "Loungers along the pool deck"),
        ("Putting green &amp; lawn games", "lakeside-putting-green.jpg", "The putting green"),
    ]
    ghtml = "".join(f"""<div class="card rv">
        <div class="card__img" style="aspect-ratio:1/1">{img(im, alt)}</div>
        <h4 style="font-family:var(--sans);font-size:.78rem;letter-spacing:.16em;text-transform:uppercase;font-weight:400">{t}</h4>
      </div>""" for t, im, alt in grounds)

    return f"""
{hero("lakeside-both-homes.jpg", "Two of the estate's accommodations at golden hour",
      "The Estate", "Five places to sleep,<br>fifteen acres to use",
      "The accommodation and grounds detail behind every wedding and every retreat "
      "booked here.", short=True)}

  <section class="sect">
    <div class="wrap wrap--narrow center rv">
      <h2>Twenty-eight people, one property</h2>
      <p class="lede" style="margin-top:1.4rem">The estate sleeps 28 across five separate
        accommodations. Everything below is on the same fifteen acres &mdash; nobody is
        driving between locations.</p>
    </div>
  </section>

  <section class="sect sect--paper2" style="padding-top:0">
    <div class="wrap" style="padding-top:var(--sect)">
      {hhtml}
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:48ch">
        {eyebrow("The grounds")}
        <h2>The rest of the fifteen acres</h2>
      </div>
      <div class="cards cards--3">{ghtml}</div>
      <div class="rv" style="margin-top:clamp(2.5rem,5vw,3.5rem);border-top:1px solid var(--line);padding-top:2.5rem">
        {ilist(["Walking trails across the property",
                "Starlink internet in all five houses and the venue",
                "200 AMP electrical service and on-site water",
                "Parking for 75 cars",
                "3,200 sq ft pavilion and 40&times;80 ft tent",
                "Vendor and load-in access within 50 feet of the venue"])}
      </div>
    </div>
  </section>

  {band("lake-sunset-boat.jpg", "The lake at sunset from the estate",
        "See it for yourself",
        "Photographs only go so far. Tell us your dates and we will walk you through the "
        "property and what it would look like for your group.",
        btn("contact.html", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== GALLERY
# (file, alt, category) — category: weddings | estate | grounds
PHOTOS = [
    ("wedding-aerial-tent.jpg", "Aerial view of the tent and ceremony lawn", "weddings"),
    ("ceremony-tent-wide.jpg", "Ceremony seating with the tent and lake behind", "weddings"),
    ("wedding-couple-arch.jpg", "A couple beneath the ceremony arch", "weddings"),
    ("ceremony-aisle-view.jpg", "The aisle looking toward the water", "weddings"),
    ("ceremony-setup.jpg", "Ceremony chairs set on the lawn", "weddings"),
    ("ceremony-forest.jpg", "A ceremony set among the trees", "weddings"),
    ("ceremony-vertical.jpg", "The ceremony site from the rear", "weddings"),
    ("wedding-bw-stairs.jpg", "Black and white portrait on the estate stairs", "weddings"),
    ("tent-front.jpg", "The front of the reception tent", "weddings"),
    ("venue-overview.jpg", "The estate and pavilion from above", "weddings"),
    ("venue-wide.jpg", "Wide view of the venue grounds", "weddings"),
    ("hero-pavilion-lake.jpg", "The pavilion at dusk above Flathead Lake", "weddings"),
    ("reception-tent-full.jpg", "The reception tent set for dinner", "weddings"),
    ("reception-long-table.jpg", "A long reception table under the tent", "weddings"),
    ("reception-mountain-view.jpg", "Reception tables against the mountains", "weddings"),
    ("evening-dinner-candlelight.jpg", "Dinner by candlelight after dark", "weddings"),
    ("table-setting-florals.jpg", "A place setting with florals", "weddings"),
    ("floral-arrangement-closeup.jpg", "Close view of a floral arrangement", "weddings"),
    ("cake-florals.jpg", "The cake table with florals", "weddings"),
    ("bar-cheers-setup.jpg", "The built-in bar set for service", "weddings"),
    ("lounge-interior.jpg", "Lounge seating inside the pavilion", "weddings"),
    ("grazing-table-spread.jpg", "A grazing table spread", "weddings"),
    ("food-truck-catering.jpg", "A catering truck on the grounds", "weddings"),
    ("vendor-party-setup.jpg", "Tables set for a vendor gathering", "weddings"),
    ("vendor-party-reception.jpg", "The pavilion during a vendor reception", "weddings"),
    ("vendor-party-details.jpg", "Table details at a vendor gathering", "weddings"),
    ("vendor-party-exterior.jpg", "The venue exterior during an event", "weddings"),
    ("vendor-appreciation-wall.jpg", "The vendor appreciation wall", "weddings"),

    ("swan-exterior.jpg", "The Swan main house exterior", "estate"),
    ("swan-living-new.jpg", "The living room in the Swan", "estate"),
    ("swan-kitchen-new.jpg", "The kitchen in the Swan", "estate"),
    ("swan-kitchen-alt.jpg", "Another view of the Swan kitchen", "estate"),
    ("swan-bar.jpg", "The bar in the Swan", "estate"),
    ("swan-bedroom-new.jpg", "A bedroom in the Swan", "estate"),
    ("swan-bedroom-alt.jpg", "Another bedroom in the Swan", "estate"),
    ("swan-bunk-room.jpg", "The bunk room in the Swan", "estate"),
    ("swan-game-room.jpg", "The game room in the Swan", "estate"),
    ("swan-game-room-alt.jpg", "Another view of the game room", "estate"),
    ("swan-lower-level.jpg", "The lower level of the Swan", "estate"),
    ("glacier-exterior.jpg", "The Glacier cabin exterior", "estate"),
    ("glacier-exterior-alt.jpg", "The Glacier cabin from the side", "estate"),
    ("glacier-bedroom.jpg", "A bedroom in the Glacier", "estate"),
    ("glacier-loft.jpg", "The sleeping loft in the Glacier", "estate"),
    ("glacier-patio.jpg", "The Glacier's private patio", "estate"),
    ("lakeside-exterior.jpg", "A Lakeside tiny home exterior", "estate"),
    ("lakeside-both-homes.jpg", "Both Lakeside tiny homes", "estate"),
    ("lakeside-living.jpg", "Inside a Lakeside tiny home", "estate"),
    ("lakeside-bedroom.jpg", "A bedroom in the Lakeside", "estate"),
    ("lakeside-loft.jpg", "The loft in the Lakeside", "estate"),
    ("lakeside-bathroom.jpg", "The bathroom in the Lakeside", "estate"),
    ("summit-exterior.jpg", "The Summit treehouse", "estate"),
    ("ridge-exterior.jpg", "The Ridge treehouse", "estate"),

    ("pool-wide.jpg", "The heated pool and cabana", "grounds"),
    ("pool-hottub-wide.jpg", "The pool and hot tub together", "grounds"),
    ("pool-loungers.jpg", "Loungers beside the pool", "grounds"),
    ("pool-house-firepit.jpg", "The fire pit beside the pool house", "grounds"),
    ("hottub-views.jpg", "The hot tub looking over the valley", "grounds"),
    ("pool-house-gym.jpg", "The fitness room in the pool house", "grounds"),
    ("pool-house-pingpong.jpg", "The games room in the pool house", "grounds"),
    ("barrel-sauna.jpg", "The cedar barrel sauna", "grounds"),
    ("lakeside-putting-green.jpg", "The putting green", "grounds"),
    ("lake-sunset-boat.jpg", "A boat on Flathead Lake at sunset", "grounds"),
    ("heli-new.jpg", "A helicopter over the Flathead valley", "grounds"),
]


def page_gallery():
    figs = "".join(
        f'<figure class="rv" data-cat="{cat}" data-full="{IMG}{f}">'
        f'<img src="{THMB}{f}" alt="{alt}" loading="lazy" decoding="async"></figure>'
        for f, alt, cat in PHOTOS)

    return f"""
  <section class="sect sect--tight" style="padding-top:clamp(8rem,14vw,11rem)">
    <div class="wrap center rv">
      {eyebrow("Gallery")}
      <h2>{len(PHOTOS)} photographs of the property</h2>
      <p class="lede measure" style="margin-top:1.4rem">Everything here was shot on the
        estate. Select a photograph to open it full size.</p>
    </div>
  </section>

  <section style="padding-bottom:var(--sect)">
    <div class="wrap">
      <div class="gfilter">
        <button data-filter="all" aria-pressed="true">All</button>
        <button data-filter="weddings" aria-pressed="false">Weddings</button>
        <button data-filter="estate" aria-pressed="false">The Estate</button>
        <button data-filter="grounds" aria-pressed="false">Grounds &amp; Amenities</button>
      </div>
      <div class="grid">{figs}</div>
    </div>
  </section>

  {band("venue-wide.jpg", "Wide view of the estate grounds",
        "Come see the rest",
        "Photographs miss the scale of the place. Tell us your dates and we will show "
        "you the property properly.",
        btn("contact.html", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== STORY
def page_story():
    return f"""
{hero("owners-photo.jpg", "Claudia and Eric on the estate", "Our Story",
      "Claudia &amp; Eric", "The two people who answer your inquiry are the two people "
      "who built the place.", short=True)}

  <section class="sect">
    <div class="wrap wrap--narrow rv">
      <p class="lede">We started with rental houses. In 2021 we began hosting guests on
        Flathead Lake as Flathead Lake Luxury Lodging, and for four years we learned the
        thing you only learn by doing it &mdash; what a group actually needs when they
        take over a property for a weekend.</p>
      <p style="margin-top:1.6rem">The pattern repeated. Guests booked a house for a
        celebration and then spent the planning months stitching together a venue
        somewhere else: a tent from one vendor, generators from another, a bar built on
        site, lighting hung the morning of, and a hard cutoff at ten because of an
        ordinance nobody mentioned until late.</p>
      <p>So in 2025 we built the venue those weekends kept asking for. The pavilion, the
        tent, the power, the bar, the lighting, the parking &mdash; permanent, on the
        same fifteen acres as the houses, so that the celebration and the place everyone
        sleeps are finally in the same place.</p>
      <p>We keep the calendar deliberately short. One group at a time is not a marketing
        position; it is the only way the property works.</p>
    </div>
  </section>

  <section class="sect sect--forest">
    <div class="wrap wrap--narrow center rv">
      <blockquote style="font-family:var(--serif);font-size:clamp(1.5rem,3vw,2.3rem);line-height:1.38;font-style:italic;color:#fff;margin:0">
        &ldquo;We wanted the kind of place where nobody has to leave at the end of the
        night. Everything else followed from that.&rdquo;
      </blockquote>
      <p style="margin-top:2rem;font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;color:var(--gold-soft)">
        Claudia &amp; Eric &middot; Owners</p>
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      {split(img("vendor-appreciation-wall.jpg", "The vendor appreciation wall on the estate"),
        '''<h2>The people we work with</h2>
        <p class="lede" style="margin:1.4rem 0">A venue is only as good as the planners,
          caterers, florists and photographers who work it. We keep real relationships
          with a short list of Flathead Valley vendors who know the property, and
          several extend a partner discount to our couples.</p>
        <p>You are never required to book from that list. It exists because it saves
          people time, not because it earns us a commission.</p>''',
        flip=True)}
    </div>
  </section>

  {band("lake-sunset-boat.jpg", "The lake at sunset",
        "Come and see it",
        "Send us your dates. Claudia or Eric will write back personally.",
        btn("contact.html", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== CONTACT
def page_contact():
    return f"""
  <section class="sect sect--tight" style="padding-top:clamp(8rem,14vw,11rem)">
    <div class="wrap">
      <div class="split" style="align-items:start">
        <div class="rv">
          {eyebrow("Contact")}
          <h1 style="font-size:clamp(2.3rem,4.6vw,3.6rem)">Start your inquiry</h1>
          <p class="lede" style="margin-top:1.6rem">Tell us the dates you are considering
            and the shape of the gathering. Claudia or Eric answers every inquiry
            personally, usually within one business day.</p>

          <div style="margin-top:3rem;border-top:1px solid var(--line);padding-top:2rem">
            <h4 style="font-family:var(--sans);font-size:.72rem;letter-spacing:.17em;text-transform:uppercase;color:var(--muted);font-weight:400;margin-bottom:1.2rem">Direct</h4>
            {plist([f'<a href="mailto:{BIZ["email"]}" style="text-decoration:none">{BIZ["email"]}</a>',
                    f'<a href="tel:{BIZ["tel"]}" style="text-decoration:none">{BIZ["phone"]}</a>',
                    f'{BIZ["city"]}, {BIZ["state"]}',
                    f'<a href="{BIZ["ig"]}" rel="noopener" style="text-decoration:none">Instagram {BIZ["handle"]}</a>'])}
          </div>

          <div style="margin-top:2.5rem;border-top:1px solid var(--line);padding-top:2rem">
            <h4 style="font-family:var(--sans);font-size:.72rem;letter-spacing:.17em;text-transform:uppercase;color:var(--muted);font-weight:400;margin-bottom:1.2rem">Getting here</h4>
            <p style="color:var(--ink-soft);font-size:.98rem">Lakeside, Montana &mdash; 35
              minutes from Glacier Park International Airport (FCA), about 45 minutes from
              Glacier National Park and Whitefish Mountain Resort.</p>
          </div>
        </div>

        {honeybook_form() if INQUIRY_MODE == "honeybook" else own_form()}
      </div>
    </div>
  </section>

  {getting_here()}
"""



# Two ways to take an inquiry. "honeybook" embeds the live lead form, so a
# submission becomes a real HoneyBook inquiry with its workflows attached.
# "own" renders the hand-built form below, which still needs an endpoint.
INQUIRY_MODE = "honeybook"


def own_form():
    return f"""        <div class="rv">
          <!-- WIRING: see README step 2. Either set data-endpoint (HoneyBook / CRM
               webhook, posts JSON) or replace action= with your Formspree URL. -->
          <form class="form" id="inquiry" method="POST"
                action="https://formspree.io/f/YOUR_FORM_ID"
                data-endpoint="">
            <div class="formstatus" role="status" aria-live="polite"></div>

            <div class="field">
              <label for="name">Name <span class="req">*</span></label>
              <input id="name" name="name" type="text" autocomplete="name" required>
            </div>
            <div class="field">
              <label for="email">Email <span class="req">*</span></label>
              <input id="email" name="email" type="email" autocomplete="email" required>
            </div>
            <div class="field">
              <label for="phone">Phone</label>
              <input id="phone" name="phone" type="tel" autocomplete="tel">
            </div>
            <div class="field">
              <label for="eventType">Event type <span class="req">*</span></label>
              <select id="eventType" name="eventType" required>
                <option value="">Select one</option>
                <option value="Wedding">Wedding</option>
                <option value="Corporate Retreat">Corporate Retreat</option>
                <option value="Other Private Event">Other Private Event</option>
              </select>
            </div>
            <div class="field">
              <label for="dates">Preferred dates</label>
              <input id="dates" name="dates" type="text" placeholder="e.g. late August 2027, or flexible">
            </div>
            <div class="field">
              <label for="groupSize">Group size</label>
              <input id="groupSize" name="groupSize" type="text" placeholder="Guests, and how many staying onsite">
            </div>
            <div class="field field--full">
              <label for="message">Tell us about it</label>
              <textarea id="message" name="message"
                placeholder="What are you planning, and what would make the weekend work?"></textarea>
            </div>
            <button class="btn btn--lg" type="submit">Send Inquiry</button>
            <p class="form__note">We use this to answer you and nothing else. No list, no
              drip sequence.</p>
          </form>
        </div>"""



# ================================================================== WELLNESS
def page_wellness():
    cards = [
        ("hero-pavilion-lake.jpg", "The empty pavilion looking out over Flathead Lake",
         "Room to move",
         "The pavilion is 3,200 sq ft under cover with the lake in front of it &mdash; "
         "clear floor for mats, and nobody needs to reset it between sessions. It runs "
         "clear-top or fully enclosed with sides, which makes shoulder season workable."),
        ("barrel-sauna.jpg", "The cedar barrel sauna",
         "Heat and cold",
         "A cedar barrel sauna, a hot tub and a heated pool within a few steps of each "
         "other, so contrast work does not mean going anywhere or booking a slot."),
        ("pool-house-gym.jpg", "The fitness room in the pool house",
         "The fitness room",
         "Equipment in the pool house with the water through the glass. Open at five in "
         "the morning if that is when your group trains, because your group is the only "
         "one here."),
        ("venue-overview.jpg", "The estate grounds from above",
         "Fifteen acres to walk",
         "Trails across the property for a morning walk or a long silence, and Flathead "
         "Lake minutes down the hill when the week calls for water."),
        ("swan-kitchen-new.jpg", "The kitchen in the Swan",
         "Food that fits the week",
         "A private chef can cook to whatever the retreat calls for &mdash; plant-based, "
         "protein-forward, or simply early. Caterers can take the whole stay instead."),
        ("pool-loungers.jpg", "Loungers along the pool deck",
         "Nowhere to be",
         "No lobby to cross, no other guests, no schedule but yours. Most of what a "
         "retreat is trying to buy is the absence of other people, and that is the "
         "part we can actually guarantee."),
    ]
    chtml = "".join(
        f'<div class="exp__card"><div class="exp__img">{img(f, a)}</div>'
        f'<h3>{t}</h3><p>{d}</p></div>' for f, a, t, d in cards)

    spec_groups = [
        ("The space", [
            "<b>3,200 sq ft</b> pavilion, clear floor, lake views",
            "<b>40 &times; 80 ft</b> tent &mdash; clear-top or enclosed with sides",
            "Fitness room in the pool house",
            "Fire pit and covered terraces",
        ]),
        ("Water and heat", [
            "Heated pool",
            "Hot tub",
            "Cedar barrel sauna",
            "Flathead Lake, minutes down the hill",
        ]),
        ("The group", [
            "Sleeps <b>28</b> across five accommodations",
            "<b>One</b> group on the property at a time",
            "Private chef or full catering, arranged",
            "Starlink at the venue and in all five houses",
        ]),
        ("The setting", [
            "<b>15</b> private acres above Flathead Lake",
            "Walking trails across the property",
            "<b>35 min</b> from Glacier Park International Airport",
            "<b>45 min</b> from Glacier National Park",
        ]),
    ]

    faqs = [
        ("Can we bring our own instructors and practitioners?",
         "<p>Yes, and most groups do. If you would rather not, tell us what the week "
         "needs and we will look for it in the valley.</p>"),
        ("How many people can a retreat be?",
         "<p>28 stay on the property across the five accommodations. The pavilion holds "
         "far more than that for daytime sessions if part of your group is coming in "
         "from town.</p>"),
        ("Is the whole property really private?",
         "<p>Yes. One group is on the estate at a time, for the length of the booking. "
         "There is no other party on the far lawn and nobody crossing to a pool.</p>"),
        ("Can you handle specific diets?",
         "<p>A private chef is the simplest route &mdash; they cook for your group "
         "alone, so a menu built around whatever the week requires is normal rather "
         "than an accommodation.</p>"),
        ("What time of year works?",
         "<p>Summer is the obvious answer, but the tent encloses fully with sides and "
         "every building is heated, so spring and autumn work. Ask us about "
         "shoulder-season dates.</p>"),
    ]

    return f"""
{hero("pool-wide.jpg",
      "The heated pool and terrace above Flathead Lake",
      "Wellness Retreats",
      "A quiet estate<br>for the work of resting",
      "Fifteen private acres above Flathead Lake, closed to everyone but your group "
      "&mdash; for yoga, movement, recovery and the retreats people actually remember.",
      btn("contact.html?type=wellness", "Check Availability", "btn btn--light btn--lg")
      + btn("#what", "What Is Here", "btn btn--outline-light btn--lg"),
      slides=[("pool-hottub-wide.jpg", "The pool and hot tub on the terrace"),
              ("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate")])}

  <section class="sect">
    <div class="wrap">
      <div class="rv" style="max-width:56ch">
        {eyebrow("Why here")}
        <h2>The hard part is already solved</h2>
        <p class="lede" style="margin-top:1.4rem">A retreat needs a room that can be
          held all week, water and heat within walking distance, food that bends to the
          programme, and no strangers. Most places give you two of those.</p>
        <p style="color:var(--ink-soft);max-width:62ch">The estate is booked one group
          at a time, so the pavilion stays set, the sauna is yours at six in the
          morning, and nobody has to explain to a front desk why twenty people are
          barefoot on the lawn.</p>
      </div>
    </div>
  </section>

  <section class="sect sect--paper2" id="what">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:52ch">
        {eyebrow("What is here")}
        <h2>A property that already works for this</h2>
      </div>
      <div class="exp rv rv--stagger">{chtml}</div>
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      <div class="split split--wide-img">
        <div class="split__body rv">
          {eyebrow("Who books it this way")}
          <h2>Retreats we host</h2>
          <p class="lede" style="margin-top:1.3rem">Bring your own instructors and
            practitioners, or tell us what the week needs and we will find them in the
            valley.</p>
        </div>
        <div class="split__media rv" style="align-self:center">
          {ilist(["Women&rsquo;s retreats",
                  "Men&rsquo;s retreats",
                  "Yoga, breathwork and movement",
                  "Leadership resets and founder offsites",
                  "Teacher trainings and small certifications",
                  "Recovery and longevity weeks"])}
        </div>
      </div>
    </div>
  </section>

  <section class="sect sect--paper2">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:50ch">
        {eyebrow("The detail")}
        <h2>Everything the week can use</h2>
      </div>
      {spec(spec_groups)}
    </div>
  </section>

  <section class="sect sect--forest">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.8rem);max-width:22ch">
        {eyebrow("From our guests")}
        <h2>What groups say after a stay</h2>
      </div>
      <div class="quotes">
        {quote(*R_KELSEY_RETREAT)}
        {quote(*R_GREG_RETREAT)}
      </div>
    </div>
  </section>

  <section class="sect">
    <div class="wrap wrap--narrow">
      <div class="rv" style="margin-bottom:2.5rem">
        {eyebrow("Questions")}
        <h2>Before you book</h2>
      </div>
      <div class="rv">{faq(faqs)}</div>
    </div>
  </section>

  {band("hottub-views.jpg", "The hot tub looking out over the valley",
        "Tell us what the week is for",
        "Send the dates and the shape of the retreat and we will tell you honestly "
        "whether the estate is open and whether it suits.",
        btn("contact.html?type=wellness", "Check Availability", "btn btn--light btn--lg"))}
"""


# ================================================================== assembly
CRUMB = {"weddings.html": "Weddings", "retreats.html": "Corporate Retreats",
         "wellness.html": "Wellness Retreats",
         "estate.html": "The Estate", "gallery.html": "Gallery",
         "story.html": "Our Story", "contact.html": "Contact"}

PAGES = [
    ("index.html", page_home, "hero-pavilion-lake.jpg", True,
     "The Overlook at Flathead Lake | Private Montana Estate",
     "A private 15-acre estate above Flathead Lake, Montana, booked exclusively for "
     "one group — weddings up to 200 guests, corporate retreats, 28 sleeping onsite."),

    ("weddings.html", page_weddings, "ceremony-tent-wide.jpg", True,
     "Montana Wedding Venue on Flathead Lake | The Overlook",
     "A multi-day wedding weekend on a private 15-acre Flathead Lake estate. Up to 200 "
     "guests, 28 sleeping onsite, pavilion, tent and bar already standing."),

    ("retreats.html", page_retreats, "venue-overview.jpg", True,
     "Montana Corporate Retreat Venue | The Overlook at Flathead Lake",
     "A private full-estate buyout above Flathead Lake for leadership teams, boards and "
     "company gatherings. Full-estate buyout, Starlink throughout, 35 minutes from FCA."),

    ("wellness.html", page_wellness, "pool-wide.jpg", True,
     "Montana Wellness Retreat Venue | The Overlook at Flathead Lake",
     "A private 15-acre estate above Flathead Lake for yoga, movement and recovery "
     "retreats. Pavilion, sauna, hot tub, heated pool, 28 onsite, one group at a time."),

    ("estate.html", page_estate, "lakeside-both-homes.jpg", True,
     "The Estate | Lodging &amp; Grounds at The Overlook at Flathead Lake",
     "Five accommodations sleeping 28, plus a heated pool, sauna, fitness room, fire pit "
     "and trails across 15 private acres above Flathead Lake."),

    ("gallery.html", page_gallery, "wedding-aerial-tent.jpg", False,
     "Gallery | The Overlook at Flathead Lake",
     "Photographs of the estate, weddings, accommodations and grounds at The Overlook at "
     "Flathead Lake in Lakeside, Montana."),

    ("story.html", page_story, "owners-photo.jpg", True,
     "Our Story | The Overlook at Flathead Lake",
     "How Claudia and Eric went from hosting guests on Flathead Lake in 2021 to building "
     "The Overlook venue in 2025."),

    ("contact.html", page_contact, "hero-pavilion-lake.jpg", False,
     "Contact | The Overlook at Flathead Lake",
     "Start an inquiry for a wedding, corporate retreat or private event at The Overlook "
     "at Flathead Lake in Lakeside, Montana."),
]


def _plain(frag):
    """Strip tags/entities so HTML answers can go into JSON-LD as plain text."""
    t = re.sub(r"<[^>]+>", " ", frag)
    return re.sub(r"\s+", " ", ihtml.unescape(t)).strip()


def faq_schema(items):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": _plain(q),
         "acceptedAnswer": {"@type": "Answer", "text": _plain(a)}} for q, a in items]}


# Lakeside town centre, not the estate — the exact location is not published.
GEO = {"@type": "GeoCoordinates", "latitude": 48.0172, "longitude": -114.2244}

ADDRESS = {"@type": "PostalAddress", "addressLocality": BIZ["city"],
           "addressRegion": BIZ["state"], "addressCountry": "US"}

AMENITIES = ["Heated pool", "Hot tub", "Barrel sauna", "Fitness room", "Games room",
             "Fire pit", "Putting green", "Walking trails", "Starlink internet",
             "Onsite parking for 75 cars", "Event pavilion and tent", "Built-in bar",
             "Private chef available", "Catering arranged on site",
             "Helicopter arrivals available"]


def venue_schema():
    """The homepage graph. No prices: the site does not publish any."""
    return {"@context": "https://schema.org", "@graph": [
        {"@type": ["EventVenue", "LodgingBusiness"], "@id": f"{SITE}/#venue",
         "name": BIZ["name"],
         "description": ("A private 15-acre estate above Flathead Lake in Lakeside, "
                         "Montana, booked exclusively for one group at a time. Weddings "
                         "for up to 200 guests, corporate retreats, and sleeping for 28 "
                         "across five accommodations."),
         "url": f"{SITE}/", "telephone": BIZ["tel"], "email": BIZ["email"],
         "address": ADDRESS, "geo": GEO, "areaServed": "Flathead Valley, Montana",
         "maximumAttendeeCapacity": 200,
         "petsAllowed": False,
         "numberOfRooms": 5,
         "image": [f"{SITE}/{IMG}{f}" for f in
                   ("hero-pavilion-lake.jpg", "venue-overview.jpg", "swan-exterior.jpg",
                    "pool-wide.jpg", "lake-sunset-boat.jpg")],
         "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": a,
                             "value": True} for a in AMENITIES],
         "containsPlace": [
             {"@type": "Accommodation", "name": "The Swan",
              "description": "Four-bedroom, four-bath main house across three levels."},
             {"@type": "Accommodation", "name": "The Glacier",
              "description": "Two-storey cabin with a sleeping loft and private patio."},
             {"@type": "Accommodation", "name": "The Lakeside",
              "description": "Two modern tiny homes, each with a full bath and a loft."},
             {"@type": "Accommodation", "name": "The Summit",
              "description": "Elevated treehouse in the canopy."},
             {"@type": "Accommodation", "name": "The Ridge",
              "description": "Treehouse along the ridge line with its own deck."}],
         # No prices are published, so no Offer carries one — a figure here would
         # be quoted back by search and assistants as if it were on the page.
         "makesOffer": [
             {"@type": "Offer", "name": "Wedding weekend",
              "description": "Exclusive use of the estate for a multi-day wedding. "
                             "Quoted against your dates."},
             {"@type": "Offer", "name": "Corporate or private retreat",
              "description": "Full-property buyout. Quoted against your dates."},
             {"@type": "Offer", "name": "Private chef and catering",
              "description": "A private chef can cook for the group in the main house, "
                             "and full-service catering or a food truck can be arranged "
                             "on the property."},
             {"@type": "Offer", "name": "The Ultimate Flathead Lake Wedding Weekend",
              "description": "Five nights across two estates — The Overlook and The "
                             "Driftwood, a 14,000 sq ft lakefront home in Woods Bay — "
                             "sleeping up to 54 guests.",
              "priceSpecification": {"@type": "PriceSpecification",
                                     "minPrice": 100000, "priceCurrency": "USD"}}],
         "sameAs": [BIZ["ig"], BIZ["ig_sis"]]},
        {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/",
         "name": BIZ["name"], "publisher": {"@id": f"{SITE}/#venue"},
         "inLanguage": "en-US"}]}


def crumbs(name, label):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": label, "item": f"{SITE}/{name}"}]}


def schema(name, label):
    """Every page gets structured data, not just the homepage."""
    blocks = []
    if name == "index.html":
        blocks.append(venue_schema())
    else:
        blocks.append(crumbs(name, label))
    if name == "weddings.html":
        blocks.append(faq_schema(FAQ_WEDDINGS))
    if name == "retreats.html":
        blocks.append(faq_schema(FAQ_RETREATS))
    return "".join('<script type="application/ld+json">\n%s\n</script>\n'
                   % json.dumps(b, ensure_ascii=False, separators=(",", ":"))
                   for b in blocks)


def llms_txt():
    """https://llmstxt.org — a plain-language brief for models that read the site.

    Everything here is also in the HTML; this just removes any need to infer it.
    """
    faq = "\n".join(f"- **{_plain(q)}** {_plain(a)}"
                     for q, a in FAQ_WEDDINGS[:5] + FAQ_RETREATS[:3])
    return f"""# {BIZ['name']}

> A private 15-acre estate above Flathead Lake in {BIZ['city']}, {BIZ['region']}, booked
> exclusively for one group at a time. Weddings for up to 200 guests, corporate and
> private retreats, and sleeping for 28 people across five accommodations.

## Facts

- Location: {BIZ['city']}, {BIZ['region']}, on the west shore of Flathead Lake
- Event capacity: up to 200 guests
- Sleeping capacity: 28 people across five accommodations (The Swan, The Glacier,
  The Lakeside, The Summit, The Ridge)
- Exclusivity: one group on the property at a time; no shared facilities
- Pricing: not published, with one exception below. Every other booking is quoted
  directly against the dates and the shape of the event.
- The Ultimate Flathead Lake Wedding Weekend: starting at $100,000
- That package is five nights across two estates: The Overlook (sleeps 28) plus The
  Driftwood, a 14,000 sq ft lakefront home at Woods Bay (sleeps 26), for a combined 54.
  Helicopter transfer between the two is available through WestSlope Helicopters.
- Travel: 35 minutes from Glacier Park International Airport (FCA); about 45 minutes
  from Glacier National Park and Whitefish Mountain Resort
- Amenities: {", ".join(AMENITIES)}
- Food: a private chef can cook for the group in the main house; full-service catering,
  family-style service, grazing tables or a food truck on the lawn can all be arranged.
  The bar is built in.
- Activities: Flathead Lake boating and swimming minutes away; helicopter arrivals and
  private lake flights through WestSlope Helicopters; Glacier
  National Park and Whitefish Mountain Resort about 45 minutes away
- Contact: {BIZ['phone']} / {BIZ['email']}
- Owners: Claudia and Eric, who answer inquiries personally

## Pages

- [Home]({SITE}/): overview of the estate and both ways it is booked
- [Weddings]({SITE}/weddings.html): the wedding weekend, what is included, pricing, FAQ
- [Corporate Retreats]({SITE}/retreats.html): full-property buyout for teams, formats, rates
- [Wellness Retreats]({SITE}/wellness.html): yoga, movement and recovery retreats — the
  pavilion as a movement floor, sauna, hot tub, heated pool, trails, private chef
- [The Estate]({SITE}/estate.html): the five accommodations and the grounds
- [Gallery]({SITE}/gallery.html): photographs of the property
- [Our Story]({SITE}/story.html): how the venue came to be
- [Contact]({SITE}/contact.html): inquiry form, location and drive times

## Common questions

{faq}
"""


def main():
    missing = set()
    for name, fn, og, over, title, desc in PAGES:
        body = fn()
        # the LCP image on every page is its hero, so tell the browser early
        extra = (f'<link rel="preload" as="image" href="{IMG}{og}" fetchpriority="high">\n'
                 + schema(name, CRUMB.get(name, "Home")))
        html = (head(title, desc, name, og, extra)
                + header(name, over_hero=over) + body
                + footer().replace("{year}", str(YEAR))
                          .replace("{STICKYBAR}", stickybar(name)))
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(html)
        # verify every referenced photo actually exists
        for part in html.split('src="')[1:]:
            p = part.split('"')[0]
            if p.startswith(("assets/img/", "assets/thumb/")) and \
               not os.path.exists(os.path.join(ROOT, p)):
                missing.add(p)
        print(f"  wrote {name:16s} {len(html)//1024:>3d} KB")

    # sitemap + robots
    today = datetime.date.today().isoformat()
    urls = "".join(
        f"<url><loc>{SITE}/{'' if n == 'index.html' else n}</loc>"
        f"<lastmod>{today}</lastmod>"
        f"<priority>{'1.0' if n=='index.html' else '0.8'}</priority></url>"
        for n, *_ in PAGES)
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    ai_bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
               "Claude-SearchBot", "PerplexityBot", "Perplexity-User", "Google-Extended",
               "Applebot-Extended", "CCBot", "meta-externalagent", "Bytespider"]
    bots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ai_bots)
    open(os.path.join(ROOT, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\n"
        f"# Assistants are welcome to read and cite this site.\n{bots}"
        f"Sitemap: {SITE}/sitemap.xml\n")
    open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write(llms_txt())
    print("  wrote sitemap.xml, robots.txt, llms.txt")

    if missing:
        print("\n  !! MISSING IMAGES:")
        for m in sorted(missing):
            print("     ", m)
        return 1
    print(f"\n  {len(PAGES)} pages, {len(PHOTOS)} gallery photos, all images present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
