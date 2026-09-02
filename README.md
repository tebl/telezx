# TeleZX
TeleZX is the kind of thing that you create four hours after you were supposed to go to bed, but were a bit sentimental about years long gone by now. More specifically I was thinking about browsing Teletext-pages on my TV; news, movie reviews and sale ads available at a touch of the remote without much in the way of other distractions. It was a pretty simple text-based affair, 24 rows of text with 40 characters each divided into pages identified by a number between 1 and 999.

Then I thought that I would like to recreate the feeling of browsing Teletext, but it had to work on one of my favourite computers - ZX Spectrum. Mostly because I'm familiar enough with the hardware to write something resembling software for it, but it'll also have to function within its inherent limitations (only 32 characters per line, colour clash and all that).

In order to make this a reality we'll need some content to display, something that I've chosen to separate out into its own separate Github-repository. This repository will be referenced to the software components as a "*document repository*". A document has an ID attached to it, and this is how you'll be accessing content though instead up to 999 pages the system uses a 4-digit hex number. Each document can have up to 99 pages attached to it, and as it's intended for the ZX Spectrum we'll be working with either SCR-files or a custom format based on SpecSCII for a more familiar blocky format. 

The software used for working with such repositories are included here, for more information see TeleZX Editor below. As a proof of concept that the format works I've also implemented an online viewer, see TeleZX Online below. This allows us the ability to browse the content from a modern computer, if we're so inclined.

## TeleZX Editor (and related tools)
Repository includes an extensive amount of Python-scripts for creating and working with *TeleZX document repositories*.

## TeleZX Online
An online viewer has been implemented in Javascript, it has been implemented in such a way that it works with memory structured in the same way as the ZX Spectrum itself. Not exactly what you might consider efficient, but in the age of modern computing that's a compromise I was willing to make. Anyway, check out a deployed copy of it if any of that sounds mildly interesting: 

https://tebl.github.io/telezx/