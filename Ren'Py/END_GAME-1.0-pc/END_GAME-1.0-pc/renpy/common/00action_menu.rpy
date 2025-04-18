﻿# Copyright 2004-2025 Tom Rothamel <pytom@bishoujo.us>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

init -1500 python:


    ##########################################################################
    # Menu-related actions.

    config.show_menu_enable = {
        "save" : "(not main_menu) and (not _in_replay)",
        "load" : "(not _in_replay)",
        }

    __NoShowTransition = renpy.object.Sentinel("NoShowTransition")

    @renpy.pure
    class ShowMenu(Action, DictEquality):
        """
        :doc: menu_action
        :args: (screen=_game_menu_screen, *args, _transition=config.intra_transition, **kwargs)

        Causes us to enter the game menu, if we're not there already. If we
        are in the game menu, then this shows a screen or jumps to a label.

        `screen` is usually the name of a screen, which is shown using
        the screen mechanism. If the screen doesn't exist, then "_screen"
        is appended to it, and that label is jumped to.
        the screen mechanism with the ``*args`` and ``**kwargs`` passed to
        the screen. If the screen doesn't exist, then "_screen" is appended
        to it, and that label is jumped to, ignoring `args` and `kwargs`.

        If the optional keyword argument `_transition` is given, the
        menu will change screens using the provided transition.
        If not manually specified, the default transition is
        `config.intra_transition`.

        * ShowMenu("load")
        * ShowMenu("save")
        * ShowMenu("preferences")

        This can also be used to show user-defined menu screens. For
        example, if one has a "stats" screen defined, one can
        show it as part of the game menu using:

        * ShowMenu("stats")

        ShowMenu without an argument will enter the game menu at the
        default screen, taken from :var:`_game_menu_screen`.

        Extra arguments and keyword arguments are passed on to the screen
        """
        transition = None  # For save compatibility; see renpy#2376

        def __init__(self, screen=None, *args, **kwargs):
            self.screen = screen
            self.transition = kwargs.pop("_transition", __NoShowTransition)
            self.args = args
            self.kwargs = kwargs

        def predict(self):
            if renpy.has_screen(self.screen):
                renpy.predict_screen(self.screen, *self.args, **self.kwargs)

        def __call__(self):

            if not self.get_sensitive():
                return

            transition = self.transition
            if transition is __NoShowTransition:
                transition = config.intra_transition

            orig_screen = screen = self.screen or store._game_menu_screen

            if not (renpy.has_screen(screen) or renpy.has_label(screen)):
                screen = screen + "_screen"

            # Ugly. We have different code depending on if we're in the
            # game menu or not.
            if renpy.context()._menu:

                if renpy.has_screen(screen):

                    renpy.transition(transition)
                    renpy.show_screen(screen, *self.args, _transient=True, **self.kwargs)
                    renpy.restart_interaction()

                elif renpy.has_label(screen):
                    renpy.transition(transition)

                    ui.layer("screens")
                    ui.remove_above(None)
                    ui.close()

                    renpy.jump(screen)

                else:
                    raise Exception("%r is not a screen or a label." % orig_screen)

            else:
                renpy.call_in_new_context("_game_menu", *self.args, _game_menu_screen=screen, **self.kwargs)

        def get_selected(self):
            screen = self.screen or store._game_menu_screen

            if screen is None:
                return False

            return renpy.get_screen(screen)

        def get_sensitive(self):
            screen = self.screen or store._game_menu_screen

            if screen is None:
                return False

            if screen in config.show_menu_enable:
                return eval(config.show_menu_enable[screen])
            else:
                return True


    @renpy.pure
    class Continue(Action, DictEquality):
        """
        :doc: menu_action

        Causes the last save to be loaded.
        The purpose of this is to load the player's last save
        from the main menu.

        `regexp`
            If present, will be used in `renpy.newest_slot`. The default
            pattern will continue from any save, including quick saves and
            auto saves. If you want to continue from only saves created by
            the player, set this to ``r"\d"``.

        `confirm`
            If true, causes Ren'Py to ask the user if they want to continue
            where they left off, if they are not at the main menu.
        """

        def __init__(self, regexp=r"[^_]", confirm=True):
            self.regexp = regexp
            self.confirm = confirm

        def __call__(self):
            if self.confirm and not main_menu:
                layout.yesno_screen(layout.CONTINUE, Continue(self.regexp, False))
                return

            recent_save = renpy.newest_slot(self.regexp)

            if recent_save:
                renpy.load(recent_save)

        def get_sensitive(self):
            if _in_replay:
                return False
            return renpy.newest_slot(self.regexp) is not None


    @renpy.pure
    class Start(Action, DictEquality):
        """
        :doc: menu_action

        Causes Ren'Py to jump out of the menu context to the named
        label. The main use of this is to start a new game from the
        main menu. Common uses are:

        * Start() - Start at the start label.
        * Start("foo") - Start at the "foo" label.
        """

        def __init__(self, label="start"):
            self.label = label

        def __call__(self):
            renpy.jump_out_of_context(self.label)


    @renpy.pure
    class MainMenu(Action, DictEquality):
        """
        :doc: menu_action

        Causes Ren'Py to return to the main menu.

        `confirm`
            If true, causes Ren'Py to ask the user if he wishes to
            return to the main menu, rather than returning
            directly.

        `save`
            If true, the game is saved in :var:`_quit_slot` before Ren'Py
            restarts and returns the user to the main menu. The game is not
            saved if :var:`_quit_slot` is None.
        """

        save = True

        def __init__(self, confirm=True, save=True):
            self.confirm = confirm
            self.save = save

        def __call__(self):

            if not self.get_sensitive():
                return

            if self.confirm:
                if config.autosave_on_quit:
                    renpy.force_autosave()

                layout.yesno_screen(layout.MAIN_MENU, MainMenu(False, save=self.save))
            else:
                renpy.full_restart(config.game_main_transition, save=self.save)

        def get_sensitive(self):
            return not renpy.context()._main_menu

    _confirm_quit = True

    @renpy.pure
    class Quit(Action, DictEquality):
        """
        :doc: menu_action

        Quits the game.

        `confirm`
            If true, prompts the user if he wants to quit, rather
            than quitting directly. If None, asks if and only if
            the user is not at the main menu.
        """

        def __init__(self, confirm=None):
            self.confirm = confirm

        def __call__(self):

            confirm = self.confirm

            if confirm is None:
                confirm = (not main_menu) and _confirm_quit

            if confirm:
                if config.autosave_on_quit:
                    renpy.force_autosave()

                layout.yesno_screen(layout.QUIT, Quit(False))

            else:
                renpy.quit(save=True)

    @renpy.pure
    class Skip(Action, DictEquality):
        """
        :doc: other_action

        Causes the game to begin skipping. If the game is in a menu
        context, then this returns to the game. Otherwise, it just
        enables skipping.

        `fast`
            If true, skips directly to the next menu choice.

        `confirm`
            If true, asks for confirmation before beginning skipping.
        """

        fast = False
        confirm = False

        def __init__(self, fast=False, confirm=False):
            self.fast = fast
            self.confirm = confirm

        def __call__(self):
            if not self.get_sensitive():
                return

            if config.skipping:
                config.skipping = None
                renpy.restart_interaction()
                return

            if self.confirm:
                if self.fast:
                    if _preferences.skip_unseen:
                        layout.yesno_screen(layout.FAST_SKIP_UNSEEN, Skip(True))
                    else:
                        layout.yesno_screen(layout.FAST_SKIP_SEEN, Skip(True))
                else:
                    layout.yesno_screen(layout.SLOW_SKIP, Skip(False))

                return

            if renpy.context()._menu:
                if self.fast:
                    renpy.jump("_return_fast_skipping")
                else:
                    renpy.jump("_return_skipping")
            else:
                if self.fast:
                    config.skipping = "fast"
                else:
                    config.skipping = "slow"

                renpy.restart_interaction()

        def get_selected(self):
            if self.fast:
                return config.skipping == "fast"
            else:
                return config.skipping and config.skipping != "fast"

        def get_sensitive(self):
            if not config.allow_skipping:
                return False

            if not _skipping:
                return False

            if store.main_menu:
                return False

            if renpy.game.context().seen_current(True):
                return True

            if _preferences.skip_unseen:
                return True

            return False

    @renpy.pure
    class Help(Action, DictEquality):
        """
        :doc: other_action

        Displays help.

        `help`
            A string that is used to find help. This is used in the
            following way:

            * If a label with this name exists, the label is called in
              a new context.
            * Otherwise, this is interpreted as giving the name of a file
              that should be opened in a web browser.

            If `help` is None, :var:`config.help` is used as the default
            value. If it is also None, the :var:`config.help_screen` screen
            is shown in a new context, if it exists. Otherwise, does nothing.
        """

        def __init__(self, help=None):
            self.help = help

        def __call__(self):
            _help(self.help)
