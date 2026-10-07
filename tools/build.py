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
import os, re, sys, json, hashlib, datetime
import html as ihtml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import images
from shell import (SITE, BIZ, NAV, IMG, THMB, rel, FCA, WHITEFISH, GLACIER, cap,
                   hero_preload, SZ_FULL, SZ_HALF, SZ_THIRD, SZ_GALLERY, SZ_THUMB,
                   img, imgsize, eyebrow, btn, tlink,
                   plist, ilist, quote, faq, hero, band, split, vmap, stickybar, marquee,
                   getting_here, switcher, rail, mosaic, hb_form, spec, sectnav, experiences,
                   weekend_builder, film,
                   driftwood, slideshow,
                   head, header, footer, CF_ANALYTICS_TOKEN, PACKAGE_CAMPAIGN)

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
     f"<p>The estate sits above Flathead Lake in Lakeside, Montana, {FCA['time']} "
     f"from {FCA['name']}, {WHITEFISH['time']} from {WHITEFISH['name']} and "
     f"{GLACIER['time']} from {GLACIER['entrance']}, the west entrance to "
     f"{GLACIER['name']}.</p>"),
    ("How many guests can it hold?",
     "<p>Up to 200 guests for the celebration itself. Separately, up to 28 people "
     "sleep on the property across the five accommodations &mdash; usually the couple "
     "and their closest family and wedding party.</p>"),
    ("What does a booking include?",
     "<p>A booking covers exclusive use of the whole venue &mdash; everything "
     "listed under What&rsquo;s included, and your onsite venue coordinator. The "
     "figure depends on your dates and the shape of the weekend. "
     "<a href='overlook-wedding.html'>See the package in full.</a></p>"),
    ("Is lodging included or separate?",
     "<p>Separate. Lodging is booked apart from the venue fee, so you only take the "
     "houses you need. "
     "<a href='estate.html'>See where everyone stays.</a></p>"),
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
     "<p>Yes. The pavilion holds the whole group for working sessions, and the main "
     "house and the grounds give you room for breakouts and meals.</p>"),
    ("Do you offer team experiences or local activities?",
     "<p>Helicopter arrivals and private lake flights are available through WestSlope "
     "Helicopters, along with access to Flathead Lake recreation and Glacier National "
     "Park.</p>"),
    # No claim about which cities fly into FCA: the route map is the airport's to
    # change, not ours, and it is not a fact we hold.
    ("How far is the nearest airport?",
     f"<p>{FCA['name']} is {FCA['time']} from the estate. {WHITEFISH['name']} is "
     f"{WHITEFISH['time']} away, and {GLACIER['entrance']}, the west entrance to "
     f"{GLACIER['name']}, {GLACIER['time']}.</p>"),
    ("How do we get a custom proposal?",
     "<p>Send your dates, your group size and what the gathering needs to accomplish, "
     "and we will send you a written proposal.</p>"),
]

FAQ_WELLNESS = [
    ("Can we bring our own instructors and practitioners?",
     "<p>Yes. Or tell us what the week needs and we will look for the right people "
     "in the valley.</p>"),
    ("How many people can a retreat be?",
     "<p>28 stay on the property across the five accommodations. The pavilion holds "
     "far more than that for daytime sessions if part of your group is coming in "
     "from town.</p>"),
    ("Is the whole property really private?",
     "<p>Yes. For the length of the booking the estate is yours alone &mdash; "
     "nobody on the far lawn and nobody crossing to the pool.</p>"),
    ("Can you handle specific diets?",
     "<p>Yes. A private chef cooks for your group alone, so the menu can be built "
     "around whatever the week requires.</p>"),
    ("What time of year works?",
     "<p>Summer is the easiest. The tent closes fully with sides, so spring and "
     "autumn work too. Ask us about shoulder-season dates.</p>"),
]

FAQ_AREA = [
    ("How far is Glacier National Park?",
     f"{cap(GLACIER['time'])} — {GLACIER['miles']} to {GLACIER['entrance']}, the west "
     f"entrance to the park."),
    ("How close is the lake?",
     "The estate sits on the hillside above Flathead Lake in Lakeside. Boating and "
     "swimming are minutes away."),
    ("What is there to do without leaving the property?",
     "A heated pool, a hot tub, a barrel sauna, a fitness room, a games room, a fire "
     "pit, a putting green and walking trails across the fifteen acres."),
    ("Can guests arrive by helicopter?",
     "Yes. Helicopter arrivals and private flights over the lake are arranged through "
     "WestSlope Helicopters."),
    ("How far is Whitefish Mountain Resort?",
     f"{cap(WHITEFISH['time'])} from the estate."),
    ("Which airport do guests fly into?",
     f"{FCA['name']}, {FCA['time']} away."),
    ("Is there skiing near the estate?",
     "Blacktail Mountain Ski Area is on the mountain above Lakeside, 14 miles up "
     f"Blacktail Road. {WHITEFISH['name']} is {WHITEFISH['time']} away."),
    ("Where can guests stay if the estate is full?",
     "The estate sleeps 28. Nearby, Flathead Harbor in Lakeside has cabins and condos "
     "on the lake, and Whitefish and Kalispell have hotels."),
    ("What is the museum in Polson?",
     "The Miracle of America Museum, at the south end of Flathead Lake: a museum of "
     "Americana with a village of more than 40 historic buildings."),
]

FAQ_MTVENUES = [
    ("What is an estate-buyout wedding venue?",
     "One group takes the whole property for the length of the booking. The "
     "celebration and the place people sleep are on the same land, and no other event "
     "shares the site."),
    ("How many guests can this venue hold?",
     "Up to 200 guests for the celebration. Separately, 28 people sleep on the "
     "property across five accommodations."),
    ("Is lodging included in the venue fee?",
     "No. Lodging is booked separately from the venue fee, so you only take the "
     "houses you need."),
    ("What should I ask a Montana venue before booking?",
     "Whether power and water are permanently installed or brought in, how far vendors "
     "load in, how many cars park on site, when the noise cutoff falls, what is already "
     "standing, and whether another event shares the property that weekend."),
    ("How far ahead do Montana venues book?",
     "Summer Saturdays go first, so if you have one in mind, ask early. Send the "
     "weekend and we will tell you whether it is open."),
    ("Is pricing published?",
     "Two starting figures are published: The Overlook Wedding starts at $20,000, and "
     "the Ultimate Flathead Lake Wedding Weekend, which adds The Driftwood, starts at "
     "$135,000. Everything beyond those is quoted against your dates and the shape of "
     "the event."),
]

