import ast
import os
from pathlib import Path
from typing import Optional, List, Set
import builtins
import sys


class SafeFileAccess:
    """Provides controlled file access for the REPL."""

    def __init__(self, allowed_dirs: Optional[List[str]] = None):
        """
        Initialize safe file access.

        Args:
            allowed_dirs: List of allowed directory paths. If None, uses current directory.
        """
        if allowed_dirs is None:
            allowed_dirs = [os.getcwd()]

        self.allowed_dirs = [Path(d).resolve() for d in allowed_dirs]

    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is within allowed directories."""
        target = Path(path).resolve()
        return any(
            target == allowed or str(target).startswith(str(allowed) + os.sep)
            for allowed in self.allowed_dirs
        )

    def open(self, path: str, mode: str = "r", *args, **kwargs):
        """Safely open a file (read-only by default)."""
        if not self._is_path_allowed(path):
            raise PermissionError(
                f"Access denied to {path}. Not in allowed directories."
            )

        # Restrict to read-only unless explicitly write mode
        if "w" in mode or "a" in mode or "x" in mode or "+" in mode:
            raise PermissionError(f"Write access denied. Use read-only mode.")

        return builtins.open(path, mode, *args, **kwargs)

    def listdir(self, path: str = "."):
        """List directory contents."""
        if not self._is_path_allowed(path):
            raise PermissionError(
                f"Access denied to {path}. Not in allowed directories."
            )
        return os.listdir(path)

    def read_file(self, path: str) -> str:
        """Read entire file as string."""
        with self.open(path, "r") as f:
            return f.read()


class ImportInterceptor:
    """Controls and intercepts module imports."""

    # Dangerous modules that should always be blocked
    BLOCKED_MODULES = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "pathlib",  # Use safe Path instead
        "importlib",
        "exec",
        "eval",
        "compile",
        "urllib",
        "socket",
        "ssl",
        "__main__",
    }

    # Safe modules that can be imported by default
    SAFE_MODULES = {
        "math",
        "random",
        "json",
        "datetime",
        "collections",
        "itertools",
        "functools",
        "string",
        "re",
        "decimal",
        "fractions",
        "statistics",
        "array",
        "numpy",
        "pandas",
    }

    def __init__(
        self,
        allowed_modules: Optional[Set[str]] = None,
        blocked_modules: Optional[Set[str]] = None,
    ):
        """
        Initialize import interceptor.

        Args:
            allowed_modules: Set of module names to allow importing (extends defaults).
            blocked_modules: Set of module names to block (extends defaults).
        """
        self.allowed_modules = self.SAFE_MODULES.copy()
        self.blocked_modules = self.BLOCKED_MODULES.copy()

        if allowed_modules:
            self.allowed_modules.update(allowed_modules)
        if blocked_modules:
            self.blocked_modules.update(blocked_modules)

        # Remove any overlap (blocked takes precedence)
        self.allowed_modules -= self.blocked_modules

        # Store original __import__
        self._original_import = builtins.__import__

    def safe_import(self, name: str, *args, **kwargs):
        """Custom import function that validates module names."""
        # Get the top-level module name
        module_name = name.split(".")[0]

        # Check if module is blocked
        if module_name in self.blocked_modules:
            raise ImportError(
                f"Import of '{module_name}' is not allowed in this REPL. "
                f"Blocked modules: {', '.join(sorted(self.blocked_modules))}"
            )

        # Check if module is allowed
        if module_name not in self.allowed_modules:
            raise ImportError(
                f"Import of '{module_name}' is not allowed. "
                f"Allowed modules: {', '.join(sorted(self.allowed_modules))}"
            )

        # Perform the actual import using the original function
        return self._original_import(name, *args, **kwargs)


class REPL:
    def __init__(
        self,
        allowed_dirs: Optional[List[str]] = None,
        allowed_modules: Optional[Set[str]] = None,
        blocked_modules: Optional[Set[str]] = None,
        cwd: Optional[str] = None,
    ):
        """
        Initialize REPL with optional directory whitelist and module controls.

        Args:
            allowed_dirs: List of directories the REPL can access. Defaults to current directory.
            allowed_modules: Additional modules to allow importing.
            blocked_modules: Additional modules to block from importing.
            cwd: Optional working directory to change to (must be in allowed_dirs).
        """
        self.file_access = SafeFileAccess(allowed_dirs)
        self.import_interceptor = ImportInterceptor(allowed_modules, blocked_modules)

        # Change working directory if specified
        if cwd:
            if not self.file_access._is_path_allowed(cwd):
                raise ValueError(
                    f"Working directory '{cwd}' is not in allowed directories."
                )
            os.chdir(cwd)
            self.cwd = cwd
        else:
            self.cwd = os.getcwd()

        self.namespace = self._create_safe_namespace()

    def _create_safe_namespace(self) -> dict:
        """Create a restricted namespace without dangerous functions."""
        # Start with builtins but remove dangerous ones
        safe_builtins = {
            name: getattr(builtins, name)
            for name in dir(builtins)
            if name
            not in [
                "__import__",  # Use our custom import
                "exec",  # Prevent exec
                "eval",  # Prevent eval (though eval is used internally)
                "compile",  # Prevent compile
                "open",  # Use our safe version
                "input",  # Prevent interactive input
                "breakpoint",  # Prevent debugger
            ]
        }

        # Add safe file access
        safe_builtins["open"] = self.file_access.open
        safe_builtins["read_file"] = self.file_access.read_file
        safe_builtins["listdir"] = self.file_access.listdir

        # Add custom import interceptor
        safe_builtins["__import__"] = self.import_interceptor.safe_import

        return {
            "__builtins__": safe_builtins,
            "Path": Path,  # Safe path manipulation
        }

    def run(self, code: str):
        try:
            # Parse the code to find the last expression
            tree = ast.parse(code)

            if not tree.body:
                return None

            # Check if the last statement is an expression
            last_stmt = tree.body[-1]
            is_last_expr = isinstance(last_stmt, ast.Expr)

            # Check if the last statement is a print call
            is_print_call = False
            if is_last_expr and isinstance(last_stmt.value, ast.Call):
                if (
                    isinstance(last_stmt.value.func, ast.Name)
                    and last_stmt.value.func.id == "print"
                ):
                    is_print_call = True

            if is_last_expr:
                # Execute all but the last statement
                if len(tree.body) > 1:
                    exec(
                        compile(
                            ast.Module(body=tree.body[:-1], type_ignores=[]),
                            filename="<ast>",
                            mode="exec",
                        ),
                        self.namespace,
                    )

                if is_print_call:
                    # Get the first argument to print and return its repr
                    print_call = last_stmt.value
                    if hasattr(print_call, "args") and print_call.args:  # type: ignore sorry
                        # Evaluate the first argument
                        result = eval(
                            compile(
                                ast.Expression(body=print_call.args[0]),  # type: ignore sorry
                                filename="<ast>",
                                mode="eval",
                            ),
                            self.namespace,
                        )
                        return repr(result)
                    else:
                        return None
                else:
                    # Evaluate the last expression and get its value
                    result = eval(
                        compile(
                            ast.Expression(body=last_stmt.value),
                            filename="<ast>",
                            mode="eval",
                        ),
                        self.namespace,
                    )

                    # Display result if not None (like Jupyter)
                    if result is not None:
                        return repr(result)
            else:
                # No expression at the end, just execute everything
                exec(code, self.namespace)
                return None

        except Exception as e:
            return f"{type(e).__name__}: {e}"


if __name__ == "__main__":
    # Optional: Configure allowed directories and modules
    # allowed_dirs = ["/Users/sajals/Documents/Dev/agents_exp/seatbelt"]
    # allowed_modules = {"numpy", "pandas"}  # Add to defaults
    # blocked_modules = {"json"}  # Remove from defaults
    # repl = REPL(allowed_dirs=allowed_dirs, allowed_modules=allowed_modules, blocked_modules=blocked_modules, cwd=allowed_dirs[0])

    repl = REPL()  # Defaults: current directory only, safe modules only
    print("REPL initialized with security controls enabled.")
    print(f"Working directory: {repl.cwd}")
    print(f"Allowed directories: {repl.file_access.allowed_dirs}")
    print(
        f"Allowed modules: {', '.join(sorted(repl.import_interceptor.allowed_modules))}"
    )
    print(
        f"Blocked modules: {', '.join(sorted(repl.import_interceptor.blocked_modules))}"
    )
    print()

    while True:
        user_input = input(">>> ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting REPL.")
            break
        result = repl.run(user_input)
        if result is not None:
            print(result)
