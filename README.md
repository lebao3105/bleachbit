# BleachBit

BleachBit cleans files to free disk space and to maintain privacy.

## Running from source

To run BleachBit without installation, get the soure code and then run these commands:

    make -C po local # build translations
    python3 bleachbit.py

Then, review the preferences.

Then, select some options, and click Preview.  Review the files, toggle options accordingly, and click Delete.

For information regarding the command line interface, run:

    python3 bleachbit.py --help

Read more about [running from source](https://docs.bleachbit.org/dev/running-from-source-code.html).

## About this wxPython port

I made this port in order to make this work on macOS as well and help Windows users have a real system look without using any GTK theme (since it's not GTK on Windows anymore, it's Win32 with default build settings).

The work is in progress, but I'm pretty alone here... This is a HUGE big project!

What I have done (inside and outside [bleachbit/](bleachbit/)):

* Patched system-dependant modules to not use GTK code if any
* Ported dialogs (Make chaff, About, System infomation) to wxPython
* Ported main window & GUI entrypoint to wxPython (not completed)
* Ported all universal GUI functions to use wxPython and cross-platform solutions
* Kept all strings for translation
* Removed Windows theme for GTK as not needed anymore

What I have not done:
* All packaging-related stuffs (so MUCH FILES)
* Fully port ~~Preferences~~ (completed) and main window
* Add macOS search paths
* Update tests (they're a bunch of files)

For macOS search paths for the cleaner, I suggest you ask in forums, or look at programs such as iCleaner (for jailbroken device). Create a fork or message me about what did you find!

### FAQ

Q: ETA?

A: It's in /dev/null (no ETA) for now. Especially that I'm going to have a lot of things else to do this summer.

Q: Is resolving packaging files (e.g bleachbit.spec) so hard?

A: Yes. Look at bleachbit.spec and NSIS files for windows. It's a huge mess.

## Links

* [BleachBit home page](https://www.bleachbit.org)
* [Support](https://www.bleachbit.org/help)
* [Documentation](https://docs.bleachbit.org)

## Localization

Read [translation documentation](https://www.bleachbit.org/contribute/translate) or translate now in [Weblate](https://hosted.weblate.org/projects/bleachbit/), a web-based translation platform.

<a href="https://hosted.weblate.org/engage/bleachbit/">
      <img src="https://hosted.weblate.org/widgets/bleachbit/-/multi-auto.svg" alt="Translation status"/>
</a>

## Licenses

BleachBit itself, including source code and cleaner definitions, is licensed under the [GNU General Public License version 3](COPYING), or at your option, any later version.

markovify is licensed under the [MIT License](https://github.com/jsvine/markovify/blob/master/LICENSE.txt).

## Development
* [BleachBit on AppVeyor](https://ci.appveyor.com/project/az0/bleachbit)  ![Build status](https://ci.appveyor.com/api/projects/status/7p8amofd7rv7n268?svg=true)
* [BleachBit on Travis CI](https://travis-ci.com/github/bleachbit/bleachbit)  ![Build Status](https://travis-ci.com/bleachbit/bleachbit.svg?branch=master)
* [CleanerML Repository](https://github.com/bleachbit/cleanerml)
* [BleachBit Miscellaneous Repository](https://github.com/bleachbit/bleachbit-misc)
* [Winapp2.ini Repository](https://github.com/bleachbit/winapp2.ini)