# One page, one FAQ list. The page renders it, schema() turns it into FAQPage
# structured data and llms_txt() prints it, so the three cannot drift apart.
FAQS = {"weddings.html": FAQ_WEDDINGS,
        "retreats.html": FAQ_RETREATS,
        "wellness.html": FAQ_WELLNESS,
        "things-to-do/index.html": FAQ_AREA,
        "wedding-venues-montana/index.html": FAQ_MTVENUES}


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
    # the headline already says fifteen acres; the strip says something new
    facts = [("200", "Event guests"), ("28", "Sleep onsite"),
             (FCA["brief"].split()[0], "Min from the airport"), ("One", "Group at a time")]
    parts = []
    for n, l in facts:
        attr = ' data-count="%s"' % n if n.isdigit() else ""
        parts.append('<div class="facts__item"><span class="facts__n"%s>%s</span>'
                     '<span class="facts__l">%s</span></div>' % (attr, n, l))
    fhtml = "".join(parts)

    cards = [
        ("weddings.html", "tent-interior-lake-view.jpg",
         "Inside the clear tent with the tables set and Flathead Lake beyond", "Weddings",
         "The whole estate for a multi-day celebration &mdash; ceremony, cocktails and "
         "reception each in their own part of the property.",
         "See the wedding weekend"),
        ("retreats.html", "lounge-interior.jpg",
         "The pavilion lounge set for a small group", "Corporate &amp; Private Retreats",
         "A full-property buyout for leadership teams, boards and company gatherings. "
         "Everyone works, eats and sleeps in the same place.",
         "Plan a retreat"),
        ("estate.html", "treehouse-sunset.jpg",
         "A treehouse at sunset, the light coming through the pines", "The Estate",
         "Five places to sleep and the grounds between them &mdash; what your group "
         "has to itself.",
         "Tour the property"),
    ]
    chtml = "".join(f"""<a class="card" href="{h}">
        <div class="card__img">{img(i, a, sizes=SZ_THIRD)}</div>
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

  {marquee(["Lakeside, Montana", "Flathead Lake", "Glacier Country",
            "Weddings", "Retreats", "Wellness"])}

  <section class="sect">
    <div class="wrap">
      <div class="center rv" style="margin-bottom:clamp(3rem,6vw,4.5rem)">
        {eyebrow("Two ways to use the estate")}
        <h2>One property. No overlap.</h2>
        <p class="lede measure" style="margin-top:1.4rem">The estate becomes whatever
          the group booking it needs &mdash; a wedding weekend in July, a leadership
          offsite in October.</p>
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
        <h2 style="max-width:16ch">What our guests say</h2>
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
        "mind and we will tell you whether it is open.",
        btn("contact.html", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== WEDDINGS
def page_weddings():
    # Only what the ledger below does not already cover: each offering has one
    # home on this page (tools/repetition.py enforces it).
    included = [
        ("On the grounds", [
            "<b>15</b> private acres above Flathead Lake",
            "Estate grounds with walking trails",
            "Heated pool, hot tub, barrel sauna and putting green",
            "Fire pit for evening gatherings",
            "Starlink at the venue and in every house",
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
         "On the property, with four head tables."),
        ("Guest parking", "Arranged on site, or a shuttle from town.",
         "Parking for 75 cars on site."),
        ("Vendor access", "Depends on where a truck can reach.",
         "Load-in within 50 feet of the venue."),
        ("Where guests stay", "In town, travelling in each morning.",
         "On the property, a short walk from breakfast."),
    ]
    trows = "".join(
        f'<tr><th scope="row">{r}</th>'
        f'<td data-label="Elsewhere">{a}</td>'
        f'<td class="col-ours" data-label="The Overlook">{b}</td></tr>'
        for r, a, b in rows)

    spots = [
        (15, 54, "Arrival",
         "Guests park on the property",
         "No shuttle and no field: guests park on site, and the lake is in view "
         "from the moment they arrive.",
         "venue-overview.jpg", "The estate grounds and tent from the lawn"),
        (52, 17, "Ceremony",
         "The lawn faces the lake",
         "Chairs sit on the grass above the water, with trees on both sides. In the "
         "late afternoon the sun is behind your guests, not in their eyes.",
         "ceremony-aisle-view.jpg", "The aisle looking toward the water"),
        (55, 39, "The walk down",
         "A short walk down",
         "Ceremony and reception are a few minutes apart on foot, on the same "
         "hillside. Nobody needs a car between them.",
         "ceremony-tent-wide.jpg", "Ceremony seating with the tent below"),
        (84, 40, "Cocktails",
         "Drinks on the grounds",
         "The bar opens after the ceremony, and guests spread out across the "
         "lawn.",
         "bar-cheers-setup.jpg", "The built-in bar set for service"),
        (52, 68, "Reception",
         "Dinner under the tent",
         "Clear-top or white-top with full sides, set with the estate&rsquo;s own "
         "tables and chairs.",
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
      btn("contact.html", "Ask About Your Date", "btn btn--light btn--lg")
      + btn("#packages", "Explore Wedding Packages", "btn btn--outline-light btn--lg"),
      extra='<p class="hero__help">Share your dates and guest count. We&rsquo;ll reply personally with availability and package details.</p>',
      slides=[("ceremony-aisle-view.jpg", "The aisle looking toward the ceremony site"),
              ("venue-wide.jpg", "The estate grounds from across the lawn")],
      portrait=HERO_PORTRAIT["weddings.html"],
      )}

  {sectnav([("weekend", "Weekend"), ("film", "Watch"), ("your-weekend", "Your weekend"), ("included", "Included"), ("packages", "Packages"), ("lodging", "Lodging"), ("reviews", "Reviews"), ("faq", "FAQ")])}

  <section class="sect" id="weekend">
    <div class="wrap">
      {split(img("wedding-couple-arch.jpg", "A couple beneath the ceremony arch", sizes=SZ_HALF) ,
        f'''{eyebrow("Your wedding weekend")}
        <h2>The whole property is yours</h2>
        <p class="lede" style="margin:1.4rem 0">For the length of your booking the
          estate is closed to everyone but your guests. One wedding, and no other
          events on the property.</p>
        <p>The ceremony is on the lawn above the water. Cocktail hour is on the
          grounds. Dinner and dancing are in the pavilion and tent.</p>''',
        wide=True)}
    </div>
  </section>

  <section class="sect sect--tight" id="film">
    <div class="wrap">
      <div class="split split--film" style="align-items:center">
        <div class="split__media rv">
          {film("ceremony-lawn", "film-ceremony-lawn.jpg",
                "The ceremony lawn set for a wedding, with the trees and the lake beyond",
                "Thirty-five seconds on the property, set for a wedding.")}
        </div>
        <div class="split__body rv">
          {eyebrow("Watch")}
          <h2>Set, and waiting</h2>
          <p class="lede" style="margin:1.4rem 0">The ceremony lawn with the chairs out,
            then the tent with the tables laid &mdash; the trees, the lake behind them,
            and the quiet before anyone arrives.</p>
          <p>Tap to play. It is short, and it is the real place.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="sect sect--paper2" style="padding-block:clamp(3.5rem,8vw,6rem)">
    <div class="wrap">
      {vmap("wedding-aerial-tent.jpg",
            "Overhead view of the ceremony lawn and reception tent",
            "How the evening moves",
            "From the ceremony to the last dance",
            "Each part of the evening has its own place on the property. Select a "
            "marker to see where.",
            spots)}
    </div>
  </section>

  <section class="sect" id="your-weekend">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(1.6rem,4vw,2.6rem);max-width:54ch">
        {eyebrow("Your weekend")}
        <h2>Picture your wedding weekend</h2>
        <p class="lede" style="margin-top:1.2rem">This step is optional. Choose the moments you have in mind, then copy
          your selections into the inquiry form. You can also ask about dates
          without planning the weekend first.</p>
      </div>
      <div class="rv">{weekend_builder()}</div>
    </div>
  </section>

  <section class="sect sect--paper2" id="included">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:56ch">
        {eyebrow("What&rsquo;s included")}
        <h2>What comes with the venue</h2>
        <p class="lede" style="margin-top:1.4rem">Much of what a wedding needs usually
          has to be rented and delivered. Here the pavilion, tent, power and bar are
          permanent &mdash; line by line, against what it takes elsewhere.</p>
      </div>
      <div class="tbl-scroll rv">
        <table class="tbl">
          <thead><tr><th scope="col">&nbsp;</th><th scope="col">Arranged for the day</th>
            <th scope="col" class="col-ours">The Overlook</th></tr></thead>
          <tbody>{trows}</tbody>
        </table>
      </div>
      <div class="rv" style="margin-top:clamp(2.5rem,5vw,3.5rem)">
        <h3 style="margin-bottom:1.1rem">Also on the property</h3>
        {spec(included)}
      </div>
    </div>
  </section>

  <section class="sect sect--paper2" id="packages">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:50ch">
        {eyebrow("Packages")}
        <h2>Two ways to book the weekend</h2>
      </div>
      <div class="pkg">
        <div class="pkg__card rv">
          <h3>The Overlook Wedding</h3>
          <p class="pkg__meta">The estate, yours alone</p>
          <p style="color:var(--ink-soft);margin-bottom:1.6rem">Exclusive use of the
            estate for your celebration, with the venue infrastructure in place.</p>
          {plist(["Every venue space on the property, already standing",
                  "Ceremony, cocktail and reception areas",
                  "Your onsite venue coordinator",
                  "Lodging booked separately"])}
          {btn("overlook-wedding.html", "Explore This Package", "btn btn--ghost")}
        </div>
        <div class="pkg__card pkg__card--feature rv">
          {eyebrow("Signature")}
          <h3>The Ultimate Flathead Lake Wedding Weekend</h3>
          <p class="pkg__meta">Five nights, two estates</p>
          <p style="color:#CFCabd;margin-bottom:1.6rem">Two estates, one group, five
            nights. The wedding is at The Overlook, and
            <b style="font-weight:400;color:#fff">The Driftwood</b>, on the water at
            Woods Bay, gives more of your guests a place to stay.</p>
          {plist(["The Overlook &mdash; the pavilion, the tent and the grounds, yours alone",
                  "The Driftwood &mdash; 14,000 sq ft on the lake, private cove and boat slips",
                  "Sleeps 54 across both estates &mdash; 28 at The Overlook, 26 at The Driftwood",
                  "Helicopter transfer between them, through WestSlope",
                  "Planning support from the first call to the send-off"])}
          {btn("ultimate-wedding-weekend.html", "Explore This Package", "btn btn--light")}
        </div>
      </div>
    </div>
  </section>

  <section class="sect" id="lodging">
    <div class="wrap">
      {split(img("treehouse-deck-evening.jpg", "One of the two treehouses on its stilts in evening light", sizes=SZ_HALF),
        f'''{eyebrow("Onsite lodging")}
        <h2>Stay on the property</h2>
        <p class="lede" style="margin:1.4rem 0">Five accommodations sit on the same
          hillside as the ceremony lawn: a four-bedroom main house, a cabin, a pair of
          tiny homes and two treehouses.</p>
        <p>Getting ready happens here, and so does breakfast the next morning. Lodging
          is quoted separately from the venue fee.</p>
        <div style="margin-top:2rem">{tlink("estate.html", "See all five")}</div>''',
        flip=True)}
    </div>
  </section>

  <section class="sect sect--forest" id="reviews">
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
        [("tent-long-table-roses.jpg", "Long tables under the clear tent, set with white roses and candles",
          "White roses, the length of the table"),
         ("tent-interior-lake-view.jpg", "Inside the clear tent with the tables set and Flathead Lake beyond",
          "The lake, through the tent"),
         ("tent-from-lawn-ceremony.jpg", "The clear-top tent seen from the lawn below",
          "The tent from the lawn"),
         ("tent-exterior-sunflare.jpg", "The clear-top tent on its stone terrace in afternoon sun",
          "Afternoon on the terrace"),
         ("ceremony-setup.jpg", "Chairs set on the ceremony lawn before guests arrive",
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

  <section class="sect" id="faq">
    <div class="wrap wrap--narrow">
      <div class="rv" style="margin-bottom:2.5rem">
        {eyebrow("Questions")}
        <h2>Before you inquire</h2>
      </div>
      <div class="rv">{faq(faqs)}</div>
    </div>
  </section>

  {band("reception-mountain-view.jpg", "Reception tables set against the mountains",
        "Let&rsquo;s talk about your wedding",
        "Send your preferred dates and approximate guest count. We&rsquo;ll help you "
        "understand availability, package options and lodging for your guests.",
        btn("contact.html?type=wedding", "Ask About Your Date", "btn btn--light btn--lg"))}
"""



# ================================================================== PACKAGES
# One page per wedding package (owner's brief, 2026-09-28): the weddings page
# shows the two packages without prices; each "See the full experience" button
# opens its page, which carries the price, what is in it, and the weekend told
# in photographs. Facts are the ones the weddings page and the Driftwood block
# already state — nothing new is claimed here.

# The five houses as Flathead Lake Luxury Lodging rents them. Names, sleeping
# counts and the Compound / Full Estate groupings are copied from that site's
# content/properties.py (checked against the owner's Guesty listings on
# 2026-09-25); the photographs are the owner's own, from the same site.
LODGING_URL = "https://flatheadlakeluxurylodging.com/"
LODGING = [
    ("lodging-swan-house-exterior-drive.jpg", "The Swan House from the drive",
     "The Swan House &middot; sleeps 14"),
    ("lodging-swan-house-upper-deck-guests.jpg", "Guests on the Swan House's upper deck",
     "The Swan House, the upper deck"),
    ("lodging-glacier-house-exterior-lit.jpg", "The Glacier House lit up at dusk",
     "The Glacier House &middot; sleeps 4"),
    ("lodging-glacier-house-living-seating.jpg", "The living room in the Glacier House",
     "The Glacier House, inside"),
    ("lodging-lakeside-house-patio-guests.jpg", "The Lakeside House with its glass door open onto the patio",
     "The Lakeside House &middot; sleeps 4"),
    ("lodging-lakeside-house-bed-gold-accent-wall.jpg", "The Lakeside House bedroom and its gold accent wall",
     "The Lakeside House, inside"),
    ("summit-annalise-exterior.jpg", "The Summit treehouse and deck among the pines",
     "The Summit &middot; sleeps 3"),
    ("summit-annalise-open-living.jpg", "The Summit living area open to the trees",
     "The Summit, inside"),
    ("summit-annalise-bedroom.jpg", "The Summit bedroom", "The Summit, the bedroom"),
    ("summit-annalise-deck.jpg", "Dining and seating on the Summit deck", "The Summit, the deck"),
    ("lodging-the-ridge-exterior.jpg", "The Ridge treehouse on its stilts",
     "The Ridge &middot; sleeps 3"),
    ("lodging-the-ridge-king-bed.jpg", "The bedroom in The Ridge",
     "The Ridge, inside"),
]
LODGING_LINK = f'<a href="{LODGING_URL}" rel="noopener">Flathead Lake Luxury Lodging</a>'


def ask_btn(label, note, cls="btn btn--light btn--lg"):
    """An inquiry button that opens the sheet with the package named in the note."""
    return btn("contact.html?type=wedding", label, cls, note=note)


def pkg_summary(image, alt, price, lede, included):
    """The package block: photograph, starting price, one line, what is in it."""
    body = (f'{eyebrow("The package")}'
            f'<p class="pkg__price" style="margin-top:.4rem"><small>Starting at</small>{price}</p>'
            f'<p class="lede" style="margin:1.2rem 0 1.6rem">{lede}</p>'
            f'{plist(included)}')
    return f"""  <section class="sect" id="package">
    <div class="wrap">
      {split(img(image, alt, sizes=SZ_HALF), body, wide=True)}
    </div>
  </section>"""


def page_pkg_overlook():
    note = "Interested in: The Overlook Wedding package"
    included = ["The whole estate for your booking &mdash; one wedding, no other events",
                "The <b>3,200 sq ft</b> pavilion and the <b>40 &times; 80 ft</b> tent, "
                "clear-top or white-top with full sides",
                "Separate ceremony, cocktail and reception areas",
                "The built-in bar, the estate&rsquo;s tables and chairs, and four head tables",
                "<b>200 AMP</b> power and water on site; vendors load in within 50 feet",
                "Parking for 75 cars on the property",
                "Your onsite venue coordinator",
                "Up to <b>200</b> guests, with an 11:00 p.m. end",
                "The five houses on the property, booked separately through "
                "Flathead Lake Luxury Lodging"]
    day = [("ceremony-aisle-view.jpg", "The aisle on the ceremony lawn, looking toward the water",
            "Afternoon", "Vows on the lawn above the lake, with the trees on either side "
            "and the sun behind your guests."),
           ("bar-cheers-setup.jpg", "Glasses raised at the bar",
            "Early evening", "Drinks out on the grass while the tent is made ready; "
            "nobody is herded into a hallway."),
           ("tent-long-table-roses.jpg", "Long tables under the clear tent, set with white roses and candles",
            "Dinner", "The tables laid under the tent, the lake through the walls, and "
            "the light going gold."),
           ("evening-dinner-candlelight.jpg", "Dinner by candlelight after dark",
            "After dark", "Candles, speeches and the dance floor, until the end time your "
            "contract sets."),
           ("treehouse-sunset.jpg", "A treehouse at sunset, the light coming through the pines",
            "The morning after", "The people staying on the property wake up a short walk "
            "from where the night ended.")]
    return f"""
{hero("reception-mountain-view.jpg", "Reception tables set against the mountains",
      "Wedding package", "The Overlook Wedding",
      "The whole estate for your celebration, with everything a wedding needs "
      "already standing when you arrive.",
      ask_btn("Ask About This Package", note)
      + btn("weddings.html#packages", "Both Packages", "btn btn--outline-light btn--lg"),
      portrait=HERO_PORTRAIT["overlook-wedding.html"])}

{pkg_summary("tent-interior-lake-view.jpg",
             "Inside the clear tent with the tables set and Flathead Lake beyond",
             "$20,000",
             "Exclusive use of the estate, with the venue already built. The final figure "
             "depends on your dates and the shape of the weekend, so we quote it against both.",
             included)}

  <section class="sect sect--paper2">
    <div class="wrap">
      {film("ceremony-lawn", "film-ceremony-lawn.jpg",
            "The ceremony lawn set for a wedding, with the trees and the lake beyond",
            "Thirty-five seconds on the property, set for a wedding.")}
    </div>
  </section>

  {experiences("The day", "How the day moves",
               "From the first chair on the lawn to breakfast the next morning, all of it "
               "on one hillside.", day)}

  {rail("Where everyone stays", "Five houses, a short walk from the tent",
        f"Your wedding party can sleep on the property. The houses are booked through "
        f"our lodging company, {LODGING_LINK}: The Compound &mdash; the Swan, Glacier "
        f"and Lakeside houses, sleeping 22 &mdash; or The Full Estate, all five, "
        f"sleeping 28.", LODGING)}

  <section class="sect sect--forest">
    <div class="wrap wrap--narrow">
      {quote(*R_OLIVIA)}
    </div>
  </section>

  {band("tent-exterior-sunflare.jpg", "The clear-top tent on its stone terrace in afternoon sun",
        "Hold your date",
        "Tell us the weekend you have in mind and we will tell you honestly whether it "
        "is open.",
        ask_btn("Ask About This Package", note))}
"""


def page_pkg_ultimate():
    note = "Interested in: The Ultimate Flathead Lake Wedding Weekend"
    included = ["<b>Five nights</b> across two estates, for one group",
                "The Overlook &mdash; the pavilion, the tent and the grounds, yours alone "
                "for the wedding",
                "The Driftwood &mdash; a <b>14,000 sq ft</b> lakefront home at Woods Bay "
                "with <b>7</b> bedrooms, <b>9</b> baths, a private cove and boat slips",
                "Room for <b>54</b> to stay: 28 across The Overlook&rsquo;s five houses, "
                "26 at The Driftwood",
                "Helicopter transfer between the two, through WestSlope",
                "Planning support from the first call to the send-off"]
    heli_body = (f'{eyebrow("Between the two")}'
                 '<h2>Twenty minutes by road, a few by air</h2>'
                 '<p class="lede" style="margin:1.4rem 0">The estates are about twenty '
                 'minutes apart around the lake. WestSlope can fly your group between '
                 'them, so the rehearsal dinner can be at one and the last night at the '
                 'other.</p>')
    tiles = "".join(
        f'<div class="card rv"><div class="card__img" style="aspect-ratio:4/5">'
        f'{img(f, a, sizes=SZ_THIRD)}</div></div>'
        for f, a in [("tent-interior-lake-view.jpg", "Inside the clear tent with Flathead Lake beyond"),
                     ("ceremony-aisle-view.jpg", "The aisle on the ceremony lawn"),
                     ("tent-long-table-roses.jpg", "Long tables set with white roses under the tent")])
    return f"""
{hero("driftwood-exterior-dusk.jpg", "The Driftwood from the water at dusk",
      "Signature package", "The Ultimate Flathead Lake<br>Wedding Weekend",
      "Five nights, two estates, one group &mdash; the wedding up on the hill at The "
      "Overlook, and The Driftwood down on the water.",
      ask_btn("Ask About This Package", note)
      + btn("weddings.html#packages", "Both Packages", "btn btn--outline-light btn--lg"))}

{pkg_summary("driftwood-great-room.jpg", "The Driftwood's great room, opening to the lake",
             "$135,000",
             "The whole of The Overlook for the celebration and a lakefront home for the "
             "people closest to you, under one booking.",
             included)}

  <section class="sect sect--paper2">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2rem,4vw,3rem);max-width:54ch">
        {eyebrow("The Driftwood")}
        <h2>Down on the water at Woods Bay</h2>
        <p class="lede" style="margin-top:1.2rem">Where the wedding party wakes up: the
          great room opens to the lake, the dock runs out to the boat slips, and the
          deck looks straight down the water.</p>
      </div>
      {slideshow(DRIFTWOOD_SHOTS, "Photographs of The Driftwood")}
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      {split(img("heli-new.jpg", "A helicopter over the Flathead valley", sizes=SZ_HALF),
             heli_body, flip=True)}
    </div>
  </section>

  <section class="sect sect--paper2">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2rem,4vw,3rem);max-width:54ch">
        {eyebrow("The Overlook")}
        <h2>Up on the hill, for the wedding itself</h2>
      </div>
      <div class="cards cards--3 cards--tiles">{tiles}</div>
      <div class="rv" style="margin-top:2rem">{tlink("overlook-wedding.html", "See The Overlook Wedding")}</div>
    </div>
  </section>

  {rail("Where everyone stays", "The five houses up on the hill",
        f"While the closest family takes The Driftwood, the rest of the party sleeps in "
        f"the estate&rsquo;s houses, which our lodging company, {LODGING_LINK}, runs "
        f"the rest of the year.", LODGING)}

  {band("driftwood-dock-slips.jpg", "The Driftwood's dock and private boat slips",
        "Both estates, one weekend",
        "Availability for the two estates is separate, so ask early if you want them "
        "on the same dates.",
        ask_btn("Ask About This Package", note))}
"""


# ================================================================== RETREATS
def page_retreats():
    why = [
        ("Total exclusivity",
         "The entire fifteen-acre estate is booked for your group alone. For the "
         "length of your booking, every building and every acre belongs to you."),
        ("Everyone stays where you meet",
         "Your team works, eats and stays in the same place. The conversation carries "
         "from the pavilion to dinner to the fire pit, and nobody has to drive "
         "anywhere."),
        ("A place people want to travel to",
         f"Flathead Lake is out the window, and Whitefish and {GLACIER['name']} are "
         f"close enough to extend the trip."),
        ("Built as a venue",
         "The meeting space, the power, the internet and the grounds are permanent, "
         "so nothing has to be brought in for your week."),
    ]
    whyhtml = "".join(
        f'<div class="rv"><h3>{t}</h3><p style="color:var(--ink-soft);margin-top:.9rem">{d}</p></div>'
        for t, d in why)

    space = [
        ("The Pavilion", "hero-pavilion-lake.jpg", "The pavilion looking out over Flathead Lake",
         "3,200 sq ft with panoramic lake views and dimmable lighting, adaptable from a "
         "full-group general session to a seated dinner. The tent runs clear-top or "
         "fully enclosed white-top with sides, so spring and fall work too."),
        ("The Main House &mdash; The Swan", "swan-game-room.jpg", "The game room in the Swan",
         "Three levels with a gourmet kitchen, a full bar, a game room and lake-view "
         "balconies. It works well for breakout groups and evenings."),
        ("The Grounds", "pool-wide.jpg", "The heated pool and cabana above the lake",
         "Heated pool and cabana, hot tub, barrel sauna, fitness room, fire pit, putting "
         "green, lawn games and walking trails for the hours between sessions."),
        ("Connectivity", "swan-kitchen-new.jpg", "The kitchen in the Swan",
         "Starlink is installed in every house and at the venue, so people can stay "
         "on calls and keep working."),
    ]
    spacehtml = ""
    for i, (t, im, alt, d) in enumerate(space):
        spacehtml += f"""<div class="spaces__item">{split(
            img(im, alt, sizes=SZ_HALF),
            f'<h3>{t}</h3><p style="color:var(--ink-soft);margin-top:1.1rem;font-size:1.05rem;line-height:1.7">{d}</p>',
            flip=bool(i % 2))}</div>"""

    formats = [
        ("Leadership / Executive Retreat", "Multi-night &middot; full estate",
         "The whole group stays on the property. This is what the estate suits "
         "best."),
        ("Board or Strategy Retreat", "Two to three nights &middot; full estate",
         "A smaller group, with the pavilion held for working sessions and the houses "
         "for everything else."),
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
        "Any team that wants to get real work done somewhere new",
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

  {sectnav([("why", "Why"), ("space", "The space"), ("formats", "Formats"), ("rates", "Rates"), ("reviews", "Reviews"), ("faq", "FAQ")])}

  <section class="sect" id="why">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.8rem,6vw,4.5rem);max-width:54ch">
        {eyebrow("Why teams choose the Overlook")}
        <h2>The whole estate, for your team only</h2>
      </div>
      <div class="cards cards--2" style="gap:clamp(2.2rem,4vw,3.5rem)">{whyhtml}</div>
    </div>
  </section>

  <section class="sect sect--paper2" id="space">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.8rem,6vw,4.5rem);max-width:50ch">
        {eyebrow("The space")}
        <h2>What your group has to work with</h2>
      </div>
      <div class="spaces">{spacehtml}</div>
      <div class="rv" style="border-top:1px solid var(--line);padding-top:2.5rem">
        <h3 style="margin-bottom:1.3rem">Logistics</h3>
        {ilist(["200 AMP electrical service",
                "On-site water",
                "Parking for 75 cars",
                "Vendor and load-in access within 50 feet of the venue"])}
      </div>
    </div>
  </section>

  <section class="sect" id="formats">
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
      {split(img("lounge-interior.jpg", "Lounge seating inside the pavilion", sizes=SZ_HALF),
        f'''{eyebrow("Who it is for")}
        <h2>Who it suits</h2>
        <div style="margin-top:1.8rem">{plist(who)}</div>''')}
    </div>
  </section>

  <section class="sect">
    <div class="wrap">
      {split(img("heli-new.jpg", "A helicopter over the Flathead valley", sizes=SZ_HALF),
        f'''{eyebrow("Getting here")}
        <h2>Easy to reach</h2>
        <p class="lede" style="margin:1.4rem 0">{FCA["short_name"]} is {FCA["time"]}
          away by car. A team on a morning flight can be working by the
          afternoon.</p>
        <p>{GLACIER["name"]} is {GLACIER["time"]} out for groups extending the
          trip.</p>''',
        flip=True)}
    </div>
  </section>

  <section class="sect sect--forest" id="rates">
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
        <div class="split__media rv rv--wipe">{img("barrel-sauna.jpg", "The cedar barrel sauna", sizes=SZ_HALF)}</div>
        <div class="split__body rv">
          {eyebrow("Also here")}
          <h2>Wellness retreats</h2>
          <p class="lede" style="margin-top:1.3rem">The estate also hosts yoga,
            movement and recovery retreats, with the pavilion as open floor space and
            the heat and water a few steps away.</p>
          {tlink("wellness.html", "See wellness retreats")}
        </div>
      </div>
    </div>
  </section>

  {experiences(
      "Food and time off the clock",
      "How the group eats, and what it does after",
      "Tell us how you want the group fed and what you want to do between sessions, "
      "and we will help you arrange it.",
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
        "Grazing tables, working lunches, and the built-in bar for the evenings."),
       ("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate",
        "On the lake",
        "Flathead Lake is minutes down the hill, with boating, swimming and sunset "
        "cruises."),
       ])}

  {driftwood(DRIFTWOOD_SHOTS, "retreat")}

  <section class="sect sect--forest" id="reviews">
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

  <section class="sect" id="faq">
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
         "full bar, a game room and balconies facing the water. It is the largest house "
         "on the property, and where groups tend to gather."),
        ("The Glacier", "Modern cabin", "glacier-exterior.jpg",
         "The Glacier cabin among the trees",
         "A two-storey cabin in dark board-and-batten under a single sloping roof, with "
         "a sleeping loft and a private patio, set back from the main house for some "
         "privacy."),
        ("The Lakeside", "Two modern tiny homes", "lakeside-both-homes.jpg",
         "The two Lakeside tiny homes side by side",
         "A pair of modern tiny homes, each with a full bath, a loft and a view down "
         "toward the water."),
        # one tab for both, as The Lakeside is for the two tiny homes; the new
        # photographs are of the treehouses but not labelled by building. The
        # wording is main's fact-corrected copy (2026-09-28), joined.
        ("The Treehouses", "The Summit &amp; The Ridge", "treehouse-sunset.jpg",
         "A treehouse at sunset, the light coming through the pines",
         "Two treehouses: The Summit, raised up among the trees, and The Ridge, set "
         "along the ridge line with its own deck."),
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
        "The Treehouses": [
            ('summit-annalise-exterior.jpg', 'The Summit treehouse and its deck among the pines'),
            ('summit-annalise-bedroom.jpg', 'The Summit bedroom with the bathroom beyond'),
            ('summit-annalise-open-living.jpg', 'The Summit living area with its glass door raised to the trees'),
            ('summit-annalise-bathroom.jpg', 'The Summit bathroom with its vanity and glass shower'),
            ('summit-annalise-deck.jpg', 'Dining table and lounge chairs on the Summit deck'),
            ('ridge-annalise-lake-aerial.jpg', 'The treehouses among the pines with Flathead Lake beyond'),
            ('ridge-exterior.jpg', 'The Ridge treehouse at the edge of the trees'),
            ('lodging-the-ridge-king-bed.jpg', 'The bedroom in The Ridge'),
            ('treehouse-sauna-evening.jpg', 'A treehouse and the cedar barrel sauna at golden hour'),
        ],
    }
    hhtml = switcher(
        "Where everyone sleeps",
        "Choose a building",
        "Look through each one. Every building is a short walk from the pavilion.",
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
        <div class="card__img" style="aspect-ratio:1/1">{img(im, alt, sizes=SZ_THIRD)}</div>
        <h4 style="font-family:var(--sans);font-size:.78rem;letter-spacing:.16em;text-transform:uppercase;font-weight:400">{t}</h4>
      </div>""" for t, im, alt in grounds)

    return f"""
{hero("meadow-evening-light.jpg", "Evening light across the meadow, with the accommodations among the pines",
      "The Estate", "Five places to sleep,<br>fifteen acres to use",
      "Where your group sleeps, and what is on the grounds.", short=True)}

  <section class="sect">
    <div class="wrap wrap--narrow center rv">
      <h2>Twenty-eight people, one property</h2>
      <p class="lede" style="margin-top:1.4rem">The estate sleeps 28 across five separate
        accommodations. Nobody has to drive between them.</p>
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
      <div class="cards cards--3 cards--tiles">{ghtml}</div>
      <div class="rv" style="margin-top:clamp(2.5rem,5vw,3.5rem);border-top:1px solid var(--line);padding-top:2.5rem">
        {ilist(["Walking trails across the property",
                "Starlink internet in every house and at the venue",
                "200 AMP electrical service and on-site water",
                "Parking for 75 cars",
                "3,200 sq ft pavilion and 40&times;80 ft tent",
                "Vendor and load-in access within 50 feet of the venue"])}
      </div>
    </div>
  </section>

  {band("lake-sunset-boat.jpg", "The lake at sunset from the estate",
        "See it for yourself",
        "Tell us your dates and we will walk you through the property and how it "
        "would work for your group.",
        btn("contact.html", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== GALLERY
# (file, alt, category) — category: weddings | estate | grounds
PHOTOS = [
    # Owner-provided J. Annalise photography: distinct interiors and setting.
    ('summit-annalise-exterior.jpg', 'The Summit treehouse and its deck among the pines', 'estate'),
    ('summit-annalise-bedroom.jpg', 'The Summit bedroom with the bathroom beyond', 'estate'),
    ('summit-annalise-open-living.jpg', 'The Summit living area with its glass door raised to the trees', 'estate'),
    ('summit-annalise-bathroom.jpg', 'The Summit bathroom with its vanity and glass shower', 'estate'),
    ('summit-annalise-deck.jpg', 'Dining table and lounge chairs on the Summit deck', 'estate'),
    ('ridge-annalise-lake-aerial.jpg', 'The treehouses among the pines with Flathead Lake beyond', 'estate'),

    # added 2026-09-28 from the new shoot — these open the gallery
    ("tent-interior-lake-view.jpg", "Inside the clear tent with the tables set and Flathead Lake beyond", "weddings"),
    ("treehouse-sunset.jpg", "A treehouse at sunset, the light coming through the pines", "estate"),
    ("tent-long-table-roses.jpg", "Long tables under the clear tent, set with white roses and candles", "weddings"),
    ("meadow-evening-light.jpg", "Evening light across the meadow, with the accommodations among the pines", "grounds"),
    ("tent-from-lawn-ceremony.jpg", "The clear-top tent seen from the lawn below", "weddings"),
    ("treehouse-deck-evening.jpg", "One of the two treehouses on its stilts in evening light", "estate"),
    ("tent-exterior-sunflare.jpg", "The clear-top tent on its stone terrace in afternoon sun", "weddings"),
    ("treehouse-sauna-evening.jpg", "A treehouse and the cedar barrel sauna at golden hour", "estate"),
    ("tent-side-rock-wall.jpg", "The tent with its sides down, behind the boulder wall", "weddings"),
    ("treehouses-among-pines.jpg", "The treehouses among the pines in evening light", "estate"),
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
        f'<figure class="rv" data-cat="{cat}" data-full="{IMG}{f}" data-stem="{f.rsplit(".", 1)[0]}">'
        f'{img(f, alt, thumb=True, sizes=SZ_GALLERY)}</figure>'
        for f, alt, cat in PHOTOS)

    return f"""
  <section class="sect sect--tight" style="padding-top:clamp(8rem,14vw,11rem)">
    <div class="wrap center rv">
      {eyebrow("Gallery")}
      <h1 style="font-size:clamp(2rem,4.2vw,3.35rem)">Photographs of the estate</h1>
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
        "Photos only show so much. Tell us your dates and we will show you around "
        "in person.",
        btn("contact.html", "Start Your Inquiry", "btn btn--light btn--lg"))}
"""


# ================================================================== STORY
def page_story():
    return f"""
{hero("owners-photo.jpg", "Claudia and Eric on the estate", "Our Story",
      "Claudia &amp; Eric", "The owners, and how the venue came to be.", short=True)}

  <section class="sect">
    <div class="wrap wrap--narrow rv">
      <p class="lede">We started with rental houses. In 2021 we began hosting guests on
        Flathead Lake as Flathead Lake Luxury Lodging, and over four years we learned
        what a group needs when they take over a property for a weekend.</p>
      <p style="margin-top:1.6rem">Guests kept booking our houses for weddings and
        family celebrations, then renting a tent, power and a bar from separate
        vendors to hold the event somewhere else.</p>
      <p>So in 2025 we built the venue on the same fifteen acres as the houses: the
        pavilion, the tent, permanent power, the bar and parking. Now the celebration
        and the place everyone sleeps are in the same spot.</p>
      <p>We book one group at a time, so the whole property is always yours.</p>
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
      {split(img("vendor-appreciation-wall.jpg", "The vendor appreciation wall on the estate", sizes=SZ_HALF),
        '''<h2>The people we work with</h2>
        <p class="lede" style="margin:1.4rem 0">We work with a short list of Flathead
          Valley planners, caterers, florists and photographers who know the property,
          and several offer a partner discount to our couples.</p>
        <p>You are never required to book from that list. It is there to save you
          time.</p>''',
        flip=True)}
    </div>
  </section>

  {band("lake-sunset-boat.jpg", "The lake at sunset",
        "Come and see it",
        "Send us your dates and we will write back personally.",
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
            and the shape of the gathering. Every inquiry is answered
            personally, usually within one business day.</p>

          <div style="margin-top:3rem;border-top:1px solid var(--line);padding-top:2rem">
            <h4 style="font-family:var(--sans);font-size:.72rem;letter-spacing:.17em;text-transform:uppercase;color:var(--muted);font-weight:400;margin-bottom:1.2rem">Direct</h4>
            {plist([f'<a href="mailto:{BIZ["email"]}" style="text-decoration:none">{BIZ["email"]}</a>',
                    f'{BIZ["city"]}, {BIZ["state"]}',
                    f'<a href="{BIZ["ig"]}" rel="noopener" style="text-decoration:none">Instagram {BIZ["handle"]}</a>'])}
          </div>

          <div style="margin-top:2.5rem;border-top:1px solid var(--line);padding-top:2rem">
            <h4 style="font-family:var(--sans);font-size:.72rem;letter-spacing:.17em;text-transform:uppercase;color:var(--muted);font-weight:400;margin-bottom:1.2rem">Getting here</h4>
            <p style="color:var(--ink-soft);font-size:.98rem">Lakeside, Montana &mdash;
              {FCA["time"]} from {FCA["name"]}, {WHITEFISH["time"]} from
              {WHITEFISH["name"]} and {GLACIER["time"]} from {GLACIER["entrance"]}.</p>
          </div>
        </div>

        <div class="rv">{hb_form(inline=True)}</div>
      </div>
    </div>
  </section>

  {getting_here()}
"""



# The inquiry form is HoneyBook's own (shell.hb_form): inline here, and in the
# window every other page opens from its inquiry buttons.



# ================================================================== WELLNESS
def page_wellness():
    cards = [
        ("hero-pavilion-lake.jpg", "The empty pavilion looking out over Flathead Lake",
         "Room to move",
         "The pavilion is 3,200 sq ft under cover, facing the lake, with open floor "
         "for mats. You can leave it set up all week. The tent also closes fully with "
         "sides for cooler months."),
        ("barrel-sauna.jpg", "The cedar barrel sauna",
         "Heat and cold",
         "A cedar barrel sauna, a hot tub and a heated pool, a few steps from each "
         "other and yours whenever you want them."),
        ("pool-house-gym.jpg", "The fitness room in the pool house",
         "The fitness room",
         "A fitness room in the pool house, open whenever your group wants to "
         "train."),
        ("venue-overview.jpg", "The estate grounds from above",
         "Fifteen acres to walk",
         "Walking trails across the property, and Flathead Lake a few minutes down "
         "the hill."),
        ("swan-kitchen-new.jpg", "The kitchen in the Swan",
         "Food that fits the week",
         "A private chef can cook to your group&rsquo;s needs, whether that is "
         "plant-based, high-protein or an early breakfast. Caterers can cover the whole "
         "stay instead."),
        ("pool-loungers.jpg", "Loungers along the pool deck",
         "Just your group",
         "No other guests and no front desk. You set the schedule."),
    ]
    chtml = "".join(
        f'<div class="exp__card"><div class="exp__img">{img(f, a, sizes=SZ_THIRD)}</div>'
        f'<h3>{t}</h3><p>{d}</p></div>' for f, a, t, d in cards)

    # the cards above already describe the pavilion, heat and water, fitness
    # room, trails and food; this is only what they leave out
    spec_groups = [
        ("On the property", [
            "<b>40 &times; 80 ft</b> tent &mdash; clear-top or enclosed with sides",
            "Fire pit",
            "Starlink at the venue and in every house",
        ]),
        ("Getting here", [
            f"<b>{FCA['brief']}</b> from {FCA['short_name']}",
            f"<b>{GLACIER['brief']}</b> to {GLACIER['entrance']}, the park&rsquo;s west entrance",
        ]),
    ]

    faqs = FAQ_WELLNESS

    return f"""
{hero("pool-wide.jpg",
      "The heated pool and terrace above Flathead Lake",
      "Wellness Retreats",
      "A private estate<br>for wellness retreats",
      "Fifteen private acres above Flathead Lake, for yoga, movement and recovery "
      "retreats.",
      btn("contact.html?type=wellness", "Check Availability", "btn btn--light btn--lg")
      + btn("#what", "What Is Here", "btn btn--outline-light btn--lg"),
      slides=[("pool-hottub-wide.jpg", "The pool and hot tub on the terrace"),
              ("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate")])}

  {sectnav([("why", "Why here"), ("what", "What is here"), ("detail", "The detail"), ("reviews", "Reviews"), ("faq", "FAQ")])}

  <section class="sect" id="why">
    <div class="wrap">
      <div class="rv" style="max-width:56ch">
        {eyebrow("Why here")}
        <h2>What a retreat needs, in one place</h2>
        <p class="lede" style="margin-top:1.4rem">A room you can keep set up all week,
          heat and water close by, and food cooked for your group.</p>
        <p style="color:var(--ink-soft);max-width:62ch">We book one group at a time,
          so all of it is yours for the whole stay.</p>
      </div>
    </div>
  </section>

  <section class="sect sect--paper2" id="what">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:52ch">
        {eyebrow("What is here")}
        <h2>What is on the property</h2>
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

  <section class="sect sect--paper2" id="detail">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:50ch">
        {eyebrow("The detail")}
        <h2>Everything the week can use</h2>
      </div>
      {spec(spec_groups)}
    </div>
  </section>

  <section class="sect sect--forest" id="reviews">
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

  <section class="sect" id="faq">
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
        "Send the dates and the shape of the retreat and we will tell you "
        "whether the estate is open and whether it suits.",
        btn("contact.html?type=wellness", "Check Availability", "btn btn--light btn--lg"))}
"""


# ============================================================ ported pages
# Six URLs that already exist and are already indexed on the live site:
# /privacy /terms /journal and three /journal/<slug> articles. They are ported
# here so the rebuild does not delete them, and they keep their URLs exactly —
# hence the directory-index output paths.
#
# The ports are faithful except where the live text is out of date or
# contradicts FACTS.md. Every such change is marked below and listed in the
# handover; nothing new was invented to fill a gap.

LEGAL_UPDATED = "September 2026"     # this revision, not the January original


def dcrumb(base, trail):
    """Visible breadcrumb. trail: [(label, href_or_None), …] after Home.

    The BreadcrumbList in the page's structured data says the same thing; this
    is the version a reader can click.
    """
    parts = [f'<a href="{base}index.html">Home</a>']
    for label, href in trail:
        parts.append(f'<a href="{base}{href}">{label}</a>' if href
                     else f'<span>{label}</span>')
    # a class, not only inline styles, so the touch-target rules can reach it
    return ('<p class="dcrumb">' + ' &rsaquo; '.join(parts) + '</p>')


def doc_head(base, eyeb, h1, lede, trail=()):
    """Opening block for a page with no hero photograph."""
    crumb = dcrumb(base, trail) if trail else ""
    return f"""
  <section class="sect sect--tight" style="padding-top:clamp(8rem,14vw,11rem)">
    <div class="wrap wrap--narrow rv">
      {crumb}{eyebrow(eyeb)}
      <h1 style="font-size:clamp(2.1rem,4.4vw,3.3rem);margin-top:1.1rem">{h1}</h1>
      <p class="lede" style="margin-top:1.5rem">{lede}</p>
    </div>
  </section>"""


def legal_body(sections):
    """sections: (heading, [paragraph_or_list_html, …])"""
    out = []
    for i, (h, blocks) in enumerate(sections, start=1):
        inner = "".join(blocks)
        out.append(f"""<div class="rv" style="margin-top:2.8rem">
          <h2 style="font-size:clamp(1.15rem,2vw,1.45rem)">{i}. {h}</h2>
          <div style="margin-top:1rem;color:var(--ink-soft)">{inner}</div>
        </div>""")
    return f"""
  <section class="sect" style="padding-top:0">
    <div class="wrap wrap--narrow">{"".join(out)}</div>
  </section>"""


def page_privacy(base):
    # Ported from /privacy. Two changes from the live text, both deliberate:
    #   - section 10, "Sweepstakes Data Collection", is gone, along with the
    #     giveaway bullet in section 2 and the Official Rules link in the
    #     contact section. The Signature Wedding Experience Giveaway closed on
    #     2026-03-25 and was drawn on 2026-03-27; republishing a live entry
    #     route for it would be a false statement. Sections renumbered.
    #   - the contact address is BIZ["email"], not the Hello@ address on the
    #     live page, so a deletion request reaches a monitored mailbox.
    s = [
        # REWRITTEN 2026-09-28 for the native inquiry sheet: the form is now
        # ours, and the relay in worker/ is the only server-side code the site
        # has. Say exactly where an inquiry goes and for how long.
        ("Information We Collect",
         ["<p>These pages are static. This website has no database and no user "
          "accounts, and reading it sends us nothing.</p>",
          "<p>The inquiry form &mdash; on the contact page, and in the window the "
          "inquiry buttons open on every other page &mdash; is HoneyBook&rsquo;s own "
          "form, embedded here. HoneyBook is the client-management service we run "
          "the business on. What you enter goes straight to HoneyBook and reaches us "
          "as an inquiry there. The form asks for:</p>",
          ilist(["Name", "Email address", "Phone number", "Preferred event dates",
                 "Estimated guest count",
                 "Any additional information you provide in your message"]),
          "<p>If you would rather email, we hold what you send in our "
          "mailbox instead.</p>"]),
        ("How We Use Your Information",
         ["<p>We use the information you provide to:</p>",
          ilist(["Respond to your venue inquiry",
                 "Provide information about our services and availability",
                 "Send relevant updates about " + BIZ["name"],
                 "Improve our website and services"])]),
        # REWRITTEN: the processor is now named rather than implied.
        ("Information Sharing",
         ["<p>We do not sell, trade, or otherwise transfer your personal "
          "information to outside parties.</p>",
          "<p>Your inquiry does sit with the providers we use to run the business: "
          "HoneyBook, which hosts the inquiry form and holds the inquiry itself, and "
          "the email provider behind the address on this site. Each is bound to "
          "handle it confidentially and to use it only to provide that service to "
          "us.</p>"]),
        ("Data Security",
         ["<p>We implement appropriate security measures to protect your personal "
          "information against unauthorized access, alteration, disclosure, or "
          "destruction. All data is stored securely and access is restricted to "
          "authorized personnel only.</p>"]),
        ("Cookies and Tracking",
         ["<p>We use the Meta Pixel to measure page visits and advertising performance, "
          "build audiences for advertising on Facebook and Instagram, and support "
          "retargeting. Meta receives information about the pages you visit, your "
          "IP address, browser and device, and cookie identifiers. The pixel uses "
          "first-party cookies and may associate activity with your Meta account. "
          "See <a href='https://www.facebook.com/privacy/policy/' rel='noopener'>Meta&rsquo;s "
          "Privacy Policy</a> for information about its use of this data.</p>",
          ("<p>We also use Cloudflare Web Analytics to count page views without "
           "analytics cookies.</p>" if CF_ANALYTICS_TOKEN else ""),
          "<p>One thing is kept in your browser: if you dismiss the inquiry bar at "
          "the foot of the page, that choice is stored in your browser&rsquo;s "
          "session storage so the bar stays closed. Your browser discards it when "
          "you close the tab, and it never leaves your device.</p>",
          "<p>The typefaces are served from this site, not from Google, so reading "
          "a page does not load Google Fonts. Alongside Meta, the following third "
          "parties provide embedded content. When that content loads, each receives your IP "
          "address and basic browser information and may set cookies of its own "
          "under its own policy, which we neither control nor read:</p>",
          ilist(["<b>HoneyBook</b> (hbportal.co), for the inquiry form &mdash; on the "
                 "contact page, and elsewhere only once you open the inquiry window.",
                 "<b>Google Maps</b>, on the contact page only, for the map of "
                 "Lakeside."]),
          "<p>You can manage cookies in your browser and advertising preferences in "
          "your Meta account. Blocking Meta tracking does not prevent browsing or "
          "sending an inquiry. If embedded content is blocked, you can contact us "
          "by email instead.</p>"]),
        ("Third-Party Links",
         ["<p>Our website may contain links to third-party websites. We are not "
          "responsible for the privacy practices of these external sites and "
          "encourage you to review their privacy policies.</p>"]),
        ("Your Rights",
         ["<p>You have the right to:</p>",
          ilist(["Access the personal information we hold about you",
                 "Request correction of inaccurate information",
                 "Request deletion of your personal information",
                 "Opt out of marketing communications"])]),
        ("Children&rsquo;s Privacy",
         ["<p>Our website and services are not directed to individuals under the age "
          "of 18. We do not knowingly collect personal information from children.</p>"]),
        ("Changes to This Policy",
         ["<p>We may update this Privacy Policy from time to time. Changes will be "
          "posted on this page with an updated revision date. We encourage you to "
          "review this policy periodically.</p>"]),
        ("Contact Us",
         ["<p>If you have questions about this Privacy Policy or wish to exercise "
          "your rights regarding your personal data, please contact us:</p>",
          f'<p style="margin-top:1rem">Email: <a href="mailto:{BIZ["email"]}">'
          f'{BIZ["email"]}</a><br>Location: {BIZ["city"]}, {BIZ["region"]}</p>']),
    ]
    return (doc_head(base, f"Last updated: {LEGAL_UPDATED}", "Privacy Policy",
                     "How we collect, use and protect the information you send us "
                     "when you inquire about the estate.",
                     trail=[("Privacy Policy", None)])
            + legal_body(s))


def page_terms(base):
    # Ported from /terms. Section 3, the Signature Wedding Experience Giveaway,
    # is gone for the same reason as the privacy section above: the entry period
    # ended 2026-03-25 and the drawing was held 2026-03-27. Sections renumbered.
    # Contact address is BIZ["email"] rather than the live Hello@ address.
    s = [
        ("Acceptance of Terms",
         ["<p>By accessing and using " + BIZ["name"] + " website and services, you "
          "agree to be bound by these Terms of Service. If you do not agree to these "
          "terms, please do not use our services.</p>"]),
        ("Venue Rental Services",
         ["<p>" + BIZ["name"] + " is a private estate wedding venue available "
          "exclusively through private inquiry. All bookings are subject to "
          "availability and require a signed rental agreement.</p>",
          ilist(["All venue rental inquiries are subject to review and approval",
                 "Starting prices are published on this site; a full quote is "
                 "shared after an initial conversation",
                 "A signed contract and deposit are required to confirm any booking",
                 "Cancellation policies are outlined in the rental agreement"])]),
        ("User Conduct",
         ["<p>When using our website and services, you agree to:</p>",
          ilist(["Provide accurate and truthful information",
                 "Not use the site for any unlawful purpose",
                 "Not attempt to interfere with the proper functioning of the website",
                 "Not submit false or misleading information"])]),
        ("Intellectual Property",
         ["<p>All content on this website, including images, text, graphics, and "
          "logos, is the property of " + BIZ["name"] + " or its licensors and is "
          "protected by copyright laws. You may not reproduce, distribute, or use "
          "any content without prior written permission.</p>"]),
        ("Limitation of Liability",
         ["<p>" + BIZ["name"] + " shall not be liable for any indirect, incidental, "
          "special, or consequential damages arising from your use of our website or "
          "services. Our total liability shall not exceed the amount paid for "
          "services.</p>"]),
        ("Changes to Terms",
         ["<p>We reserve the right to modify these terms at any time. Changes will be "
          "effective immediately upon posting. Your continued use of the website "
          "constitutes acceptance of the modified terms.</p>"]),
        ("Governing Law",
         ["<p>These terms shall be governed by the laws of the State of Montana. Any "
          "disputes shall be resolved in the courts of Flathead County, Montana.</p>"]),
        ("Contact Information",
         ["<p>For questions about these Terms of Service, please contact us at:</p>",
          f'<p style="margin-top:1rem">Email: <a href="mailto:{BIZ["email"]}">'
          f'{BIZ["email"]}</a><br>Location: {BIZ["city"]}, {BIZ["region"]}</p>']),
    ]
    return (doc_head(base, f"Last updated: {LEGAL_UPDATED}", "Terms of Service",
                     "The terms that apply to this website and to an inquiry made "
                     "through it.",
                     trail=[("Terms of Service", None)])
            + legal_body(s))


# ---------------------------------------------------------------- the journal
# Three articles ported from /journal. Facts were checked against FACTS.md
# rather than carried over on trust; the three corrections are marked CORRECTED
# and are listed in the handover.

A_BUYOUT, A_SEASON, A_TRAVEL = (
    "whats-included-estate-buyout-wedding-venue",
    "best-time-of-year-montana-lake-wedding",
    "getting-to-the-overlook-travel-guide")


def art_body(paras):
    """Article prose. paras: html strings, already marked up."""
    return f"""
  <section class="sect" style="padding-top:0">
    <div class="wrap wrap--narrow">{"".join(paras)}</div>
  </section>"""


def h2(t):
    return f'<h2 class="rv" style="font-size:clamp(1.5rem,2.8vw,2.1rem);margin-top:3rem">{t}</h2>'


def para(t):
    return f'<p class="rv" style="margin-top:1.3rem;color:var(--ink-soft)">{t}</p>'


def blist(items):
    return f'<div class="rv" style="margin-top:1.3rem">{ilist(items)}</div>'


def related(base, slugs):
    li = "".join(
        f'<li style="margin-bottom:.9rem"><a class="tlink" href="{base}journal/{sl}">'
        f'{ARTICLE_TITLE[sl]} <span>&rarr;</span></a></li>' for sl in slugs)
    return f"""
  <section class="sect sect--paper2">
    <div class="wrap wrap--narrow rv">
      {eyebrow("Keep reading")}
      <ul style="list-style:none;padding:0;margin:1.6rem 0 0">{li}</ul>
    </div>
  </section>"""


def body_buyout(base):
    return art_body([
        para("Most wedding venues rent you a space for a set block of hours. An "
             "estate buyout works differently: you book the whole property, every "
             "building and every acre, for the length of your stay."),
        para("Here is what that means at The Overlook, and how it compares to a "
             "traditional venue rental."),
        h2("The whole property, only yours"),
        para("The Overlook sits on 15 private acres above Flathead Lake. When you "
             "book, the property is not shared with any other party or event. It is "
             "yours for the length of your stay."),
        para("That makes the day simpler. Getting ready happens in one of the houses "
             "on site. First looks can happen wherever the light is best. There is no "
             "other wedding sharing the parking or the grounds."),
        h2("Your closest people sleep where the wedding happens"),
        # CORRECTED: the live article listed three kinds of accommodation and
        # left out the cabin. The count is phrased exactly as weddings.html
        # phrases it, so a reader moving between the two pages is never asked to
        # reconcile five names against six buildings.
        para("The biggest difference is lodging. The estate sleeps up to 28 guests "
             "in five accommodations, all on the same fifteen acres:"),
        blist([
            "<b>The Swan</b> &mdash; the four-bedroom main house.",
            "<b>The Glacier</b> &mdash; a cabin with a sleeping loft and its own patio.",
            "<b>The Lakeside</b> &mdash; a pair of modern tiny homes.",
            "<b>The Summit</b> and <b>The Ridge</b> &mdash; two treehouses in the trees."]),
        para("Your wedding party and closest family can stay where the wedding "
             "happens. Nobody in that group needs a shuttle or a late drive back to "
             "a hotel, and everyone wakes up in the same place the next morning."),
        h2("Space built for the celebration itself"),
        para("The estate hosts receptions for up to 200 guests in a 3,200 square-foot "
             "pavilion and a 40 by 80 ft tent. Both are permanent, so nothing has to be "
             "delivered and set up for your weekend."),
        para("Around them are a pool and hot tub, open lawn for the ceremony and lawn "
             "games, and views of the lake and mountains."),
        # CORRECTED: the live article had tables and chairs as a rental. FACTS.md
        # has them on site with four head tables, and the bar built in — which
        # makes them part of what is already standing, not part of what you bring.
        para("Tables and chairs are on site, including four head tables, and the bar "
             "is built in."),
        h2("A weekend, not a time slot"),
        para("With a buyout you have the property for your whole stay, not a few "
             "hours on one day. The rehearsal dinner, a welcome gathering, the wedding "
             "and breakfast the next morning can all happen in the same place."),
        para("Quiet hours, vendor access and your timeline are set out in your "
             "agreement. Contracts are written to a 200-guest maximum and an "
             "11:00 p.m. event end."),
        h2("What you still bring in"),
        # CORRECTED: the live article called the caterers "approved partners".
        # FACTS.md has a preferred vendor list couples are not required to use.
        # Nothing here says who staffs the bar, because nothing we hold says it.
        para("Couples at "
             "The Overlook work with a day-of coordinator (required), carry event "
             "insurance, and arrange restroom rentals for larger guest counts. "
             "Catering is arranged separately. We keep a preferred vendor list of "
             "Flathead Valley planners, caterers, florists and photographers who know "
             "the property, and several extend a partner discount, but you are not "
             "required to book from it. A full planner is available if you&rsquo;d "
             "rather hand the details to someone else entirely."),
        h2("Is a buyout right for you?"),
        para("If you want a single evening with as few moving parts as possible, a "
             "traditional venue may suit you better. If you want your family and "
             "friends in one place for a few days, a buyout is built for that."),
    ])


def body_season(base):
    return art_body([
        para("The seasons in northwest Montana are very different from each other. "
             "A June evening and an October evening bring different weather, light "
             "and scenery. Here is what each time of year is like for a wedding."),
        h2("Summer: the reliable choice"),
        para("June through September brings the most settled weather of the year "
             "and the longest days. Long evenings mean the ceremony is not racing "
             "the sunset, portraits happen in good light at a reasonable hour, and "
             "dinner can start outside while it is still light."),
        para("The lake is warmest and the grounds are green, so cocktail hour on the "
             "lawn or a swim before the rehearsal dinner are easy to plan."),
        para("Summer is also the busiest time, and Saturdays in July and August are "
             "the first dates to go. If you want one, start there."),
        h2("Late spring and early fall: the shoulders"),
        para("Late May, early June, late September and October give up some "
             "weather certainty in exchange for:"),
        blist([
            "Better availability &mdash; more dates open, and more flexibility on which nights you hold the property.",
            "Different scenery &mdash; spring green and running water on one side, larch and cottonwood color on the other.",
            "Fewer crowds regionally, which makes travel and side trips easier for out-of-town guests.",
            "Softer, lower light for photos."]),
        para("Mountain weather in these months can go either way, so plan for both a "
             "warm afternoon and a cold, wet one. A covered reception space, a "
             "backup plan for the ceremony and warm layers for guests cover it."),
        h2("Winter"),
        para("A winter wedding in Montana means snow, a smaller guest list and "
             "everyone indoors. Travel takes more planning, so give guests extra time "
             "on their arrival day and keep the celebration small."),
        h2("How to decide"),
        para("Work backward from what you care about most:"),
        blist([
            "Want the safest bet on an outdoor ceremony and long golden light? Aim for the heart of summer and book far ahead.",
            "Want more date choice, a quieter valley, and dramatic scenery? Look at the shoulders and build a genuine weather plan.",
            "Have a fixed guest list traveling from far away? Prioritize the months with the easiest travel, then choose the date.",
            "Have a meaningful date already? Choose it, and design the weekend around whatever that season does best."]),
    ])


def body_travel(base):
    return art_body([
        para("Getting to The Overlook is straightforward. Here is a guide you can "
             "share with your guests."),
        h2("Fly into Glacier Park International (FCA)"),
        para("The closest airport is Glacier Park International Airport in Kalispell, "
             "Montana &mdash; airport code FCA. From FCA, the estate is roughly "
             f"{FCA['drive']}. Put that on your wedding website."),
        para("FCA is a small airport with rental car counters in the terminal. Anyone "
             "flying in on the wedding day itself should leave extra time, since a "
             "missed connection is harder to make up at a small airport."),
        h2("Renting a car vs. arranging shuttles"),
        para("Both work. Which is right depends on your guest list."),
        para("Rental cars make sense when guests are arriving on different days, want "
             "to explore the valley on their own schedule, or are extending the trip. "
             "Rental cars at FCA run short in summer, so tell guests to book "
             "early."),
        para("Group shuttles make sense when a large block of guests arrives in a "
             "similar window, when you&rsquo;d rather not manage a parking lot full "
             "of cars, or when there is a bar. A shuttle for the wedding evening means "
             "nobody has to drive after the reception. Some couples arrange rental "
             "cars for a few key people and a shuttle for everyone else."),
        blist([
            "Book shuttle service well ahead; regional operators fill up in summer.",
            "Give the driver one point of contact from your side, not five.",
            "Plan the last shuttle for after your music curfew, not at it.",
            "Let guests know in advance that there is parking on site for 75 cars."]),
        h2("Where guests stay"),
        para("The estate sleeps 28 guests onsite across the main house, the cabin, "
             "the tiny homes and the treehouses, usually kept for family and the "
             "wedding party. Everyone else stays nearby in Lakeside, Kalispell, Bigfork "
             "or Whitefish, and we can suggest places to stay."),
        h2("Extending the trip"),
        para("If guests want to stay longer, Flathead Lake has boating, swimming, "
             "lakeside restaurants and cherry stands in late summer, and the valley "
             "has plenty of hiking and small towns to visit."),
        para(f"{GLACIER['name']} is another good reason to stay. "
             f"{GLACIER['entrance']}, the park&rsquo;s west entrance, is "
             f"{GLACIER['drive']} from the estate &mdash; about {GLACIER['miles']}. "
             "It works as a day trip, but plan a full day rather than fitting it "
             "around wedding events, and check the park&rsquo;s website first, since "
             "entry rules and conditions change from year to year."),
        h2("A simple note to send your guests"),
        para("You can copy this: &ldquo;Fly into Glacier Park International "
             f"Airport (FCA) in Kalispell, Montana &mdash; the venue is about "
             f"{FCA['time']} away. Reserve a rental car early if you&rsquo;d like to "
             "explore, and watch for shuttle details for the wedding evening. If you "
             f"can, stay an extra day or two: Flathead Lake is right here, and "
             f"{GLACIER['entrance']} &mdash; the west entrance to {GLACIER['name']} "
             f"&mdash; is {GLACIER['time']} away, roughly "
             f"{GLACIER['miles']}.&rdquo;"),
    ])


ARTICLES = [
    {"slug": A_BUYOUT,
     "h1": "What&rsquo;s included in an estate-buyout wedding venue",
     "crumb": "What’s Included in an Estate-Buyout Wedding Venue",
     "title": "What&rsquo;s Included in an Estate-Buyout Wedding Venue | The Overlook",
     "desc": "How an estate buyout differs from a traditional venue rental: 15 private "
             "acres, 28 sleeping onsite, a 3,200 sq ft pavilion, and a weekend "
             "instead of a time slot.",
     "kicker": "Planning guide &middot; 5 min read",
     "lede": "A traditional venue rents you a space for a few hours. A buyout gives you "
             "the whole property for your stay.",
     "img": ("tent-front.jpg", "The reception tent from the lawn"),
     "cta_img": ("venue-overview.jpg", "The ceremony lawn and tent across the grounds"),
     "body": body_buyout,
     "cta": ("See what your weekend would look like",
             "Tell us your guest count and your season, and we will send details "
             "and current availability.",
             "Ask About Your Date", "contact.html?type=wedding"),
     "summary": "How an estate buyout differs from a traditional venue rental, and "
                "what is and is not included at The Overlook.",
     "related": [A_SEASON, A_TRAVEL]},

    {"slug": A_SEASON,
     "h1": "Best time of year for a Montana lake wedding",
     "crumb": "Best Time of Year for a Montana Lake Wedding",
     "title": "Best Time of Year for a Montana Lake Wedding | The Overlook",
     "desc": "Choosing a wedding date in northwest Montana: what summer, the shoulder "
             "seasons and winter each give you, and what each one asks of your "
             "guests and your plan.",
     "kicker": "Planning guide &middot; 5 min read",
     "lede": "What summer, the shoulder seasons and winter are each like for a "
             "wedding here.",
     "img": ("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate"),
     "cta_img": ("ceremony-setup.jpg", "Chairs set on the ceremony lawn before guests arrive"),
     "body": body_season,
     "cta": ("Tell us the season you have in mind",
             "Tell us the season you have in mind and we will let you know which "
             "dates are open.",
             "Ask About Your Date", "contact.html?type=wedding"),
     "summary": "What summer, the shoulder seasons and winter each give you for a "
                "wedding in northwest Montana.",
     "related": [A_BUYOUT, A_TRAVEL]},

    {"slug": A_TRAVEL,
     "h1": "Getting to The Overlook: a travel guide for wedding guests",
     "crumb": "Getting to The Overlook: A Travel Guide for Wedding Guests",
     "title": "Getting to The Overlook: A Travel Guide for Wedding Guests",
     "desc": "How wedding guests reach The Overlook at Flathead Lake: Glacier Park "
             f"International (FCA) is {FCA['time']} away. Rental cars, shuttles, "
             "and where guests stay.",
     "kicker": "Guest travel &middot; 5 min read",
     "lede": "Airport, cars, shuttles and places to stay, in a form you can share "
             "with your guests.",
     "img": ("venue-wide.jpg", "The estate grounds from across the lawn"),
     "cta_img": ("lake-sunset-boat.jpg", "Sunset over Flathead Lake from the estate"),
     "body": body_travel,
     "cta": ("Help with guest travel",
             "If you are planning a weekend at The Overlook and want help with guest "
             "travel, get in touch.",
             "Start Your Inquiry", "contact.html"),
     "summary": "The airport, rental cars versus shuttles, where guests stay, and how "
                "far it is to Glacier National Park.",
     "related": [A_BUYOUT, A_SEASON]},
]

ARTICLE_TITLE = {a["slug"]: a["h1"] for a in ARTICLES}
ARTICLE_BY_SLUG = {a["slug"]: a for a in ARTICLES}

# The live articles are all dated 2 September 2026. They were edited on the port
# — the expired CTA came out and three facts were corrected — so dateModified is
# today rather than the publication date.
ARTICLE_PUBLISHED = "2026-09-02"
ARTICLE_PUBLISHED_HUMAN = "September 2, 2026"


def page_article(base, slug):
    a = ARTICLE_BY_SLUG[slug]
    ch, clede, clabel, chref = a["cta"]
    return f"""
  <section class="sect sect--tight" style="padding-top:clamp(8rem,14vw,11rem);padding-bottom:0">
    <div class="wrap wrap--narrow rv">
      {dcrumb(base, [("Journal", "journal"), (a["crumb"], None)])}
      {eyebrow(a["kicker"])}
      <h1 style="font-size:clamp(2.1rem,4.4vw,3.3rem);margin-top:1.1rem">{a["h1"]}</h1>
      <p class="lede" style="margin-top:1.5rem">{a["lede"]}</p>
      <p style="margin-top:1.6rem;font-size:.82rem;letter-spacing:.06em;color:var(--muted)">
        <time datetime="{ARTICLE_PUBLISHED}">{ARTICLE_PUBLISHED_HUMAN}</time>
        &middot; {BIZ["name"]}</p>
    </div>
  </section>

  <section class="sect" style="padding-top:clamp(2.5rem,5vw,3.5rem);padding-bottom:0">
    <div class="wrap wrap--narrow rv rv--wipe">
      <figure style="margin:0">{img(a["img"][0], a["img"][1], base=base)}</figure>
    </div>
  </section>

  {a["body"](base)}

  {band(a["cta_img"][0], a["cta_img"][1], ch, clede,
        btn(base + chref, clabel, "btn btn--light btn--lg"), base=base)}

  {related(base, a["related"])}
"""


def page_journal(base):
    cards = ""
    for a in ARTICLES:
        cards += f"""<article class="rv" style="border-top:1px solid var(--line);padding:2.4rem 0">
          <p style="font-size:.72rem;letter-spacing:.17em;text-transform:uppercase;color:var(--muted)">
            {a["kicker"]}</p>
          <h2 style="font-size:clamp(1.4rem,2.6vw,2rem);margin-top:1rem">
            <a href="{base}journal/{a["slug"]}" style="text-decoration:none">{a["h1"]}</a></h2>
          <p style="margin-top:1rem;color:var(--ink-soft);max-width:62ch">{a["summary"]}</p>
          <p style="margin-top:1.4rem">{tlink(base + "journal/" + a["slug"], "Read it")}</p>
        </article>"""
    return (doc_head(base, "Journal", "Planning guides and travel notes",
                     "The questions couples and guests ask us most, answered in one place: "
                     "once: how an estate buyout works, how to choose a month in "
                     "northwest Montana, and how to get your guests here.",
                     trail=[("Journal", None)])
            + f"""
  <section class="sect" style="padding-top:clamp(2rem,4vw,3rem)">
    <div class="wrap wrap--narrow">{cards}</div>
  </section>

  {band("venue-overview.jpg", "The ceremony lawn and tent across the grounds",
        "Ask us the question that is not answered here",
        "Send the dates you are considering and what you are planning, and we "
        "will write back personally.",
        btn(base + "contact.html", "Start Your Inquiry", "btn btn--light btn--lg"),
        base=base)}
""")


# ============================================ PORTED: /things-to-do
def page_area(base):
    """Ported from the live /things-to-do — the URL stays. Since 2026-09-28 it is
    the local attractions page (owner's brief): the lake, the mountains, the
    museum in Polson and the resorts nearby.

    Every fact about a place comes from that place's own site or Montana's
    tourism listings; the source sits in a comment beside each entry. No hours
    or prices: they change, and the link out is the answer. Territory 1889 is
    listed as a nearby resort, not a thing to do (owner's call), and described
    as what it is today — planned, private, awaiting county approval.
    """
    groups = [
        ("On the lake", [
            ("Flathead Lake",
             "The largest natural freshwater lake west of the Mississippi in the lower "
             "48 sits below the property, and the pavilion looks out over it. Boating "
             "and swimming are minutes away.", None),
            # glaciermt.com/listing/miracle-of-america-museum (read 2026-09-28)
            ("Miracle of America Museum, Polson",
             "At the south end of the lake, a 4.5-acre museum of Americana: a main "
             "building and a village of more than 40 historic structures, from a "
             "blacksmith&rsquo;s shop to a 1912 one-room schoolhouse, with vintage "
             "motorcycles, military vehicles and aircraft. A good half-day for guests "
             "of any age.",
             "https://glaciermt.com/listing/miracle-of-america-museum"),
        ]),
        ("In the mountains", [
            # blacktailmountain.com (read 2026-09-28): "located in Lakeside, Montana,
            # and overlooks Flathead Lake"; "Blacktail Road 14 miles to the mountaintop"
            ("Blacktail Mountain Ski Area",
             "The closest skiing to the estate. The ski area overlooks Flathead Lake "
             "from the top of the mountain above Lakeside, 14 miles up Blacktail Road "
             "from Highway 93.",
             "https://blacktailmountain.com/"),
            (WHITEFISH["name"],
             f"{cap(WHITEFISH['time'])} from the estate. Skiing in winter, lift-served "
             "hiking and biking in summer, and the town of Whitefish below it.",
             None),
            (GLACIER["name"],
             f"{cap(GLACIER['drive'])} to {GLACIER['entrance']}, the west entrance "
             f"&mdash; {GLACIER['miles']}. It makes a good day trip before or after the "
             "weekend; plan a full day. Going-to-the-Sun Road is seasonal, so check the "
             "park&rsquo;s website before you go.",
             "https://www.nps.gov/glac/"),
        ]),
        ("Nearby resorts", [
            # visitmt.com/listing/flathead-harbor-at-lakeside-21509 (read 2026-09-28);
            # lodging types from flatheadharbor.com/rv-resort and the Whitefish Chamber
            ("Flathead Harbor, Lakeside",
             "A resort and marina on the lake in Lakeside, with cabins, condos and RV "
             "sites &mdash; somewhere for guests beyond the ones staying on the estate. "
             "It is home to the Far West, Montana&rsquo;s largest charter boat, rents "
             "boats and jet skis, and has waterfront dining at the Harbor Grille and "
             "the Anchor Bar.",
             "https://www.flatheadharbor.com/"),
            # territory1889.com; Daily Inter Lake 2026-09-23 and 2026-09-27
            ("Territory 1889",
             "A private golf and lake club planned by Discovery Land Company on 1,700 "
             "acres near Blacktail Mountain, with golf, a lake club and a marina. It is "
             "still in planning: as of September 2026 Flathead County had not yet "
             "approved its first phase.",
             "https://territory1889.com/"),
        ]),
    ]
    body = ""
    for gi, (head, places) in enumerate(groups):
        body += (f'<h2 style="margin-top:{"0" if gi == 0 else "3.4rem"}">{head}</h2>')
        for name, text, url in places:
            link = (f' <a href="{url}" rel="noopener" style="white-space:nowrap">Their site '
                    f'&rarr;</a>' if url else "")
            body += (f'<h3 style="margin-top:1.8rem;font-size:1.35rem">{name}</h3>'
                     f'<p style="margin-top:.6rem;color:var(--ink-soft)">{text}{link}</p>')
    on_site = ["A heated pool and a hot tub", "A barrel sauna",
               "A fitness room and a games room", "A fire pit",
               "A putting green", "Walking trails across the fifteen acres"]
    items = "".join(f"<li>{i}</li>" for i in on_site)
    return (doc_head(base, "The Area", "Around Lakeside and Flathead Lake",
                     "What is near the estate for guests who want to get out and "
                     "explore &mdash; and where extra guests can stay.",
                     trail=[("Things to Do", None)])
            + f"""
  <section class="sect" style="padding-top:clamp(2rem,4vw,3rem)">
    <div class="wrap wrap--narrow rv">
      {body}

      <h2 style="margin-top:3.4rem">Arriving by air</h2>
      <p style="margin-top:1rem">{FCA['name']} is {FCA['time']} away. Helicopter
        arrivals and private flights over the lake can be arranged through WestSlope
        Helicopters, who also run the transfer in the two-estate weekend package.</p>

      <h2 style="margin-top:3.4rem">Without leaving the property</h2>
      <ul style="margin-top:1rem;color:var(--ink-soft);line-height:2">{items}</ul>
      <p style="margin-top:1rem">{tlink(base + "estate.html", "See the estate")}</p>
    </div>
  </section>

  <section class="sect sect--stone">
    <div class="wrap wrap--narrow">
      <h2 class="rv">Questions guests ask</h2>
      <div class="rv">{faq(FAQ_AREA)}</div>
    </div>
  </section>

  {band("lake-sunset-boat.jpg", "The lake at sunset from the estate",
        "Planning a weekend here",
        "Tell us the dates you are considering and we will tell you whether they "
        "are open.",
        btn(base + "contact.html", "Start Your Inquiry", "btn btn--light btn--lg"),
        base=base)}
""")


# ============================================ PORTED: /wedding-venues-montana
def page_mt_venues(base):
    """Ported from the live /wedding-venues-montana.

    A category page, not a second wedding page: it answers "how do I choose a
    Montana venue" and only then says where this one sits. Written that way
    because that is the query it has to earn.
    """
    asks = [
        ("Is the power permanent?",
         "If not, generators have to be rented and placed for the weekend. Here it is "
         "200 AMP permanently installed service, with water on site."),
        ("How far do vendors carry everything?",
         "Load-in distance affects how long setup takes. Here vendors can pull up "
         "within 50 feet of the venue."),
        ("Where does everyone park?",
         "Seventy-five cars can park on the property."),
        ("When does the music stop?",
         "Ask for the end time before you book. Contracts here are written to an "
         "11:00 p.m. event end."),
        ("What is already standing?",
         "A 3,200 sq ft pavilion, a 40 &times; 80 ft tent, a built-in bar, tables and "
         "chairs including four head tables, and a fire pit."),
        ("Does another event share the weekend?",
         "One group is on this property at a time, with no shared facilities."),
    ]
    cards = "".join(f"""<div class="rv" style="border-top:1px solid var(--line);padding:2rem 0">
        <h3 style="font-size:clamp(1.05rem,1.8vw,1.25rem)">{q}</h3>
        <p style="margin-top:.8rem;color:var(--ink-soft);max-width:66ch">{a}</p>
      </div>""" for q, a in asks)

    return (doc_head(base, "Montana Wedding Venues",
                     "Choosing a wedding venue in Montana",
                     "Most Montana venues fall into two kinds: a space you rent for "
                     "a day, and a property you take over for a weekend. Here is how "
                     "they differ and what to ask.",
                     trail=[("Montana Wedding Venues", None)])
            + f"""
  <section class="sect" style="padding-top:clamp(2rem,4vw,3rem)">
    <div class="wrap wrap--narrow rv">
      <h2>The rented venue</h2>
      <p style="margin-top:1rem">You get the site for a block of hours. Tables, chairs,
        power and a bar are often rented and delivered, and guests stay somewhere else.
        The venue fee is usually lower, with more vendors to coordinate.</p>

      <h2 style="margin-top:2.8rem">The estate buyout</h2>
      <p style="margin-top:1rem">You book the whole property. The celebration and the
        lodging are on the same land, the power, tent and bar are already in place, and
        the weekend is yours from the rehearsal to the last morning.</p>
      <p style="margin-top:1rem">{tlink(base + "journal/" + A_BUYOUT,
        "What an estate buyout includes")}</p>

      <h2 style="margin-top:2.8rem">Six questions to ask any venue</h2>
      <div style="margin-top:1.4rem">{cards}</div>

      <h2 style="margin-top:2.8rem">Where The Overlook sits</h2>
      <p style="margin-top:1rem">Fifteen private acres above Flathead Lake in
        {BIZ['city']}, {FCA['time']} from {FCA['short_name']}. Up to 200 guests for the
        celebration, 28 sleeping across five accommodations, one group on the property
        at a time. Lodging is booked separately from the venue fee.</p>
      <p style="margin-top:1rem">The Overlook Wedding starts at $20,000. The Ultimate
        Flathead Lake Wedding Weekend, five nights across two estates, starts at
        $135,000. Everything beyond those two is quoted against your dates.</p>
    </div>
  </section>

  <section class="sect sect--stone">
    <div class="wrap wrap--narrow">
      <h2 class="rv">Common questions</h2>
      <div class="rv">{faq(FAQ_MTVENUES)}</div>
    </div>
  </section>

  {band("venue-overview.jpg", "The grounds and tent seen across the estate",
        "Check a date",
        "Send the weekend you have in mind and we will write back personally.",
        btn(base + "contact.html", "Start Your Inquiry", "btn btn--light btn--lg"),
        base=base)}
""")


# ================================================================== assembly
CRUMB = {"weddings.html": "Weddings", "retreats.html": "Corporate Retreats",
         "wellness.html": "Wellness Retreats",
         "estate.html": "The Estate", "gallery.html": "Gallery",
         "story.html": "Our Story", "contact.html": "Contact",
         "overlook-wedding.html": "The Overlook Wedding",
         "ultimate-wedding-weekend.html": "The Ultimate Wedding Weekend"}

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
     "A private 15-acre estate above Flathead Lake for leadership teams, boards and "
     f"company gatherings. Full-property buyout, Starlink throughout, {FCA['time']} "
     "from FCA."),

    ("wellness.html", page_wellness, "pool-wide.jpg", True,
     "Montana Wellness Retreat Venue | The Overlook at Flathead Lake",
     "A private 15-acre estate above Flathead Lake for yoga, movement and recovery "
     "retreats. Pavilion, sauna, hot tub, heated pool, 28 onsite, one group at a time."),

    ("estate.html", page_estate, "meadow-evening-light.jpg", True,
     "The Estate | Lodging &amp; Grounds at The Overlook at Flathead Lake",
     "Five accommodations sleeping 28, plus a heated pool, sauna, fitness room, fire pit "
     "and trails across 15 private acres above Flathead Lake."),

    ("gallery.html", page_gallery, "venue-wide.jpg", False,
     "Gallery | The Overlook at Flathead Lake",
     "Photographs of the estate, weddings, accommodations and grounds at The Overlook at "
     "Flathead Lake in Lakeside, Montana."),

    ("story.html", page_story, "lake-sunset-boat.jpg", True,
     "Our Story | The Overlook at Flathead Lake",
     "How Claudia and Eric went from hosting guests on Flathead Lake in 2021 to building "
     "The Overlook venue in 2025."),

    ("overlook-wedding.html", page_pkg_overlook, "reception-mountain-view.jpg", True,
     "The Overlook Wedding Package | The Overlook at Flathead Lake",
     "The whole Flathead Lake estate for your wedding, with the pavilion, tent, bar and "
     "power already in place. What is included, starting price and the day in photos."),

    ("ultimate-wedding-weekend.html", page_pkg_ultimate, "driftwood-exterior-dusk.jpg", True,
     "The Ultimate Flathead Lake Wedding Weekend | The Overlook",
     "Five nights across two Flathead Lake estates — The Overlook and The Driftwood at "
     "Woods Bay — sleeping 54, with helicopter transfer. What is included, in photos."),

    ("contact.html", page_contact, "hero-pavilion-lake.jpg", False,
     "Contact | The Overlook at Flathead Lake",
     "Start an inquiry for a wedding, corporate retreat or private event at The Overlook "
     "at Flathead Lake in Lakeside, Montana."),
]

# The share image and the LCP image are not the same picture on every page, and
# preloading the wrong one costs more than it saves.
#   gallery — the first thumbnail is what paints first; the full-size photograph
#             behind it is only fetched when the lightbox opens.
#   story   — the hero is a portrait photograph, which social cards crop badly,
#             so the card uses a landscape frame from further down the page.
PRELOAD = {"gallery.html": PHOTOS[0][0],
           "story.html":   "owners-photo.jpg"}

# A vertical photograph that phones get as the hero instead of the landscape
# one — a 3:2 frame cropped into a phone screen shows a sliver of itself.
HERO_PORTRAIT = {"weddings.html": "tent-interior-lake-view.jpg",
                 "overlook-wedding.html": "tent-long-table-roses.jpg"}


# The six ported URLs. `fn` takes the depth prefix and returns the body; the
# output path is what fixes the URL, so /privacy stays /privacy.
DOCS = [
    {"path": "journal/index.html", "fn": page_journal,
     "og": "venue-overview.jpg", "sticky": True, "priority": "0.6",
     "title": "Journal | Wedding Planning Guides | The Overlook at Flathead Lake",
     "desc": "Planning guides and travel notes from The Overlook at Flathead Lake "
             "— estate buyouts, Montana wedding seasons, and getting guests to the "
             "valley.",
     "trail": [("Journal", "journal/index.html")]},

    {"path": "privacy/index.html", "fn": page_privacy,
     "og": "hero-pavilion-lake.jpg", "sticky": False, "priority": "0.3",
     "title": "Privacy Policy | The Overlook at Flathead Lake",
     "desc": "How The Overlook at Flathead Lake collects, uses, and protects the "
             "personal information you send with an inquiry.",
     "trail": [("Privacy Policy", "privacy/index.html")]},

    {"path": "terms/index.html", "fn": page_terms,
     "og": "hero-pavilion-lake.jpg", "sticky": False, "priority": "0.3",
     "title": "Terms of Service | The Overlook at Flathead Lake",
     "desc": "The terms of service that apply to the website of The Overlook at "
             "Flathead Lake and to inquiries made through it.",
     "trail": [("Terms of Service", "terms/index.html")]},
]

DOCS.append(
    {"path": "things-to-do/index.html", "fn": page_area,
     "og": "lake-sunset-boat.jpg", "sticky": True, "priority": "0.7",
     "title": "Things to Do Near Flathead Lake & Lakeside | The Overlook",
     "desc": "Near the estate in Lakeside, Montana: Flathead Lake, Blacktail and "
             "Whitefish skiing, Glacier National Park, the Miracle of America Museum "
             "and nearby resorts.",
     "trail": [("Things to Do", "things-to-do/index.html")]})

DOCS.append(
    {"path": "wedding-venues-montana/index.html", "fn": page_mt_venues,
     "og": "venue-overview.jpg", "sticky": True, "priority": "0.9",
     "title": "Montana Wedding Venues | How to Choose One",
     "desc": "How Montana wedding venues differ — estate buyouts versus rented sites, "
             "six questions worth asking before you book, and where a private Flathead "
             "Lake estate fits.",
     "trail": [("Montana Wedding Venues", "wedding-venues-montana/index.html")]})

for _a in ARTICLES:
    DOCS.append({
        "path": f"journal/{_a['slug']}/index.html",
        "fn": (lambda sl: lambda base: page_article(base, sl))(_a["slug"]),
        "og": _a["img"][0], "sticky": True, "priority": "0.6",
        "title": _a["title"], "desc": _a["desc"], "article": _a["slug"],
        "trail": [("Journal", "journal/index.html"),
                  (_a["crumb"], f"journal/{_a['slug']}/index.html")]})


# ---------------------------------------------------------------- redirects
# The live site indexed these URLs. The rebuild renamed some pages and dropped
# others, so without a destination each one 404s the day the domain is
# repointed and whatever ranking it holds is thrown away.
#
# Three artefacts, because the host is not decided yet:
#   _redirects   — Netlify / Cloudflare Pages
#   vercel.json  — Vercel
#   an HTML stub — every other static host, including plain S3 or Apache
# Whichever the host understands wins; the others sit inert. The stub carries a
# canonical to the destination and noindex on itself, so it cannot compete in
# the index with the page it points at.
REDIRECTS = {
    "wedding-experiences":    "weddings.html",
    "stay-onsite":            "estate.html",
    "helicopter-experiences": "things-to-do",
    "private-events":         "retreats.html",
    "corporate-retreats":     "retreats.html",
    "wellness-retreats":      "wellness.html",
    "gallery":                "gallery.html",
    "about":                  "story.html",
    "contact":                "contact.html",
    "book":                   "contact.html",
}

STUB = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Page moved | {name}</title>
<meta name="description" content="This page has moved. The current version of it now lives at {target} instead.">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{target}">
<meta http-equiv="refresh" content="0;url={dest}">
</head>
<body>
<p>This page has moved to <a href="{dest}">{target}</a>.</p>
<script>location.replace({js});</script>
</body>
</html>
"""


def write_redirects():
    lines, vercel = [], []
    for old, new in sorted(REDIRECTS.items()):
        dest = "/" + new
        lines.append("/%s  %s  301" % (old, dest))
        vercel.append({"source": "/" + old, "destination": dest, "permanent": True})

        d = os.path.join(ROOT, old)
        os.makedirs(d, exist_ok=True)
        target = SITE + "/" + new
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(STUB.format(name=BIZ["name"], target=target, dest=dest,
                                js=json.dumps(dest)))

    header = "# Generated by tools/build.py - old live URLs kept alive.\n"
    open(os.path.join(ROOT, "_redirects"), "w", encoding="utf-8").write(
        header + "\n".join(lines) + "\n")
    with open(os.path.join(ROOT, "vercel.json"), "w", encoding="utf-8") as f:
        json.dump({"redirects": vercel}, f, indent=2)
        f.write("\n")
    print("  wrote %d redirects (_redirects, vercel.json, HTML stubs)" % len(REDIRECTS))


# ---------------------------------------------------------------- share cards
# Social and chat previews crop to roughly 1.91:1. The photography here is 3:2,
# so handing it over raw lets each platform choose its own crop — which is how
# a horizon ends up through somebody's head. These are cut once, centred, at the
# size the scrapers actually want, and regenerated only when the source changes.
OG_DIR = "assets/img/og/"
OG_W, OG_H = 1200, 630


def make_og_cards(names):
    import subprocess
    out = os.path.join(ROOT, OG_DIR)
    os.makedirs(out, exist_ok=True)
    made = 0
    for n in sorted(set(names)):
        src = os.path.join(ROOT, IMG + n)
        dst = os.path.join(out, n)
        if not os.path.isfile(src):
            continue
        if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            continue
        dims = imgsize(IMG + n)
        if not dims:
            continue
        w, h = dims
        # crop to the card's aspect at full resolution first, then scale down,
        # so the result is a real 1200x630 rather than a stretched 3:2
        want = OG_W / float(OG_H)
        if w / float(h) > want:
            cw, ch = int(round(h * want)), h
        else:
            cw, ch = w, int(round(w / want))
        try:
            subprocess.run(["sips", "-c", str(ch), str(cw), src, "--out", dst],
                           check=True, capture_output=True)
            subprocess.run(["sips", "-z", str(OG_H), str(OG_W), dst],
                           check=True, capture_output=True)
            made += 1
        except Exception as e:
            print("  !! og card failed for %s: %s" % (n, e))
    if made:
        print("  wrote %d share cards (%dx%d) to %s" % (made, OG_W, OG_H, OG_DIR))


def blog_nodes(path, article_slug):
    """BlogPosting for an article, or the blogPost list for the index."""
    if article_slug:
        a = ARTICLE_BY_SLUG[article_slug]
        url = url_of(path)
        return [{"@type": "BlogPosting", "@id": f"{url}#article",
                 "headline": _plain(a["h1"]), "description": _plain(a["desc"]),
                 "url": url,
                 "datePublished": ARTICLE_PUBLISHED,
                 "dateModified": datetime.date.today().isoformat(),
                 "author": {"@id": f"{SITE}/#venue"},
                 "publisher": {"@id": f"{SITE}/#venue"},
                 "mainEntityOfPage": {"@id": f"{url}#webpage"},
                 "isPartOf": {"@id": f"{SITE}/journal#webpage"},
                 "image": [f"{SITE}/{IMG}{a['img'][0]}"],
                 "articleSection": _plain(a["kicker"].split("&middot;")[0]),
                 "inLanguage": "en-US"}]
    return []


def blog_index_extra():
    return {"blogPost": [
        {"@type": "BlogPosting",
         "@id": f"{url_of('journal/' + a['slug'] + '/index.html')}#article",
         "headline": _plain(a["h1"]),
         "url": url_of(f"journal/{a['slug']}/index.html"),
         "datePublished": ARTICLE_PUBLISHED} for a in ARTICLES]}


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


def venue_node():
    """The one description of the business, emitted on every page.

    Every page carries the same node under the same @id, so no two pages can
    describe the estate differently — a crawler that only ever sees weddings.html
    still gets the whole entity, and an assistant comparing two pages finds them
    identical rather than in disagreement. No prices: the site publishes one, and
    it lives on the Offer for that package alone.
    """
    return {"@type": ["EventVenue", "LodgingBusiness"], "@id": f"{SITE}/#venue",
         "name": BIZ["name"],
         "description": ("A private 15-acre estate above Flathead Lake in Lakeside, "
                         "Montana, booked exclusively for one group at a time. Weddings "
                         "for up to 200 guests, corporate retreats, and sleeping for 28 "
                         "across five accommodations."),
         "url": f"{SITE}/", "email": BIZ["email"],
         "address": ADDRESS, "geo": GEO, "areaServed": "Flathead Valley, Montana",
         "maximumAttendeeCapacity": 200,
         # No petsAllowed key: there is no pets policy in FACTS.md or anywhere on
         # the site, and this node is now on all 14 pages — an unsourced "no pets"
         # would be the single most machine-readable claim we make. If Eric sets a
         # policy, it goes in FACTS.md first and here second.
         "numberOfRooms": {"@type": "QuantitativeValue", "value": 5,
                           "unitText": "accommodations"},
         "logo": f"{SITE}/{IMG}overlook-logo-main.png",
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
             {"@type": "Offer", "name": "The Overlook Wedding",
              "description": "Exclusive use of the estate for a multi-day wedding, with "
                             "the pavilion, tent and bar already standing. Lodging is "
                             "booked separately.",
              "priceSpecification": {"@type": "PriceSpecification",
                                     "minPrice": 20000, "priceCurrency": "USD"}},
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
                                     "minPrice": 135000, "priceCurrency": "USD"}}],
         "sameAs": [BIZ["ig"], BIZ["fb"], BIZ["ig_sis"]]}


def website_node():
    return {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/",
            "name": BIZ["name"], "publisher": {"@id": f"{SITE}/#venue"},
            "inLanguage": "en-US"}


def url_of(path):
    """Output file -> the URL it is served at.

    "index.html"                 -> https://…/
    "weddings.html"              -> https://…/weddings.html
    "privacy/index.html"         -> https://…/privacy
    "journal/<slug>/index.html"  -> https://…/journal/<slug>

    The six ported pages keep the extensionless URLs they are already indexed
    under; a directory index is what makes that work without a redirect.
    """
    if path.endswith("/index.html"):
        path = path[:-len("/index.html")]
    elif path == "index.html":
        path = ""
    return f"{SITE}/{path}"


def crumbs(url, trail):
    """trail: [(label, path), …] after Home. The homepage gets no trail at all."""
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"}]
    for i, (label, path) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": label,
                      "item": url_of(path)})
    return {"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb",
            "itemListElement": items}


def schema(path, title, desc, og_image, trail=(), extra=None, page_type=None,
           page_extra=None):
    """One @graph per page: the venue, the site, this page, its trail, its FAQ.

    Emitting the business on every page rather than the homepage alone is the
    point — most pages here can be the landing page for a query, and a page that
    only carries a breadcrumb tells an assistant nothing about who it is reading.
    """
    url = url_of(path)
    page = {"@type": page_type or "WebPage", "@id": f"{url}#webpage", "url": url,
            "name": _plain(title), "description": _plain(desc),
            "isPartOf": {"@id": f"{SITE}/#website"},
            "about": {"@id": f"{SITE}/#venue"},
            "primaryImageOfPage": {"@type": "ImageObject",
                                   "url": f"{SITE}/{IMG}{og_image}"},
            "inLanguage": "en-US"}
    page.update(page_extra or {})
    nodes = [venue_node(), website_node(), page]
    if trail:
        page["breadcrumb"] = {"@id": f"{url}#breadcrumb"}
        nodes.append(crumbs(url, trail))
    if path in FAQS:
        # FAQPage is a WebPage, so the page node carries the questions rather
        # than a second, competing page-level node at the same URL.
        page["@type"] = ["WebPage", "FAQPage"]
        page["mainEntity"] = faq_schema(FAQS[path])["mainEntity"]
    nodes.extend(extra or [])
    graph = {"@context": "https://schema.org", "@graph": nodes}
    return ('<script type="application/ld+json">\n%s\n</script>\n'
            % json.dumps(graph, ensure_ascii=False, separators=(",", ":")))


def llms_txt():
    """https://llmstxt.org — a plain-language brief for models that read the site.

    Everything here is also in the HTML; this just removes any need to infer it.
    """
    def qa(items):
        return "\n".join(f"- **{_plain(q)}** {_plain(a)}" for q, a in items)

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
- Pricing: two starting figures are published, below. Everything else is quoted
  directly against the dates and the shape of the event.
- The Overlook Wedding: starting at $20,000
- The Ultimate Flathead Lake Wedding Weekend (both estates): starting at $135,000
- That package is five nights across two estates: The Overlook (sleeps 28) plus The
  Driftwood, a 14,000 sq ft lakefront home at Woods Bay (sleeps 26), for a combined 54.
  Helicopter transfer between the two is available through WestSlope Helicopters.
- Travel: {FCA['time']} from {FCA['name']}; {WHITEFISH['time']} from
  {WHITEFISH['name']}; {GLACIER['time']} ({GLACIER['miles']}) to {GLACIER['entrance']},
  the west entrance to {GLACIER['name']}
- The event spaces: a 3,200 sq ft reception pavilion with panoramic lake views; a
  40 × 80 ft tent, clear-top or white-top, with full sides; separate ceremony, cocktail
  and reception areas; a built-in bar; tables and chairs on site including four head
  tables; a fire pit; a dedicated onsite venue coordinator.
- Infrastructure: 200 AMP permanently installed electrical service and on-site water;
  vendor load-in within 50 ft of the venue; parking for 75 cars on the property;
  Starlink at the venue and in all five houses.
- Contract terms: written to a 200-guest maximum, with an 11:00 p.m. event end.
  Lodging is booked separately from the venue fee.
- Vendors: a preferred list of Flathead Valley planners, caterers, florists and
  photographers who know the property, several of whom extend a partner discount.
  Couples are not required to book from it.
- Amenities: {", ".join(AMENITIES)}
- Food: a private chef can cook for the group in the main house; full-service catering,
  family-style service, grazing tables or a food truck on the lawn can all be arranged.
  The bar is built in.
- Activities: Flathead Lake boating and swimming minutes away; helicopter arrivals and
  private lake flights through WestSlope Helicopters; {WHITEFISH['name']}
  {WHITEFISH['time']} away and {GLACIER['name']} {GLACIER['time']}
- Contact: {BIZ['email']}
- Owners: Claudia and Eric
- Inquiries are answered personally, usually within one business day
- Sister brand: Flathead Lake Luxury Lodging

## Not published here

- Rates, other than the one package above. There is no rate card to quote from; every
  booking is priced against the dates and the shape of the event.
- Open dates. Availability changes and is answered by the owners directly, so please
  do not infer a calendar from this page.
- The exact street address. The estate is private; directions and a gate code go out
  once a date is held.

## Pages

- [Home]({SITE}/): overview of the estate and both ways it is booked
- [Weddings]({SITE}/weddings.html): the wedding weekend, what is included, how pricing
  works, the two packages, reviews, FAQ
- [Corporate Retreats]({SITE}/retreats.html): full-property buyout for teams, the
  formats it runs in, how to get a proposal
- [Wellness Retreats]({SITE}/wellness.html): yoga, movement and recovery retreats — the
  pavilion as a movement floor, sauna, hot tub, heated pool, trails, private chef
- [The Estate]({SITE}/estate.html): the five accommodations and the grounds
- [Gallery]({SITE}/gallery.html): photographs of the property
- [Our Story]({SITE}/story.html): how the venue came to be
- [Contact]({SITE}/contact.html): inquiry form, location and drive times
- [Montana Wedding Venues]({SITE}/wedding-venues-montana): how an estate buyout differs
  from renting a site for the day, and the questions worth asking either kind
- [Things to Do]({SITE}/things-to-do): the lake, Glacier National Park, Whitefish and
  what is on the property, with drive times

## Guides

- [What is included in an estate-buyout wedding venue]({SITE}/journal/{A_BUYOUT}):
  how a buyout differs from a traditional venue rental, and what you still bring in.
- [Best time of year for a Montana lake wedding]({SITE}/journal/{A_SEASON}): what
  summer, the shoulder seasons and winter each give you here.
- [Getting to The Overlook: a travel guide for wedding guests]({SITE}/journal/{A_TRAVEL}):
  the airport, rental cars versus shuttles, and how far the park really is.

## Policies

- {SITE}/privacy
- {SITE}/terms

## Common questions — weddings

{qa(FAQ_WEDDINGS)}

## Common questions — corporate retreats

{qa(FAQ_RETREATS)}

## Common questions — wellness retreats

{qa(FAQ_WELLNESS)}

## Common questions — choosing a Montana venue

{qa(FAQ_MTVENUES)}

## Common questions — the area

{qa(FAQ_AREA)}

## About this file

Generated by tools/build.py from the same copy the pages render, so it cannot
contradict them. Reviews are quoted on the site verbatim and credited; please quote
them the same way rather than paraphrasing. Last built {datetime.date.today().isoformat()}.
"""


LASTMOD_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lastmod.json")


def lastmods(built, today):
    """<lastmod> per page, moved only when that page's HTML actually changed.

    Stamping every URL with today's date on every build is the fastest way to
    teach a crawler that this sitemap's dates mean nothing. The hashes live in
    tools/lastmod.json and should be committed with the HTML they describe.
    """
    try:
        with open(LASTMOD_STATE, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}
    for name, html in built.items():
        h = hashlib.sha1(html.encode("utf-8")).hexdigest()
        if state.get(name, {}).get("hash") != h:
            state[name] = {"hash": h, "lastmod": today}
    state = {k: v for k, v in state.items() if k in built}
    with open(LASTMOD_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")
    return {k: v["lastmod"] for k, v in state.items()}


def write_page(path, body, title, desc, og, over, current, sticky, ld, lcp,
               missing, built):
    """Assemble, write, and check one page at any depth."""
    base = rel(path)
    extra = ""
    if lcp:
        # lcp is a photograph name; the preload carries the same AVIF candidates
        # as the hero <picture>, so the phone fetches one small file, once.
        name = lcp.rsplit("/", 1)[-1]
        extra = hero_preload(name, base, SZ_GALLERY if current == "gallery.html" else SZ_FULL,
                             portrait=HERO_PORTRAIT.get(current)) + "\n"
    html = (head(title, desc, url_of(path), og, extra + ld, base)
            + header(current, over_hero=over, base=base) + body
            + footer(base, sheet=(current != "contact.html"),
                     kind={"weddings.html": "wedding", "retreats.html": "corporate",
                           "overlook-wedding.html": "wedding",
                           "ultimate-wedding-weekend.html": "wedding",
                           "wellness.html": "wellness"}.get(current, ""),
                     campaign=PACKAGE_CAMPAIGN.get(current, "")).replace("{year}", str(YEAR))
                          .replace("{STICKYBAR}",
                                   stickybar(current, base) if sticky else ""))
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)
    built[path] = html
    # verify every referenced photo actually exists — including the preload
    # and the absolute og:image, neither of which is an src attribute
    for part in re.split(r'(?:src|href|content)="', html)[1:]:
        p = part.split('"')[0].replace(SITE + "/", "")
        if base and p.startswith(base):
            p = p[len(base):]
        if p.startswith(("assets/img/", "assets/thumb/")) and \
           not os.path.exists(os.path.join(ROOT, p)):
            missing.add(p)
    print(f"  wrote {path:38s} {len(html)//1024:>3d} KB")


def main():
    images.build(ROOT, log=print)           # responsive derivatives + manifest, cached by hash
    make_og_cards([p[2] for p in PAGES] + [d["og"] for d in DOCS])
    missing = set()
    built = {}
    priority = {}
    for name, fn, og, over, title, desc in PAGES:
        trail = () if name == "index.html" else ((CRUMB[name], name),)
        write_page(name, fn(), title, desc, og, over, name, True,
                   schema(name, title, desc, og, trail),
                   PRELOAD.get(name, IMG + og), missing, built)
        priority[name] = "1.0" if name == "index.html" else "0.8"

    for d in DOCS:
        path, base = d["path"], rel(d["path"])
        slug = d.get("article")
        ld = schema(path, d["title"], d["desc"], d["og"], d["trail"],
                    extra=blog_nodes(path, slug),
                    page_type=(["CollectionPage", "Blog"]
                               if path == "journal/index.html" else None),
                    page_extra=(blog_index_extra()
                                if path == "journal/index.html" else None))
        write_page(path, d["fn"](base), d["title"], d["desc"], d["og"],
                   False, "", d["sticky"], ld,
                   IMG + d["og"] if slug else None, missing, built)
        priority[path] = d["priority"]

    write_redirects()

    # sitemap + robots
    today = datetime.date.today().isoformat()
    stamps = lastmods(built, today)
    urls = "\n".join(
        f"  <url><loc>{url_of(n)}</loc>"
        f"<lastmod>{stamps[n]}</lastmod>"
        f"<priority>{priority[n]}</priority></url>"
        for n in built)
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f"{urls}\n</urlset>\n")
    ai_bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
               "Claude-SearchBot", "PerplexityBot", "Perplexity-User", "Google-Extended",
               "Applebot-Extended", "CCBot", "meta-externalagent", "Bytespider"]
    bots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ai_bots)
    open(os.path.join(ROOT, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\n"
        f"# Assistants are welcome to read and cite this site. The condensed\n"
        f"# fact sheet is at {SITE}/llms.txt\n"
        f"# — generated from the same copy as the pages, so it cannot\n"
        f"# contradict them.\n\n{bots}"
        f"Sitemap: {SITE}/sitemap.xml\n")
    open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write(llms_txt())
    print("  wrote sitemap.xml, robots.txt, llms.txt")

    if missing:
        print("\n  !! MISSING IMAGES:")
        for m in sorted(missing):
            print("     ", m)
        return 1
    print(f"\n  {len(built)} pages ({len(DOCS)} at ported URLs), "
          f"{len(PHOTOS)} gallery photos, all images present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
