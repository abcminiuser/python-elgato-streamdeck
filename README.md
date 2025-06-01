# Python Elgato Stream Deck Library

![Example Deck](ExampleDeck.jpg)

This is an open source Python 3 library to control an
[Elgato Stream Deck](https://www.elgato.com/en/gaming/stream-deck) directly,
without the official software. This can allow you to create your own custom
front-ends, such as a custom control front-end for home automation software.

_________________

[PyPi Project Entry](https://pypi.org/project/streamdeck/) - [Online Documentation](https://python-elgato-streamdeck.readthedocs.io) - [Source Code](https://github.com/abcminiuser/python-elgato-streamdeck)


## Project Status:

Working - you can enumerate devices, set the brightness of the panel(s), set
the images shown on each button, and read the current button states.

Currently the following StreamDeck products are supported in multiple hardware
variants:

* StreamDeck Mini
* StreamDeck Neo
* StreamDeck Original
* StreamDeck Pedal
* StreamDeck Plus
* StreamDeck XL

## Package Installation:

Install the library via pip:

```
pip install streamdeck
```

Alternatively, manually clone the project repository:

```
git clone https://github.com/abcminiuser/python-elgato-streamdeck.git
```

For detailed installation instructions, refer to the prebuilt
[online documentation](https://python-elgato-streamdeck.readthedocs.io), or
build the documentation yourself locally by running `make html` from the `docs`
directory.


## Credits:

I've used the reverse engineering notes from
[this GitHub](https://github.com/alvancamp/node-elgato-stream-deck/blob/master/NOTES.md)
repository to implement this library. Thanks Alex Van Camp!

Thank you to the following contributors, large and small, for helping with the
development and maintenance of this library:

- [admiral0](https://github.com/admiral0)
- [Aetherdyne](https://github.com/Aetherdyne)
- [benedikt-bartscher](https://github.com/benedikt-bartscher)
- [brimston3](https://github.com/brimston3)
- [BS-Tek](https://github.com/BS-Tek)
- [Core447](https://github.com/Core447)
- [dirkk0](https://github.com/dirkk0)
- [dodgyrabbit](https://github.com/dodgyrabbit)
- [dubstech](https://github.com/dubstech)
- [Giraut](https://github.com/Giraut)
- [impala454](https://github.com/impala454)
- [iPhoneAddict](https://github.com/iPhoneAddict)
- [itsusony](https://github.com/itsusony)
- [jakobbuis](https://github.com/jakobbuis)
- [jmudge14](https://github.com/jmudge14)
- [Kalle-Wirsch](https://github.com/Kalle-Wirsch)
- [karstlok](https://github.com/karstlok)
- [Lewiscowles1986](https://github.com/Lewiscowles1986)
- [m-weigand](https://github.com/m-weigand)
- [mathben](https://github.com/mathben)
- [matrixinius](https://github.com/matrixinius)
- [phillco](https://github.com/phillco)
- [pointshader](https://github.com/pointshader)
- [shanna](https://github.com/shanna)
- [spidererrol](https://github.com/Spidererrol)
- [spyoungtech](https://github.com/spyoungtech)
- [Subsentient](https://github.com/Subsentient)
- [swedishmike](https://github.com/swedishmike)
- [TheSchmidt](https://github.com/TheSchmidt)
- [theslimshaney](https://github.com/theslimshaney)
- [tjemg](https://github.com/tjemg)
- [VladFlorinIlie](https://github.com/VladFlorinIlie)

If you've contributed in some manner, but I've accidentally missed you in the
list above, please let me know.


## License:

Released under the [MIT license](LICENSE).
