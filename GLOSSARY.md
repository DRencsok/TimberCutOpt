# TimberCutOpt

Plans how to cut a list of timber pieces from stock boards so that as little timber as possible is bought and wasted.

## Language

**Waste**:
The timber bought but not used in pieces: every offcut plus the wood lost to saw cuts (kerf). Used as the term in code, API and on screen.
_Avoid_: Lost, scrap

**Stack**:
A group of boards in a plan with the same section, stock length and cuts, shown once with a count of how many boards it holds.
_Avoid_: Pile, batch
