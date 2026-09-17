# Instalatory CODESYS

Ten katalog jest miejscem docelowym dla pobranych instalatorów CODESYS w
trakcie CI (git-ignored - nic poza tym plikiem tu nie trafia do repo).

CODESYS Development System i CODESYS Control Win V3 nie są publicznie
pobieralne - wymagają konta w CODESYS Store i akceptacji licencji, więc
workflow **nie** ściąga ich bezpośrednio ze store.codesys.com. Zamiast
tego trzeba je raz pobrać ręcznie i wystawić z prywatnego, dostępnego dla
runnera miejsca (np. private GitHub Release asset, Azure Blob z SAS token,
S3 z presigned URL) pod adresami przekazanymi jako sekrety repo:

- `CODESYS_DEVSYS_INSTALLER_URL` - instalator CODESYS Development System
  (V3.5 SP22, np. `CODESYS-3.5.22.0-Setup.exe`).
- `CODESYS_RTE_INSTALLER_URL` - instalator CODESYS Control Win V3 x64
  (np. `CODESYSControlWinV3x64Setup.exe`).

Workflow cache'uje pobrane pliki (`actions/cache`, klucz oparty o
`CODESYS_VERSION`), więc ściąganie ich z prywatnego storage odpala się
tylko przy braku trafienia w cache - kolejne uruchomienia na tym samym
kluczu nie pobierają ich ponownie. Sam proces instalacji (silent install)
uruchamia się jednak w każdym jobie od nowa, bo hostowany runner GitHub
(`windows-latest`) to za każdym razem świeża, jednorazowa maszyna.
