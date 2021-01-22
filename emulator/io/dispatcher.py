"""
This file defines the `Dispatcher` class.

This is a neat way to generate a call chain that dispatches messages
by their type. For example:

```
class AbcMessage:
    pass
class Message1(AbcMessage):
    pass
class Message2(AbcMessage):
    pass

class Controller:
    DISPATCH = Dispatcher()

    def incoming(self, message):
        if self.DISPATCH.dispatch(self, message):
            # message was processed
        else:
            # unknown message

    @DISPATCH.handler(Message1)
    def on_msg1(self, val):
        # handle msg1

    @DISPATCH.handler(Message2)
    def on_msg2(self, val):
        # handle msg2

    @DISPATCH.unhandler
    def on_other(self, val):
        # handle other
        if processed:
            return True
        else:
            return False
```

The unhandler is expected to return a bool indicating whether this
message was handled outside this dispatcher.
"""

from rpython.rlib.objectmodel import always_inline, not_rpython


class Dispatcher:
    def __init__(self):
        def noop(slf, val):
            return False

        @always_inline
        def dflt(slf, val):
            return self._unhandled(slf, val)

        self._unhandled = noop
        self.dispatch = dflt

    @not_rpython
    def handler(self, tp):
        @not_rpython
        def annotate(func):
            prev = self.dispatch

            @always_inline
            def impl(slf, val):
                if isinstance(val, tp):
                    func(slf, val)
                    return True
                else:
                    return prev(slf, val)

            self.dispatch = impl
            return func
        return annotate

    @not_rpython
    def unhandler(self, func):
        self._unhandled = func
        return func
