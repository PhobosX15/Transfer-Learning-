import ast
import os
import textwrap

import nbformat
import pytest


def remove_ipython_magic(source: str) -> str:
    """ Remove ipython 'magic', i.e., the !, % and %% commands. """
    removed_magic = os.linesep.join(
        f"# {line}" if line.startswith("%") else line
        for line in source.split(os.linesep)
    )
    removed_commands = os.linesep.join(
        line.replace("!", "'command:' # !", 1) if line.strip().startswith("!") else line
        for line in removed_magic.split(os.linesep)
    )
    return removed_commands


def make_notebook_source_ast_parsable(source: str) -> str:
    # notebooks allow defining "root indentation" per cell
    source = textwrap.dedent(source)
    # ipython magic is not executable here:
    return remove_ipython_magic(source)


def assert_code_assigns_stop_training_simple_and_true(source: str):
    source = make_notebook_source_ast_parsable(source)
    cell = ast.parse(source)

    assignment_complicated = (
        "Detected assignment to `stop_training` that was more complicated than "
        "a simple `stop_training = True` or `stop_training = False` on line: {}. "
        "Please remove this assignment add `stop_training = False` to run the automated test."
    )
    last_stop_training_value = None
    for assignment in [line for line in cell.body if isinstance(line, ast.Assign)]:
        if "stop_training" not in [getattr(target, "id", None) for target in assignment.targets]:
            continue
        error_with_lineno = assignment_complicated.format(assignment.lineno)
        assert len(assignment.targets) == 1, error_with_lineno
        assert isinstance(assignment.value, ast.Constant), error_with_lineno
        assert isinstance(assignment.value.value, bool), error_with_lineno
        # Since we know `stop_training` is assigned to, we can check its value:
        last_stop_training_value = assignment.value.value

    assignment_false = "`stop_training` is set to `False`. Set it to `True` to run the automated test."
    assert last_stop_training_value is None or last_stop_training_value is True, assignment_false
    return last_stop_training_value


def assert_stop_training_is_true():
    """Check that `Assignment_3_2023.ipynb has `stop_training` set to `True`."""
    with open("Assignment_3_2023.ipynb", "r") as notebook_file:
        notebook = nbformat.read(notebook_file, as_version=nbformat.NO_CONVERT)

    stop_training_is_set = False
    for i, cell in enumerate(notebook.cells):
        if cell.cell_type != "code" or "stop_training" not in cell.source:
            continue
        try:
            stop_training = assert_code_assigns_stop_training_simple_and_true(cell.source)
            if stop_training:
                stop_training_is_set = True
        except AssertionError as e:
            raise AssertionError(f"Issue with assignment of `stop_train` in cell {i}:\n {e.args[0]}") from e
    assert stop_training_is_set, (
            "No assignment to `stop_training` found in the notebook. "
            "It is possible that your assignment is part of a more complex compound statement, e.g., "
            "tuple unpacking. Revert those changes and make a single simple assignment as in the original. "
            "Please add `stop_training = True` to allow the automated test to work."
    )


def test_submission():
    assert_stop_training_is_true()
    try:
        s = os.system(r"jupyter nbconvert --to notebook --execute Assignment_3_2023.ipynb")
        assert s == 0
    except:
        pytest.fail("Error while running notebook.")
