# Title

# Abstract
_A 150 word description of the project idea, goals, dataset used. What story you would like to tell and why? What's the motivation behind your project?_

# Research questions and hypotheses

* What recurring patterns and regularities make Schubert's dances so intuitively appealing and easy to grasp?
* Are the different dance types musically distinguishable? Which features will a classifier use to distinguish the different dance types? Hypothetically, these features will include:
  * meter
  * melodic motives and shapes
  * musical form
  * harmonic progressions
  * rhythmic markup
  * musical texture
  * relation between the two hands

# Dataset
The dataset consists of the scores of all 394 dances, written by Franz Schubert (1797-1828), in MuseScore 3 XML format.

The dances include short pieces in triple meter, such as:
* Waltzs
* Minuets
* Ländlers
* Deutsche
* Cotillions

And short pieces in binary meter, such as:
* Ecossaises
* Galops

Most of this dataset was crawled from the web and cleaned by ourselves,
and the rest has been directly typesetted in a group effort.

The dataset is labelled at the piece level, so we have the name of the dance types for each piece.
But no label exists (yet) at the section or chord levels.

# A list of internal milestones up until project milestone 2
31.10
* Typeset the final dances (our dataset are scores in MuseScore 3 format).
* Explore XML structures of the scores.

07.11
* Decide on the inner representation of scores (we parse MuseScore 3 format to a cleaner, more usuable format).
* Finish the tool able to playback parsed scores.

14.11
* First version of the parser, able to extract basic features such as:
  * Chords/notes
  * Rests
  * Sections

21.11
* Extract descriptive statistics from the dataset, such as:
  * distribution of dance types.
  * distribution of keys and key profiles.
* Ensure the parser fully works with idiosyncratic MuseScore 3 files (i.e. works as expected with our whole dataset).

# Questions for TAa
_Add here some questions you have for us, in general or project-specific._


