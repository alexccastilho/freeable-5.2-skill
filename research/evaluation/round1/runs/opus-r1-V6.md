Here's a plan for moving a 12-person office over one weekend, Friday 6pm to Monday 8am. The aim is that people sit down Monday morning and their desk, network, and phones already work. Most of the real work happens in the 3–4 weeks **before** the weekend. The weekend itself should only be execution.

## Questions I would ask

1. **How far is the move and what are the buildings like?** (Same city? Elevators, loading dock, parking for a truck, building move-hour rules or a required certificate of insurance?)
   *Default:* same metro area, under 30 min drive. Both buildings have a freight elevator that must be booked, and both require the mover's COI.
2. **Professional movers or DIY?**
   *Default:* a professional moving company for furniture and boxes. Staff pack their own desks, and IT handles the tech.
3. **What IT is on site?** (Servers/NAS, network rack, desk phones, printers, or mostly laptops + cloud?)
   *Default:* laptops + cloud apps, plus a small rack (firewall, switch, Wi-Fi APs, NAS), 1–2 printers, and monitors at every desk. Internet at the new site is a new circuit.
4. **Is the new space ready?** (Fit-out finished, network cabling installed and tested, furniture new or moving?)
   *Default:* fit-out finished and cabling installed one week before. Existing furniture moves.
5. **Budget and who is in charge?**
   *Default:* one move coordinator (office manager) with decision authority, an IT lead (internal or MSP), and a modest budget for movers, crates, and a few volunteer staff paid for weekend time.
6. **Hard constraints?** (Old lease end date/key handover, security deposits, any client-facing service that can't go down?)
   *Default:* old lease ends a few days after the move, so there's a short buffer for leftovers and cleaning.

## Roles
- **Move coordinator:** owns the plan, the vendors, and the go/no-go decisions.
- **IT lead:** internet, network, and the desk setup checklist.
- **Two floor captains:** one at the old site, one at the new site. They direct movers and check off inventory.
- **Everyone:** packs and labels their own desk by Friday 5pm.

## Timeline

### T-6 to T-4 weeks
- Confirm the move date in writing with both building managers. Book freight elevators and loading docks for Friday evening and Saturday at both sites.
- Get 2–3 mover quotes and book one, including insurance/COI and a crate rental (crates stack better than boxes).
- **Order the internet circuit for the new site now** (lead times are often 3–6 weeks). This is the single most common reason a move slips. Order a 4G/5G backup router as a fallback.
- Floor plan: assign every person a desk number and give every desk, room, and zone a label code.
- Notify: clients and suppliers (new address), post/courier forwarding, bank, insurer, registrations, website/Google Business listing, letterhead.

### T-3 to T-2 weeks
- IT inventory: every device gets a tag mapped to its destination desk.
- Visit the new site: test cabling, power outlets per desk, Wi-Fi AP positions, rack location, and cooling. Get keys/access cards for all 12 people.
- Arrange utilities, cleaning, and kitchen setup at the new site. Schedule cleaning at the old site for after the move.
- Purge: shred, recycle, or donate what you won't take. Book a junk removal pickup.

### T-1 week
- **Confirm the internet circuit is live and tested** at the new site. If it isn't, switch to the backup router plan now.
- Pre-stage the new site where possible: install firewall and switch config, mount APs, and test that a laptop can reach the internet and cloud apps.
- Hand out crates and labels. Send a one-page "how to pack your desk" guide (label every item with the desk number, put cables in a bagged and labeled pouch, laptops go home with their owners).
- Reconfirm movers, elevator bookings, and access times. Share a contact sheet with everyone's phone numbers.
- Take full backups of the NAS/servers and verify the restore works.

### Friday (move starts)
- **By 5pm:** staff finish packing and take laptops home. Kitchen emptied, fridge defrosted.
- **6:00pm:** IT shuts down and disconnects the rack and printers, photographing the cabling before unplugging. Floor captain walks through with the mover lead.
- **6:30–11pm:** movers load furniture, crates, and IT equipment. IT gear travels in a car with the IT lead or in a clearly marked fragile load. Old-site captain checks the inventory list as items leave.

### Saturday
- **8am–2pm:** movers unload at the new site. The new-site captain directs each item to its desk/zone by label code. Furniture is assembled.
- **Afternoon:** IT installs the rack, connects NAS/printers, and verifies the internet and Wi-Fi.
- **Evening:** quick walkthrough. Note anything missing or damaged (photograph damage for the mover's insurance claim).

### Sunday
- **Morning:** desk setup. At every desk: monitors, dock, keyboard/mouse, power, and network tested against the checklist. Printers: print a test page from a laptop.
- **Afternoon:** unpack shared areas (kitchen, supplies, meeting room AV). Set up the alarm and access control. Put up signage and Wi-Fi details.
- **4pm: go/no-go check.** If something critical is broken (no internet, for example), activate the fallback: backup router, or tell staff to work from home Monday morning. Send that message Sunday evening, not Monday at 7:55.
- Send staff a "welcome Monday" message: address, parking/transit, access cards, floor plan with desk numbers, and who to ask for help.

### Monday
- **7:30am:** coordinator and IT lead on site early.
- **8am:** staff arrive and plug in. IT does rounds for the first two hours. Collect a running list of issues.
- **During the week:** fix the issue list, return crates, file any damage claim, collect leftovers from the old site, final clean, and hand back the keys.

## Risks and fallbacks
| Risk | Mitigation |
|---|---|
| New internet circuit not live | Order early, confirm at T-1 week, have a 4G/5G backup router, and a work-from-home Monday plan |
| Freight elevator unavailable / building rules | Book in writing at both sites, keep the COI on file, have the building contact's phone number |
| Movers late or no-show | Reconfirm on Wednesday and Friday morning. Keep the second-choice mover's number |
| Lost or damaged IT equipment | Tag inventory, transport IT gear separately, take photos, back up before the move |
| People can't get in Monday | Test access cards and keys on Sunday |

If you can tell me which defaults are wrong (especially the distance, whether you're using movers, and what IT is on site), I'll tighten the plan and turn it into a checklist with owners and dates.
