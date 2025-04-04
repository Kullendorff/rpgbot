# Mapping mellan korta och långa namn
WEAPON_TYPE_ALIASES = {
    "obe": "obevapnat",
    "nar": "narstrid",
    "avs": "avstand",
    "sko": "skoldar",
    # Behåll även de fullständiga namnen som alias
    "obevapnat": "obevapnat",
    "narstrid": "narstrid",
    "avstand": "avstand",
    "skoldar": "skoldar",
}

# Fumble tables data
FUMBLE_TABLES = {
    "obevapnat": {
        # Ursprungliga resultat
        1: "Rollpersonen snubblar och faller och räknas därefter som liggande. Är underlaget hårt (exempelvis sten) får rollpersonen ett krys (+1) Smärta.",
        2: "Rollpersonen snubblar och faller illa – rollpersonen får ett kryss Trauma och Ob1T6 kryss Smärta. Rollpersonen räknas som liggande.",
        3: "Rollpersonen lyckas med konststycket att attacka sig i ryggen eller annan del av kroppen – rollpersonen får därför Ob1T6 krys Smärta.",
        4: "Rollpersonen gör kapitalt fel och tappar helt balansen och får Ob1T6 krys Smärta. Rollpersonen räknas som liggande.",
        5: "Rollpersonen tappar andan och får enbart utföra instinktiva försvarshandlingar under resten av den innvarande rundan. Dessutom erhåller rollpersonen Ob2T6 krys Utmattning.",
        6: "Rollpersonen faller och slår i huvudet hårt – antingen i marken eller på något närbeläget objekt. Detta medför att rollpersonen får Ob1T6 krys Smärta och ett krys (+1) Trauma.",
        7: "Rollpersonen lyckas trassla in sig i sina kläder (eller sitt pansar om sådant finns). Det krävs ett normalt slag (Ob3T6) mot RÖR för att ta sig loss. Rollpersonen får slå en gång per runda. Under tiden som rollpersonen är intrasslad får rollpersonen inte göra någonting annat än att undvika (även ducka, gå bakåt, hoppa och sådant). Observera att försöka ta sig loss räknas som en handling. Att undvika då man är intrasslad är en nivå svårare (+Ob1T6) – gäller tills rollpersonen lyckat ta sig loss.",
        8: "Rollpersonen gör en omöjlig manöver och får tillfällig blackout och förlorar automatiskt initiativet under Ob1T6 rundor. Rollpersonen kan dock göra försvarshandlingar som vanligt under denna tid.",
        9: "Rollpersonen vrickar foten vid en klumpig handling och faller till marken. Sänk FÖR med två (–2) under Ob1T6 dagar (fri vård och ett lyckat Läkekonst-slag kan halvera tiden) samt anteckna Ob1T6 krys Smärta. Rollpersonen ligger ned och kan inte resa sig under Ob1T6 rundor.",
        10: "Rollpersonen halkar på underlaget och faller olyckligt till marken med ljudlig duns. Rollpersonen tappar andan och får Ob5T6 utmattningskrys.",
        # Nya resultat
        11: "I ett försök att imponera med en avancerad kampsportsrörelse, snurrar rollpersonen okontrollerat runt och kräks framför alla närvarande. Ob2T6 Utmattning och -2 på alla sociala färdigheter under nästa timme.",
        12: "Rollpersonen försöker en spektakulär spark men råkar istället sparka sig själv i ansiktet. Ob2T6 Smärta och ett kryss Trauma. Alla närvarande blir så förvånade att de automatiskt missar sin nästa handling.",
        13: "Ett plötsligt krampanfall i båda benen gör att rollpersonen dansar en ofrivillig jig. Ob3T6 Utmattning och kan inte springa under Ob1T6 timmar.",
        14: "Rollpersonen tappar balansen så spektakulärt att det ser ut som en planerad breakdance-rörelse. Ob2T6 Smärta, men alla imponerade åskådare ger +2 på nästa socialslag.",
        15: "En muskel i ryggen låser sig i en mycket obekväm position. Sänk RÖR med tre (-3) under Ob2T6 timmar och får Ob2T6 Smärta.",
        16: "Ett förvirrat ögonblick får rollpersonen att försöka krama sin motståndare istället för att attackera. Båda blir så generade att de får -2 på alla slag nästa runda.",
        17: "En serie av olyckliga rörelser resulterar i att rollpersonen av misstag utför en perfekt piruett. Ob3T6 Utmattning, men imponerar på eventuella åskådare med artistisk läggning.",
        18: "Rollpersonen snubblar så illa att hen börjar rulla nedför närmaste sluttning som ett mänskligt hjul. Ob3T6 Smärta och kan inte stanna förrän efter Ob1T6 rundor.",
        19: "Ett särskilt allvarligt felsteg resulterar i att rollpersonen slår en perfekt kullerbytta bakåt och landar på huvudet. Ob2T6 Trauma och förvirrad under Ob2T6 rundor.",
        20: "Rollpersonen utför en serie så katastrofalt dåliga rörelser att det ser ut som en ny dans. Ob4T6 Utmattning och måste klara ett normalt slag mot VIL för att sluta 'dansa'."
    },
    "narstrid": {
        # Ursprungliga resultat
        1: "Rollpersonen tappar balansen och alla resterande handlingar i rundan blir en nivå svårare (+Ob1T6).",
        2: "Rollpersonen anfaller på ett ställe där motståndaren inte längre befinner sig – förvånad hamnar rollpersonen i obalans och tappar sitt vapen när hen försöker återfå balansen. Slå ett normalt slag (Ob3T6) mot RÖR för att rollpersonen inte skall falla omkull.",
        3: "Rollpersonen slår sig och tappar andan och får enbart utföra instinktiva försvar under denna runda. Dessutom erhåller Ob3T6 utmattningskrys.",
        4: "Rollpersonen tappar greppet om sitt vapen som flyger Ob1T6/2 meter. Riktningen bestäms slumpmässigt. Dessutom blir rollpersonen så förstummad att rollpersonens VINIT–slag blir en nivå svårare (+Ob1T6) under Ob1T6 rundor.",
        5: "Rollpersonen slår ned vapnet hårt i marken och snubblar in i det. Sänk Bryt med ett (–1). Roll-personen får Ob1T6 kryss Smärta i manövern.",
        6: "Rollpersonen lyckas med att slå till sig själv riktigt hårt med en relativt ofarlig del av vapnet (exempelvis skaftet eller bredsidan). Rollpersonen får Ob1T6 kryss Smärta och blir automatiskt försvarare nästa Ob1T6 rundor.",
        7: "Rollpersonen lyckas trassla in sig i sina kläder (eller sitt pansar om sådant finns). Det krävs Ob3T6 mot RÖR för att ta sig loss. Roll-personen får slå en gång per runda. Under tiden som rollpersonen är intrasslad får rollpersonen inte göra någonting annat än att undvika (även ducka, gå bakåt, hoppa och sidrörelser). Observera att försöka ta sig loss räknas som en handling. Att undvika då man är intrasslad är en nivå svårare (+Ob1T6).",
        8: "Rollpersonen lyckas med konststycket att träffa sig själv i huvudet. Skadeverkan blir dock halva den vanliga. Slå skadeverkan som vanligt och halvera denna. Pansar skyddar som vanligt.",
        9: "Rollpersonen snubblar och faller illa – rollpersonen får ett (1) kryss Trauma, Ob1T6 kryss Smärta och ligger ned. Även vapnet tar stryk – sänk Bryt med ett (–1). Rollpersonen räknas som liggande.",
        10: "Rollpersonen vrickar foten vid en klumpig handling och faller till marken. Sänk FÖR med två (–2) under Ob1T6 dagar samt anteckna Ob1T6 kryss Smärta. Rollpersonen ligger ned och kan inte resa sig under Ob1T6 rundor.",
        # Nya resultat
        11: "Ett desperat svep med vapnet resulterar i att rollpersonen klipper av sin egen bältesrem. Ob1T6 rundor går åt till att försöka hålla byxorna uppe, alternativt acceptera situationen och kämpa med reducerad värdighet.",
        12: "I ett försök att vara extra dramatisk, kastar rollpersonen upp sitt vapen för att fånga det igen. Vapnet landar istället på en oskyldig åskådare. Normal skada på det olyckliga offret.",
        13: "Rollpersonen svingar sitt vapen så entusiastiskt att hen snurrar ett helt varv och blir yr. Ob2T6 Utmattning och alla slag blir en nivå svårare under nästa Ob1T6 rundor.",
        14: "Ett kraftfullt men misslyckat hugg får vapnet att vibrera så kraftigt att rollpersonens tänder skallrar. Ob2T6 Smärta och kan inte tala normalt under Ob1T6 minuter.",
        15: "Vapnet fastnar i en spricka i marken eller väggen. Kräver ett svårt slag (Ob4T6) mot STY för att dra loss det. Sänk vapnets Bryt med två (-2) när det väl kommer loss.",
        16: "Ett särskilt klumpigt svep med vapnet resulterar i att rollpersonen av misstag kastar det som ett kastvapen. Slå ett normalt slag mot KAS för att se var det landar.",
        17: "Rollpersonen tappar greppet om vapnet som flyger iväg och fastnar i taket/ett träd/annan svåråtkomlig plats. Ob2T6 rundor och ett normalt slag mot RÖR krävs för att få ner det.",
        18: "I ett ögonblick av total förvirring försöker rollpersonen använda vapnet som musikinstrument istället för att attackera. Alla närvarande blir så förbryllade att de missar sin nästa handling.",
        19: "Ett missriktat hugg får vapnet att studsa tillbaka med sådan kraft att rollpersonen gör en ofrivillig bakåtvollt. Ob3T6 Smärta och ett kryss Trauma. Alla imponerade åskådare applåderar spontant.",
        20: "Vapnet går helt av på mitten i ett spektakulärt misslyckande. Båda delarna flyger iväg Ob2T6 meter i slumpmässiga riktningar och riskerar att träffa närvarande (använd vanliga kastregler)."
    },
    "avstand": {
        # Ursprungliga resultat
        1: "Skottet går av för tidigt och träffar i marken framför rollpersonen. Rollpersonen tappar kontroll över vapnet, hamnar i obalans och får inget gjort under denna och nästa runda.",
        2: "Rollpersonen tappar greppet om sitt vapen som flyger iväg Ob1T6/2 meter. Riktningen bestäms slumpmässigt. Rollpersonen blir automatiskt förvinad under 1T6 rundor.Rollpersonen tappar greppet om sitt vapen som flyger iväg Ob1T6/2 meter. Riktningen bestäms slumpmässigt. Rollpersonen blir automatiskt försvarare under 1T6 rundor.",
        3: "Projektilen går helt fel upp i skyn och rollpersonen tittar förundrat på denna, och blir försvarare i två rundor.",
        4: "Finns det någon annan person i skottfältet blir denne träffad istället för det tilltänkta målet. Möjliga offer slår ett normalsvårt slag (Ob3T6) mot Tur för att undvika att bli träffad. Finns flera offer i närheten blir den med sämst effekt träffad av projektilen.",
        5: "Rollpersonen vrickar foten vid en klumpig handling och faller till marken. Sänk FÖR med två (–2) under Ob1T6 dagar samt anteckna Ob1T6 kryss Smärta. Rollpersonen ligger ned och kan inte resa sig under Ob1T6 rundor.",
        6: "Rollpersonen lyckas trassla in sig i sina kläder (eller sitt pansar om sådant finns). Det krävs Ob3T6 mot RÖR för att ta sig loss. Rollpersonen får slå en gång per runda. Under tiden som rollpersonen är intrasslad får rollpersonen inte göra någonting annat än att undvika (även ducka, gå bakåt, hoppa och sidsteg). Observera att försöka ta sig loss räknas som en handling. Att undvika då man är intrasslad är en nivå svårare (+Ob1T6).",
        7: "Rollpersonen tar i extra mycket och överbelastningen gör att vapnet riskerar att gå sönder. Bågar och armborst går vanligen sönder genom att strängen brister. Andra vapen bryts vanligen.",
        8: "Rollpersonen lyckas med att göra sig själv illa (exempelvis genom att komma i vägen för strängen). Rollpersonen får Ob1T6 kryss Smärta.",
        9: "Rollpersonen träffar sig själv i foten. Slå normal skada och applicera på foten. Vilken fot som drabbas bestäms slumpmässigt.",
        10: "Rollpersonen snubblar och faller illa – rollpersonen får ett (1) kryss Trauma, Ob1T6 kryss Smärta och ligger ned. Även vapnet tar stryk – sänk Bryt med ett (–1). Rollpersonen räknas dessutom som liggande.",
        # Nya resultat
        11: "Ett plötsligt vindkast får projektilen att göra en perfekt loop och landa i rollpersonens bakficka. Ob1T6 Smärta och måste spendera nästa runda med att försiktigt plocka ut den.",
        12: "Rollpersonen blir så nervös att hen siktar med fel ände av vapnet. Ob2T6 Utmattning av ren förlägenhet och -2 på alla socialslag under nästa timme av ren skam.",
        13: "Ett spektakulärt misslyckande resulterar i att projektilen studsar mellan tre olika ytor innan den landar i rollpersonens lunchlåda. Maten är förstörd och rollpersonen får Ob2T6 extra Utmattning senare under dagen.",
        14: "Vapnet fastnar i rollpersonens kläder på ett så intrikat sätt att det skulle imponera på en cirkusartist. Ob3T6 mot RÖR för att ta sig loss, och eventuella åskådare kan inte låta bli att skratta.",
        15: "Ett kritiskt felskott får projektilen att träffa närmaste ljuskälla, vilket skapar en dramatisk mörkläggning. Alla närvarande blir överraskade och missar sin nästa handling.",
        16: "Rollpersonen blir så fokuserad på att sikta att hen glömmer bort att faktiskt skjuta. Står kvar med perfekt sikte men totalt handfallen i Ob1T6 rundor.",
        17: "Ett våldsamt misslyckande gör att vapnet går sönder på ett så spektakulärt sätt att delarna bildar ett improviserat konstverk. Vapnet är förstört men kan säljas som modern konst för dubbla priset.",
        18: "Rollpersonen lyckas skjuta sin egen utrustning. Slå 1T6: 1-2: Vapenbältet går sönder, 3-4: En väska öppnas och tappar sitt innehåll, 5-6: En vattenlägel spricker och blöter ner all utrustning.",
        19: "Ett makalöst dåligt skott resulterar i att projektilen gör en perfekt cirkel runt rollpersonen och landar precis där den började. Ob3T6 Utmattning av ren förvirring.",
        20: "Ett så extremt felskott att projektilen försvinner spårlöst. Efter Ob1T6 rundor återvänder den från en oväntad riktning, nu täckt av mystiska runor. Ingen skada, men projektilen bör undersökas av en lärd person.",
    },
    "skoldar": {
        # Ursprungliga resultat
        1: "Skölden hamnar snett och kräver ett normalsvårt (Ob3T6) slag mot RÖR för att justeras. Rollpersonen får göra ett försök per runda och varje försök räknas som en handling. Om skölden inte justeras blir alla blockeringar med skölden en nivå svårare (+Ob1T6).",
        2: "Skölden fastnar i utrustning och rollpersonen får inte loss den förrän rollpersonen lyckas med ett normalt slag (Ob3T6) mot RÖR. Rollpersonen får slå en gång per runda. Under tiden som rollpersonen är intrasslad får rollpersonen inte göra någonting annat än att undvika (även ducka, gå bakåt, hoppa och sidosteg). Observera att försöka ta sig loss räknas som en handling. Att undvika då man är intrasslad är en nivå svårare (+Ob1T6).",
        3: "Med ett snyggt kast lyckas rollpersonen få skölden att flyga iväg Ob1T6/2 meter. Riktningen bestäms slumpmässigt. Rollpersonen blir automatiskt försvarare under Ob1T6 rundor.",
        4: "Rollpersonen tappar balansen och faller handlöst till marken – rollpersonen räknas numera som liggande.",
        5: "Rollpersonen slår sig och tappar andan. Ob3T6 utmattningskryss markeras.",
        6: "Sköldens remmar brister och skölden faller till marken – rakt på rollpersonens fot. Rollpersonen får därför två kryss (+2) Smärta. Om rollpersonens fot är täckt av stel rustning kan Smärtan ignoreras.",
        7: "Rollpersonen snubblar och faller illa – rollper sonen får ett (1) kryss Trauma, Ob1T6 kryss Smärta och ligger ned. Även skölden tar skada – slå sköldens skadeverkan och jämför med Bryt. Använd normala brytregler. Rollpersonen räknas efter fallet som liggande.",
        8: "Rollpersonen snubblar och slår ned skölden hårt i marken. Sänk Bryt med ett (–1).",
        9: "Rollpersonen slår sköldkanten i sin egen panna eller annat område som är någorlunda oskyddat och får Ob2T6 kryss Smärta. Rollpersonen faller som en fura till marken och räknas därefter naturligtvis som liggande.",
        10: "Rollpersonen vrickar foten vid en klumpig handling och faller till marken. Sänk FÖR med två (–2) under Ob1T6 dagar samt anteckna Ob1T6 kryss Smärta. Rollpersonen ligger ned och kan inte resa sig under Ob1T6 rundor.",
        # Nya resultat
        11: "Ett oväntat snedspark får skölden att fastna på rollpersonens rygg som ett sköldpaddsskal. Ob2T6 mot RÖR för att ta sig loss, och kan bara röra sig krypande under tiden.",
        12: "Rollpersonen tappar greppet om skölden och försöker fånga den genom att jonglera med den. Slå tre slag mot RÖR (Ob3T6) - misslyckas något får rollpersonen Ob1T6 Smärta för varje misslyckat slag.",
        13: "Ett spektakulärt misslyckande resulterar i att skölden fastnar som en frisbee i taket/ett träd. Alla närvarande är för imponerade för att attackera nästa runda.",
        14: "Skölden slår en perfekt kullerbytta och landar som en tallrik med rollpersonens matsäck uppradad på den. Maten är förstörd och rollpersonen får Ob2T6 extra Utmattning senare under dagen.",
        15: "Ett särskilt klumpigt försök att blockera får skölden att rotera som ett hjul. Rollpersonen måste jaga den i Ob1T6 rundor medan den rullar omkring på slagfältet.",
        16: "Ett förvirrat ögonblick får rollpersonen att försöka använda skölden som ett parasoll. Ob2T6 Utmattning av ren förlägenhet och -2 på alla socialslag under nästa timme.",
        17: "Skölden fastnar på rollpersonens huvud som en löjlig hatt. Ob3T6 mot RÖR för att ta loss den, och alla slag som kräver syn blir två nivåer svårare under tiden.",
        18: "Ett våldsamt snurrande får skölden att fungera som en improviserad fläkt som blåser omkull lätta föremål och skapar förvirring. Alla närvarande måste ducka eller få Smärta från flygande småföremål.",
        19: "Ett kritiskt felsteg får skölden att fungera som en perfekt spegel som bländar rollpersonen. Ob2T6 Smärta och kan inte använda några färdigheter som kräver syn under Ob1T6 rundor.",
        20: "Ett så makalöst misslyckande att skölden på något sätt lyckas blockera rollpersonens egna attacker under resten av striden. Alla egna attacker blir en nivå svårare tills skölden tas av (kräver en handling)."
      }
}