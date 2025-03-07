from dataclasses import dataclass

from mypy.nodes import (
    AssignmentStmt,
    Block,
    MypyFile,
    NameExpr,
    Statement,
    WithStmt,
)

from refurb.checks.common import check_block_like
from refurb.error import Error


@dataclass
class ErrorInfo(Error):
    """
    Due to Python's scoping rules, you can use a variable that has gone "out
    of scope" so long as all previous code paths can bind to it. Long story
    short, you don't need to declare a variable before you assign it in a
    `with` statement:

    Bad:

    ```
    x = ""

    with open("file.txt") as f:
        x = f.read()
    ```

    Good:

    ```
    with open("file.txt") as f:
        x = f.read()
    ```
    """

    code = 127
    msg: str = "This variable is redeclared later, and can be removed here"


def check(node: Block | MypyFile, errors: list[Error]) -> None:
    check_block_like(check_stmts, node, errors)


def check_stmts(body: list[Statement], errors: list[Error]) -> None:
    assign: AssignmentStmt | None = None

    for stmt in body:
        if assign:
            match stmt:
                case WithStmt(
                    body=Block(
                        body=[AssignmentStmt(lvalues=[NameExpr() as name])]
                    )
                ) if (
                    name.fullname
                    and name.fullname
                    == assign.lvalues[0].fullname  # type: ignore
                ):
                    errors.append(ErrorInfo(assign.line, assign.column))

            assign = None

        match stmt:
            case AssignmentStmt(lvalues=[NameExpr()]):
                assign = stmt
