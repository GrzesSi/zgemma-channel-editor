"""Display-only genres, independent of bouquet membership and DVB service type."""
import re
import unicodedata


def normalized_name(name):
    name = unicodedata.normalize('NFKD', name.lower().replace('ł', 'l').replace('_', ' '))
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'\b(?:sd|hd|uhd|4k|ultra|poland|polska)\b', ' ', name)
    return re.sub(r'[^a-z0-9]+', '', name)


NAMES = {
    'Wiadomości': 'TVN24|TVN24 BiS|TVP Info|TVP World|Polsat News|Polsat News 2|Polsat News Polityka|Wydarzenia 24|TV Republika|Republika|wPolsce24|wPolsce.pl|Newsmax|Newsmax Polska|CNN|CNN International|CNNI EMEA|BBC News|BBC News Europe|BBC World News|Euronews|Euronews English|Bloomberg|Bloomberg European TV|CNBC|France 24|France 24 (in English)|France 24 (en Francais)|Al Jazeera|Al Jazeera English|TRT World|Rai News 24|CCTV News English|DW English|UATV|Telesur|Kurdistan 24',
    'Filmy': 'Ale Kino+|Kino Polska|Kino TV|Polsat Film|Polsat Film 2|CANAL+ Film|Cinemax|Cinemax 2|Stopklatka|Stopklatka TV|Sundance|Sundance TV',
    'Seriale': 'Polsat Seriale|TVP Seriale|CANAL+ Seriale|BBC First|Epic Drama|Viasat Epic Drama|13 Ulica|Novela TV|NOVELAS+|Dizi',
    'Filmy i seriale': 'HBO|HBO2|HBO3|CANAL+|CANAL+ Premium|CANAL+ 1|CANAL+ Family|SkyShowtime 1|SkyShowtime 2|AMC|AXN|AXN White|AXN Black|AXN Spin|WarnerTV|Warner TV|Paramount Network|Romance TV|TVN Fabula|TVP HD|FX|SciFi|SciFi Universal',
    'Seriale i komedia': 'Comedy Central|Polsat Comedy Central Extra|Comedy Central Extra Polsat|FX Comedy|FOX Comedy',
    'Dokumentalne': 'BBC Earth|Planete+|National Geographic|National Geo|Nat Geo|National Geographic Wild|Nat Geo Wild|Nat Geo People|Animal Planet|CANAL+ Dokument|CANAL+ Discovery|Polsat Doku|Polsat X|Discovery|Discovery Channel|Discovery Science|Science|ID|Investigation Discovery|CI Polsat|Polsat Crime Investigation|Crime Investigation|Historia|History|History 2|H2|TVP Historia|Fokus TV|Adventure|Polsat Viasat Explore|Polsat Viasat History|Polsat Viasat Nature|Viasat Explore|Viasat History|Viasat Nature|Viasat True Crime|Love Nature|Water Planet|NASA TV',
    'Dziecięce': 'TVP ABC|TVP ABC 2|TVP Alfa|Cartoon Network|Cartoonito|MiniMini+|teleTOON+|Disney Channel|Disney XD|Disney Junior|Polsat Jim Jam|JimJam|Nicktoons|Nick Jr|Nickelodeon|TeenNick|BBC Cbeebies|Cbeebies|Rai Gulp|Rai Yoyo|Baby TV|Boomerang',
    'Dziecięce / edukacja': 'Da Vinci',
    'Muzyka': '4Fun.TV|4Fun Dance|4Fun Kids|Eska TV|Eska TV Extra|Eska Rock|Eska Rock TV|Nuta Gold|Nuta TV|MTV|MTV Polska|MTV Live|MTV 00s|MTV 80s|MTV 90s|MTV Hits|MTV Music|Polsat Music|Kino Polska Muzyka|STARS.TV|Vox Music TV|Power TV|Polo TV|Disco Polo Music|Szlagier TV|Mezzo|Mezzo TV|Mezzo Live|Music Box|Nick Music|Clubbing TV|Classica',
    'Sport': 'Motowizja|Golf Zone|Golf Channel|Golf Channel Polska|CANAL+ Now|Fightbox|Fast Funbox|Extreme Sports|Extreme Sports Channel|Motorvision',
    'Gry i e-sport': 'Polsat Games|Gametoon',
    'Rozrywka': 'Polsat Play|BBC Brit|TVP Rozrywka|Polsat Reality|E! Entertainment|Kabaret TV|TLC|TLC Polska',
    'Styl życia': 'Polsat Cafe|TVN Style|BBC Lifestyle|Discovery Life|Active Family|CANAL+ Domo|HGTV|Home TV|MyZen|MyZen TV',
    'Kulinaria': 'CANAL+ Kuchnia|Food Network|24 Kitchen|Kus Kus',
    'Podróże': 'Travel|Travel Channel|Travelxp',
    'Motoryzacja': 'TVN Turbo|Turbo Xtra|Discovery Turbo Xtra|DTX',
    'Kultura': 'TVP Kultura|TVP Kultura 2|Arte|Museum|Museum TV',
    'Religijne': 'Trwam|TV Trwam|EWTN|Padre Pio TV|Vatican Media Europa',
    'Zakupowe': 'TV Okazje|Mango|Mango 24|QVC|HSE24|HSE 24',
    'Dla dorosłych': 'Hustler|Hustler TV|Blue Hustler|Redlight|Private|Brazzers TV|Dorcel TV|Dorcel XXX|Penthouse|Playboy TV',
    'Ogólny': 'TVP 1|TVP1|TVP 2|TVP2|TVP 3|TVP3|TVN|TVN 7|TVN7|Polsat|Polsat 2|Super Polsat|Polsat Rodzina|TV Puls|Puls 2|TV4|TV6|TTV|Nowa TV|WP|Metro|Zoom|Zoom TV|TVS|Antena|Antena TV|TVC|TVC Super|Tele 5|Polonia 1|P1|TVP Polonia|Dla Ciebie TV|Dlia Ciebie|Rai 1|Rai 2|Rai 3|Das Erste|ZDF|RTL|RTL 2|SAT.1|ProSieben|Kabel Eins|RTP International|Tunisie Nationale',
    'Informacje dla abonentów': 'Strefa Abonenta|Dla Abonentow',
}
LOOKUP = {normalized_name(name): genre for genre, names in NAMES.items() for name in names.split('|')}
RADIO_NAMES = {normalized_name(n) for n in (
    'RMF FM', 'RMF Classic', 'RMF MAXX', 'Zlote Przeboje',
    'Jedynka - PR', 'Dwojka - PR', 'Trojka - PR', 'Czworka - PR')}


def channel_genre(name, kind='tv', placeholder=False):
    if placeholder:
        return 'Typ nieokreślony'
    value = normalized_name(name)
    if kind == 'radio' or value in RADIO_NAMES:
        return 'Radio'
    if value in LOOKUP:
        return LOOKUP[value]
    if re.fullmatch(r'tvp3[a-z]+', value):
        return 'Ogólny'
    if re.fullmatch(r'(?:eurosport|eleven(?:sports)?|polsatsport(?:extra|premium|fight)?|canal(?:sport|extra)|bein(?:sports)?|sky(?:sport|sports))\d*', value):
        return 'Sport'
    if re.fullmatch(r'filmbox[a-z0-9]*', value):
        return 'Filmy i seriale'
    if re.fullmatch(r'vod\d+', value):
        return 'Filmy na zamówienie'
    # An unknown station is not necessarily a general-interest channel.
    return 'Typ nieokreślony'

