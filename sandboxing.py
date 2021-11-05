import sys
import os
from RestrictedPython.Guards import safe_builtins
from RestrictedPython.PrintCollector import PrintCollector
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
restricted_globals = dict(__builtins__=safe_builtins)
restricted_globals["_print_"] = PrintCollector

print(restricted_globals)
_print_ = PrintCollector
_getattr_ = getattr

src = open(sys.argv[1]).read()

code = compile_restricted(src, '<string>', 'exec')
exec(code, restricted_globals)