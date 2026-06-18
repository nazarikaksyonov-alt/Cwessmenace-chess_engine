============================================================
              CWESS MENACE – CHESS ENGINE
              (Bitboard-based, Python)
============================================================

This is a simple chess engine with a graphical interface (Tkinter).
It uses bitboards for piece representation and alpha-beta pruning
with a configurable depth.

------------------------
QUICK START
------------------------

1. Install Python 3.8 or higher.

   If you don't have Python, install it using 
   "python-manager-26.2.msix" download from python.org
   IMPORTANT: during installation, make sure to check the option
   "Add Python to PATH" – this allows the engine to run correctly.

2. Run the engine.

   Double-click the file "Launch.bat" (or "run.bat") to start the program.
   A console window will open and then the chess GUI will appear.

   If the engine seems to freeze or stop responding, please wait about
   one minute – it may be thinking deeply (especially at higher depths).

3. Change the language.

   The program reads the language setting from the file "lang.txt".
   To switch to English, open "lang.txt" and write:
       en
   (or "eng"). To use Russian, write:
       ru
   (or "rus"). If the file is missing or contains anything else,
   Russian is used by default.

4. Controls.

   - Click a piece to select it, then click a highlighted square to move.
   - Use the buttons on the right:
       "New Game"   – restart the game
       "Switch Color" – play as white or black
       "Exit"       – close the program

------------------------
TROUBLESHOOTING
------------------------

- If the window does not appear, check that Python is installed
  and the required modules (tkinter, copy, etc.) are available.
  All modules are standard in Python, except possibly "tkinter"
  (on Linux you may need to install python3-tk).

- If you see errors about missing "bit_count", your Python version
  is too old (needs 3.8+). Upgrade Python.

- If the engine plays poorly, try increasing MAX_DEPTH in Depth.py
  (but the search will be slower). Depth 3–4 is recommended for
  casual play; depth 5–6 for stronger play (may take several seconds).

- The engine may occasionally make illegal or strange moves – this is
  a work in progress. Please report any bugs.

------------------------
FILES OVERVIEW
------------------------

CwessMenace.py   – main GUI and localisation
Calculations.py  – board representation, move generation, evaluation
Depth.py         – constants (depth, piece values, etc.)
AlphaSort.py     – move sorting (history heuristic)
lang.txt         – language selection (en/ru)
Launch.bat       – batch file to launch the engine

------------------------
CREDITS
------------------------

Developed as a personal project. Enjoy the game!

For support or feedback, please open an issue on the project page
(if available) or contact the author.

============================================================