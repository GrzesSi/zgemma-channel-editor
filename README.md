# zgemma-channel-editor

Polski edytor listy kanałów obsługiwany przez przeglądarkę na komputerze lub telefonie. Wtyczka odczytuje listę kanałów z dekodera, na którym jest zainstalowana. Osoby korzystające z tego samego dekodera edytują tę samą listę.

Wersja 1.0.3 — wydanie testowe. Docelowe środowisko: OpenATV 8 z Pythonem 3 i OpenWebif. Integrację sprawdzono w symulacji, a stronę na komputerze i telefonie. Działanie na rzeczywistym dekoderze oraz innych obrazach Enigma2 wymaga weryfikacji. Starsze systemy z Pythonem 2 nie są obsługiwane.

## Możliwości

- Układanie kanałów i grup przeciąganiem lub przyciskami góra/dół.
- Tworzenie i zmienianie nazw grup, kopiowanie i przenoszenie kanałów.
- Wyszukiwanie telewizji i radia, cofanie i ponawianie zmian.
- Stały typ kanału pod jego nazwą: m.in. wiadomości, filmy, seriale, sport, muzyka i ogólny. Typ jest rozpoznawany po nazwie stacji; nierozpoznane stacje mają etykietę „Typ nieokreślony”.
- Import i eksport list w formacie .tar.gz.
- Zapis na dekoderze z automatyczną kopią i możliwością przywrócenia.

## Instalacja

[Pobierz paczkę ZIP](https://github.com/GrzesSi/zgemma-channel-editor/releases/download/v1.0.3/zgemma-channel-editor_1.0.3.zip) · [Pobierz pakiet IPK](https://github.com/GrzesSi/zgemma-channel-editor/releases/download/v1.0.3/enigma2-plugin-extensions-zgemma-channel-editor_1.0.3_all.ipk) · [Wszystkie pliki wydania](https://github.com/GrzesSi/zgemma-channel-editor/releases/tag/v1.0.3)

Wybierz jeden sposób instalacji: paczkę ZIP przez WinSCP albo pakiet IPK. Pobierz plik z sekcji **Releases → Assets**. Do instalacji przez WinSCP użyj `zgemma-channel-editor_1.0.3.zip`; pliki **Source code (zip)**, **Source code (tar.gz)** oraz ZIP z przycisku **Code** zawierają źródła i mają inny układ folderów.

1. Upewnij się, że na dekoderze jest OpenWebif.
2. Rozpakuj paczkę instalacyjną na komputerze.
3. Połącz się z własnym dekoderem przez WinSCP, używając jego adresu IP i danych dostępu.
4. Skopiuj cały folder `KanalowyEditor` do `/usr/lib/enigma2/python/Plugins/Extensions/`. Plik wtyczki ma znaleźć się dokładnie pod adresem `/usr/lib/enigma2/python/Plugins/Extensions/KanalowyEditor/plugin.py`. Nie kopiuj folderu nadrzędnego paczki ani samego pliku ZIP.
5. Zrestartuj interfejs użytkownika (GUI) dekodera.
6. Otwórz **Wtyczki → zgemma-channel-editor**. Zobaczysz adres strony.
7. Otwórz w przeglądarce `http://ADRES_IP_DEKODERA:8877`, zastępując `ADRES_IP_DEKODERA` adresem swojego urządzenia.

Aby zainstalować pakiet IPK:

1. Pobierz `enigma2-plugin-extensions-zgemma-channel-editor_1.0.3_all.ipk` z sekcji **Releases → Assets**. Plik `.sha256` służy do sprawdzenia pobrania i nie jest instalatorem.
2. Połącz się z dekoderem przez WinSCP i skopiuj plik `.ipk` do folderu `/tmp` **na dekoderze**. Pakietu IPK nie rozpakowuj.
3. Otwórz terminal połączony z dekoderem, zaloguj się jako `root` i wykonaj:

```sh
opkg install /tmp/enigma2-plugin-extensions-zgemma-channel-editor_1.0.3_all.ipk
```

4. Po zakończeniu instalacji zrestartuj GUI dekodera. Następnie otwórz **Wtyczki → zgemma-channel-editor** i użyj wyświetlonego adresu w przeglądarce na komputerze lub telefonie w tej samej sieci.

Przy aktualizacji przez WinSCP podmień cały folder wtyczki. Przy aktualizacji przez IPK zainstaluj pakiet nowszej wersji. Zrestartuj GUI i odśwież stronę przez Ctrl+F5.

Jeżeli instalator zgłasza brak pliku, sprawdź, czy IPK znajduje się w `/tmp` na dekoderze i czy jego nazwa zgadza się z poleceniem. Jeśli wtyczka nie pojawia się w menu, sprawdź docelową ścieżkę `plugin.py`, wykonaj restart GUI i upewnij się, że system korzysta z Pythona 3. Komunikat o brakującym module lub zależności wymaga odczytania jego pełnej treści; nie oznacza automatycznie uszkodzonej paczki.

## Korzystanie i kopie

Program wczytuje bieżącą listę z dekodera. Nie zawiera żadnej gotowej listy kanałów, danych dostępowych ani ustawień tunerów. Importuj tylko własne paczki list kanałów.

Układanie i import nie zapisują zmian od razu. Zapis następuje po kliknięciu **Zapisz na dekoderze** i potwierdzeniu. Przed zapisem i przywróceniem powstaje kopia w `/etc/enigma2/kanaly_editor_kopie/`.

Kanały usunięte z grup pozostają w katalogu; przy zapisie wpisy bez grupy trafiają do „Pozostałe kanały”. Przy zwykłym układaniu bazy `lamedb` i `lamedb5` pozostają identyczne bajt w bajt. Program nie zmienia ustawień tunerów ani sieci. Zagnieżdżone grupy nie są obsługiwane.

Edytor otwiera się bez logowania i jest przeznaczony do zaufanej sieci lokalnej. Nie przekierowuj portu 8877 do internetu.

## Przygotowanie paczek ze źródeł

Na komputerze z Pythonem 3 uruchom:

```sh
python -m unittest discover -s tests -v
python build_package.py
```

Pliki ZIP, IPK i ich sumy SHA-256 powstaną w folderze `dist`. Budowanie nie wymaga danych ani połączenia z dekoderem.

## Publikacja

Projekt: https://github.com/GrzesSi/zgemma-channel-editor. Dodaj zawartość tego folderu do repozytorium. W sekcji **Releases** utwórz wydanie `v1.0.3`, zaznacz **pre-release** i dołącz paczki ZIP, IPK oraz pliki SHA-256 z `dist`. Do opisu wydania możesz użyć pliku `RELEASE_NOTES.md`.

Na forum zamieść tekst z `POST_NA_FORUM.txt` oraz paczkę instalacyjną ZIP; po utworzeniu repozytorium możesz dołączyć jego link. Publikacja na forum nie oznacza dodania wtyczki do oficjalnego katalogu OpenATV.

Dokumentacja GitHub: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
