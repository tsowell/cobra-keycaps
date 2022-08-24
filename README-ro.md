# Taste pentru Cobra

Acesta este un design custom al tastelor pentru
[calculatorul Cobra](http://cobrasov.com).  Designul este generat de un script
Python hacky care analizează un fișier șablon din WASD Keyboards și generează
fiecare tastă pe baza de un șablon de tastă.

Rezultatul este [`keyboard_cobra.svg`](keyboard_cobra.svg).

## Componentele

### Șablonul de tastatură

Șablonul de tastatură, `keyboard_base.svg`, a fost produs de fișierul de
tastatură a lui WASD Keyboards.  A fost produs urmând instrucțiunile în șablon
pentru a ascunde layout-ul "message" și a seta colorile de fundal pentru
fiecare tastă, și prin crearea unui layout "Cobra" în care scrie scriptul.

### Șablonul de tastă

Șablonul de tastă, `template.svg`, este un dezastru de obiecte șablon pe care
scriptul le extrage și folosează în layout-uri de tastă.

### Scriptul Python

Sunt 7 layout-uri fundamental cu combinațiile diferite de obiecte din șablonul
de tastă.  Funcția `main()` din `mkkb.py` definiște conținutul text/culor a
fiecărei taste în șablon de tastatură.

## Utilizare

`python mkkb.py`

Argumentele de fișiere sunt definit în partea de sus a scriptului.
