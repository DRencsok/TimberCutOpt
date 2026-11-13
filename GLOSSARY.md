# TimberCutOpt

Plans how to cut a list of timber pieces from stock boards so that as little timber as possible is bought and wasted.

## Language

**Waste**:
The timber bought but not used in pieces: every offcut plus the wood lost to saw cuts (kerf). Used as the term in code, API and on screen.
_Avoid_: Lost, scrap

**Stack**:
A group of boards in a plan with the same section, stock length and cuts, shown once with a count of how many boards it holds.
_Avoid_: Pile, batch

**Section**:
The cross-section and grade of a piece of timber, written as a free label such as `47x100 C24`. Pieces are only cut from stock of the same section (decision 4). In the frontend, "section" always means this, never a part of the page.
_Avoid_: Profile, size, dimension

**Offcut**:
The timber left at the end of a board after its last piece. Every offcut is part of the waste.
_Avoid_: Remnant, leftover, scrap

**Kerf**:
The width of timber one saw cut turns into dust, in whole millimetres (decision 2). Used as the term in code and API. On screen it is called "saw cut", the word people use in a workshop.
_Avoid_: Blade width, cut loss
