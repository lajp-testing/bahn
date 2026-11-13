"""The note reader on real notes from saved weeks, with what the reveal said was true."""
from dispatch.reader import read

MON, TUE, WED, THU, FRI, NEXT_MON = (day * 1440 for day in (0, 1, 2, 3, 4, 7))


def at(day: int, hour: int, minute: int = 0) -> int:
    return day + hour * 60 + minute


def test_ready_later_with_a_correction():
    facts = read("huolto kesken, valmis huomenna klo 13, ei kun klo 12. vastaanotto klo 8 - 20. avain avainboksissa, koodi 1631. kiitos etukäteen", "fi", at(MON, 9, 6))
    assert facts.ready == at(TUE, 12) and facts.delivery_hours == (480, 1200) and facts.deadline is None and facts.sure


def test_a_correction_in_the_next_sentence_replaces_the_time():
    assert read("Not ready before tomorrow 11:30. Correction: 10:30", "en", at(MON, 19, 34)).ready == at(TUE, 10, 30)
    assert read("Asiakas tulee hakemaan, perillä viim. sunnuntaina klo 17. Korjaus: maanantaina", "fi", at(FRI, 15, 20)).deadline == at(NEXT_MON, 17)


def test_a_denied_time_does_not_count():
    assert read("Kan hämtas i morgon klockan 13.00 och framåt (inte klockan 12.00). Däcken ligger i bilen, ska med", "sv", at(TUE, 10, 29)).ready == at(WED, 13)
    assert read("in the workshop, ready friday 14:30, not tomorrow. destination open weekdays 9:00 - 21:00. key box code 2918.", "en", at(WED, 10, 58)).ready == at(FRI, 14, 30)


def test_release_after_payment():
    assert read("Luovutus vasta kun maksettu, aikaisintaan perjantaina klo 11.30.", "fi", at(WED, 10, 28)).ready == at(FRI, 11, 30)
    assert read("Maksun jälkeen, ei ennen klo 14.30", "fi", at(MON, 11, 0)).ready == at(MON, 14, 30)


def test_hours_in_words_are_working_hours():
    assert read("Voi noutaa huomenna neljästä alkane.", "fi", at(THU, 11, 53)).ready == at(FRI, 16)
    assert read("Valmis noudettavaksi huoomenna puoli yhden jälkeen. Liike auki 9-19", "fi", at(WED, 17, 7)).ready == at(THU, 12, 30)
    assert read("Kiire, asiakas odottaa. Perillä maanantai viiteen mennessä", "fi", at(FRI, 13, 52)).deadline == at(NEXT_MON, 17)


def test_deadlines():
    assert read("Car is ready and waiting, must be at destination by 18:00", "en", at(FRI, 14, 46)).deadline == at(FRI, 18)
    assert read("hi. customer picks it up fri 5:30pm, must be there by then", "en", at(WED, 10, 53)).deadline == at(FRI, 17, 30)
    assert read("Perillä ma klo 18 mennessä. Auto valmis vasta huomenna klo 9", "fi", at(TUE, 10, 18)).deadline == at(NEXT_MON, 18)


def test_site_hours():
    assert read("Hejsn, mottagning till 17, ring kunden en timme innan, tack på förhand.", "sv", at(FRI, 8, 20)).delivery_hours == (None, 1020)
    assert read("liike menee kiiinni klo 1430! kiitos taas", "fi", at(MON, 10, 0)).pickup_hours == (None, 870)
    assert read("liike auki ma-pe 10:stä 16:een", "fi", at(MON, 10, 0)).pickup_hours == (600, 960)
    facts = read("Destination closes at 17:00. Collect before 20:00.", "en", at(MON, 10, 0))
    assert facts.delivery_hours == (None, 1020) and facts.pickup_hours == (None, 1200)
    assert read("Klo 19 jälkeen ei enää luovutuksia, eikun klo 20.", "fi", at(FRI, 16, 58)).pickup_hours == (None, 1200)


def test_the_car_itself():
    assert read("Manuaalivaihteet, kuski tarvii manuaalikortin. Viitenro 480135.", "fi", 0).manual
    assert not read("Hi. Automatic, not a manual.", "en", 0).manual
    assert read("kilvvet poistettu, ota koekilvet.", "fi", 0).plates
    assert not read("lämnas ut efter betalning, tidiagst i morgon kl 13. bilen står på plats 37, nyckeln i kassan", "sv", 0).plates
    assert read("Huom vielä kesärenkaat alla", "fi", 0).summer_tyres
    assert not read("kesärenkaat vanteineen takakontissa", "fi", 0).summer_tyres


def test_harmless_notes_change_nothing():
    for text, language in (("Extra set of tyres in the boot, take along. Ref 163114", "en"), ("2 sarjaa renkaita, toinen sarja kontissa. kiitos taas.", "fi"),
                           ("call 30 min before you arrive", "en"), ("Myyjä kotona huomenna klo 7 - 10.", "fi"), ("Low on fuel. Thanks in advance", "en")):
        facts = read(text, language, at(TUE, 10, 0))
        assert (facts.ready, facts.pickup_hours, facts.delivery_hours, facts.deadline, facts.manual, facts.plates, facts.summer_tyres, facts.sure) == (None, None, None, None, False, False, False, True), text
