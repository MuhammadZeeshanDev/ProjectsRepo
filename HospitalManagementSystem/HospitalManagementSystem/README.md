# Hospital Management System (Reception Desk)

A Java Swing desktop application built for a semester project, modeled on
how a real hospital front desk actually works:

**OPD (check-up) → possibly referred to → Emergency (serious case) →
possibly shifted to → Wards (bed admission)**, with a separate
**Appointments** desk for booking future visits, and a **Doctors** desk
that every other screen pulls its doctor list from.

## The five panels

1. **OPD** - a patient walks in for a routine/general check-up. The
   receptionist registers their details and symptoms here, and assigns a
   doctor. If the doctor decides it's actually serious, the visit can be
   referred straight into Emergency with one button.

2. **Emergency** - a patient in a serious condition is registered here
   directly (condition: Critical / Serious / Stable). From here they can
   be **shifted to a ward** (the app automatically finds and assigns the
   next free bed) or discharged directly.

3. **Wards** - shows every ward, its total beds, how many are occupied,
   and how many are free, plus a full table of every currently admitted
   patient (with their ward, bed number, doctor, and admission date).
   Discharging a patient here frees their bed immediately.

4. **Appointments** - for booking a *future* visit. The receptionist
   searches for a patient who has already been registered (through OPD
   or Emergency - so their details never need to be typed twice), picks
   a doctor, and picks a date/time. The date/time picker starts at the
   real current date and time (a live clock is shown), can be moved
   forward for upcoming days, cannot be set in the past, and warns if the
   chosen doctor is already booked at that exact time.

5. **Doctors** - the master list of doctors (name, department, phone,
   availability). Every doctor dropdown across OPD, Emergency, and
   Appointments is built from this same list, so adding a doctor here
   makes them selectable everywhere immediately.

A patient is only ever registered once (through OPD or Emergency, looked
up by phone number to avoid duplicates), and that same record is reused
by every other panel - this is what makes Appointments' patient search
work.

## How data is stored

This project does **not** use JDBC/SQL. It uses plain Java file I/O
instead: every table (patients, doctors, OPD visits, emergency cases,
ward admissions, appointments) is a simple pipe-separated `.txt` file
inside a `data/` folder next to the program. The whole relevant file is
rewritten immediately after every add/update, so storage is always
current ("real-time") and nothing needs to be installed or configured to
run the project - no database driver, no setup. All the file-reading
code is isolated in the `storage` package, so swapping to a real
database later (if your instructor requires it) only means rewriting
that one package.

## Project structure

```
src/
  Main.java                     -> program entry point
  model/
    Patient.java                 -> shared patient master record
    Doctor.java                  -> shared doctor master record
    OPDVisit.java                -> one general check-up visit
    EmergencyCase.java           -> one emergency case
    WardAdmission.java           -> one ward bed admission
    Appointment.java             -> one future appointment
  storage/                       -> reads/writes the data/*.txt files
  service/                       -> business logic for each panel
  ui/
    LoginScreen.java
    MainDashboard.java            -> sidebar navigation + shares services
    OPDPanel.java
    EmergencyPanel.java
    WardPanel.java
    AppointmentPanel.java
    DoctorPanel.java
    DoctorOption.java, PatientOption.java  -> small combo-box helpers
  util/
    Theme.java                    -> shared colors/fonts
    Departments.java               -> shared department list
    Wards.java                     -> fixed ward names & bed capacities
```

## Default login

- Username: `receptionist`
- Password: `reception123`

(An `admin` / `admin123` account also works - see `AuthService.java` to
add more staff accounts.)

Five sample doctors are added automatically the first time the app runs,
so there's something to pick from right away.

## How to run

### Option A: IntelliJ IDEA / Eclipse
1. Open the `HospitalManagementSystem` folder as a project.
2. Mark `src` as the Sources Root (usually detected automatically).
3. Run `Main.java`.

### Option B: VS Code
1. **File → Open Folder** and open the `HospitalManagementSystem` folder
   itself (not its parent folder). A `.vscode/settings.json` is already
   included so the Java extension knows `src` is the source folder.
2. Open `src/Main.java` and click **Run** above the `main` method.

If you ever see an error like `SomeClass cannot be resolved to a type`,
it means VS Code's Java extension compiled the project incompletely
(a stale project cache), not a bug in the code. Fix it with:
1. `Ctrl+Shift+P` → **Java: Clean Java Language Server Workspace** → reload window.
2. If it still happens, delete any `bin`/`out` folder inside the project and re-run.

### Option C: Command line (guaranteed to work everywhere)

PowerShell, from inside the `HospitalManagementSystem` folder:
```powershell
mkdir bin -Force
Get-ChildItem -Recurse -Filter *.java -Path src | ForEach-Object { $_.FullName } | javac -d bin -encoding UTF-8 @-
java -cp bin Main
```

Command Prompt / cmd.exe:
```
dir /s /b src\*.java > sources.txt
javac -d bin @sources.txt
java -cp bin Main
```

macOS/Linux:
```
mkdir -p bin
javac -d bin $(find src -name "*.java")
java -cp bin Main
```

The `data/` folder (with the `.txt` files) is created automatically the
first time you run the app, in whatever folder you launched it from.
