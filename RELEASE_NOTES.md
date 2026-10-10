# zgemma-channel-editor 1.0.3 — wydanie testowe

Polski edytor listy kanałów obsługiwany przez przeglądarkę. Docelowe środowisko to Zgemma z OpenATV 8, Pythonem 3 i OpenWebif. Zgodność na rzeczywistym dekoderze nie została jeszcze potwierdzona.

W wersji 1.0.3 ujednolicono nazwę zgemma-channel-editor w interfejsie, menu wtyczek, dokumentacji i nazwach paczek. Stały typ kanału jest widoczny pod jego nazwą w grupie i w katalogu. Układanie kanałów i grup, cofanie, import/eksport .tar.gz, automatyczne kopie oraz przywracanie.

Do instalacji wybierz plik z sekcji **Assets**: `zgemma-channel-editor_1.0.3.zip` albo `enigma2-plugin-extensions-zgemma-channel-editor_1.0.3_all.ipk`. Archiwa **Source code** nie są paczkami instalacyjnymi.

Dla ZIP: rozpakuj go i skopiuj folder `KanalowyEditor` do `/usr/lib/enigma2/python/Plugins/Extensions/`. Dla IPK: skopiuj plik do `/tmp` na dekoderze i w terminalu dekodera wykonaj `opkg install /tmp/enigma2-plugin-extensions-zgemma-channel-editor_1.0.3_all.ipk`. Po instalacji zrestartuj GUI. Pełna instrukcja jest w README projektu. Paczki nie zawierają list kanałów ani danych dostępowych.

Strona i operacje na listach zostały sprawdzone lokalnie; integracja Enigma2/Twisted w symulacji. Działanie na rzeczywistym dekoderze wymaga weryfikacji. Edytor jest przeznaczony do zaufanej sieci lokalnej, bez wystawiania portu 8877 do internetu.
