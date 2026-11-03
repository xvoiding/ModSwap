"""Names to try when listing the characters of Marvel's Spider-Man Remastered. The game's index (toc) stores only 64-bit HASHES of asset paths, so a character can only be listed when its path is
guessed; every guess is checked against the real index, so only models that really exist ever show up. Suits live at characters/hero/hero_spiderman_<id>/, everyone else at characters/npc/npc_<id>/."""

SUITS = """classic advanced advanced2 advanced_2 advancedsuit advanced_suit noir punk spiderpunk spider_punk scarlet scarlet2 scarlet_2 scarletspider scarlet_spider stealth bigtime big_time stealth_bigtime
iron ironspider iron_spider ironspider2 iron_spider_2 ironspider_mk2 crimson crimsoncowl crimson_cowl negative velocity vintage vintagecomic vintage_comic secret_war secretwar fear_itself fearitself electric
electrically_insulated insulated webwarrior web_warrior upgraded spirit anti_ock antiock homemade ultimate ps4 ps4_advanced ps4advanced ps4_classic miles base undies arachnid spider_clan spiderclan dark bodyguard
armor armour spiderarmor spider_armor armormk4 armor_mk4 armourmk4 mk4 mark4 mark_4 spiderarmor_mk4 spider_armor_mk4 spiderarmormk4 2099 spider2099 spiderman2099 spider_man_2099 black2099 black_2099 2099black
blacksuit black_suit black blackcat symbiote venom antivenom anti_venom miles_suit mileshoodie hoodie casual peter peterparker peter_parker nosuit no_suit suitless bagman bombastic bombastic_bag_man
webslinger wrestler hybrid spiderverse spider_verse amazing amazing2 amazing_spiderman raimi tobey maguire garfield holland mcu tasm tasm2 mcu_suit ps5 remastered future_foundation futurefoundation ff
steel steelspider steel_spider spiderman spider_man classic_remastered advanced_remastered scarlet_remastered noir_remastered punk_remastered cyborg cyber cybernetic neon neon_punk neonpunk
dr_octopus octopus doc_ock docock peter_hoodie peter_jacket winter winterjacket homemadesuit homemade_suit damaged torn battle battledamaged battle_damaged nwh ffh mk1 mk2 mk3 mark1 mark2 mark3 homecoming farfromhome nowayhome""".split()

_FIRST = """peter maryjane mary_jane mj aunt_may auntmay may miles morales milesmorales ganke rio otto octavius doctoroctopus doctor_octopus dr_octopus norman osborn harry jonah jameson jjj
martin li mrli mr_li martinli martin_li mrnegative mr_negative wilson fisk kingpin yuri watanabe yuriwatanabe jefferson davis jeffersondavis captain felicia hardy blackcat black_cat silver sablinger silversablinger
silvermane silver_sablinger adrian toomes vulture max dillon electro herman schultz shocker aleksei sytsevich rhino mac gargan scorpion taskmaster hammerhead screwball tinkerer phineas mason
demon demons innerdemon inner_demon thug goon grunt enforcer brute heavy sniper bodyguard guard security soldier merc mercenary agent police cop swat officer detective civilian pedestrian reporter anchor newsman
cameraman photographer firefighter paramedic nurse doctor scientist engineer technician worker construction vendor cook chef waiter bartender barista homeless busker tourist jogger student kid child boy girl
man woman male female oscorp fisk_thug fiskthug fisk_goon fiskgoon sable sable_soldier sablesoldier shield nickfury nick_fury fury carlyle conners curt connors lizard morbius tombstone rhino_suit mrnegative_suit
spiderbot spider_bot drone dronebot robot octobot sentry turret mech tinkerer_drone prowler hobgoblin green_goblin greengoblin goblin venom carnage eddie brock flash thompson ned leeds jessica jones luke cage
sandman sand kraven trapster boomerang beetle vulcan walker cop_a cop_b swat_a swat_b thug_a thug_b thug_c thug_d goon_a goon_b goon_c demon_a demon_b demon_c sable_a sable_b sable_c fisk_a fisk_b fisk_c""".split()

NPCS = list(dict.fromkeys(
    list(_FIRST) + [a + b for a in ('', ) for b in ()]
    + ['%s_%s' % (n, s) for n in ('thug', 'goon', 'demon', 'sable', 'fisk', 'oscorp', 'police', 'civilian', 'civ', 'pedestrian', 'male', 'female', 'man', 'woman', 'guard', 'soldier', 'cop', 'swat', 'worker', 'scientist') for s in ('01', '02', '03', '04', '05', 'a', 'b', 'c', 'd', 'e', 'f', 'male', 'female')]
    + ['%s%d' % (n, k) for n in ('thug', 'goon', 'demon', 'civ', 'civilian', 'pedestrian', 'male', 'female') for k in range(1, 13)]
    + [n + s for n in ('mrnegative', 'kingpin', 'rhino', 'vulture', 'electro', 'scorpion', 'shocker', 'doctoroctopus', 'maryjane', 'auntmay', 'blackcat', 'taskmaster', 'hammerhead', 'screwball', 'milesmorales', 'yuri', 'jameson', 'osborn', 'tinkerer', 'silvermane', 'fury')
       for s in ('_suit', '_casual', '_demon', '_boss', '_hero', '_01', '_02', '_a', '_b', '_young', '_old', '_hospital', '_prison', '_armor', '_armour', '_mk2', '_damaged', '_cutscene', '_gameplay', '_ps4')]))

TITLES = {'mrnegative': 'Mr. Negative', 'maryjane': 'Mary Jane', 'auntmay': 'Aunt May', 'blackcat': 'Black Cat', 'doctoroctopus': 'Doctor Octopus', 'milesmorales': 'Miles Morales', 'yuri': 'Yuri Watanabe',
          'jameson': 'J. Jonah Jameson', 'silvermane': 'Silvermane', 'screwball': 'Screwball', 'taskmaster': 'Taskmaster', 'hammerhead': 'Hammerhead', 'jeffersondavis': 'Jefferson Davis', 'maryjane': 'Mary Jane Watson', 'tombstone': 'Tombstone', 'firefighter': 'Firefighter', 'reporter': 'Reporter', 'vulture': 'Vulture',
          'electro': 'Electro', 'shocker': 'Shocker', 'rhino': 'Rhino', 'scorpion': 'Scorpion', 'kingpin': 'Kingpin'}
