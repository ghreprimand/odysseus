#!/usr/bin/env python3
"""Validate feature-catalog evidence locators against repository source.

Evidence identity is resolved from a language parser where one is available.
The cited line range is treated as generated display metadata and checked only
after the locator has been resolved.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


DISCOVERY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ROOT = DISCOVERY_ROOT.parents[1]
DEFAULT_CATALOG = DISCOVERY_ROOT / "feature-catalog.json"

RESULTS = {
    "valid",
    "invalid-path",
    "invalid-locator",
    "locator-outside-range",
    "range-mismatch",
    "ambiguous",
    "unsupported",
    "file-level-valid",
}

PYTHON_KINDS = {
    "python-function",
    "python-method",
    "python-class",
    "python-variable",
    "python-route",
    "python-module",
    "test-function",
}
JAVASCRIPT_KINDS = {
    "javascript-function",
    "javascript-class",
    "javascript-export",
    "javascript-event",
}
FILE_EXTENSIONS = {
    ".html",
    ".md",
    ".swift",
    ".yaml",
    ".yml",
}
RANGE_RE = re.compile(r"^L([1-9]\d*)-L([1-9]\d*)$")
LEGACY_ROUTE_RE = re.compile(
    r"^@(?P<router>[A-Za-z_]\w*)\."
    r"(?P<method>get|post|put|patch|delete|options|head)"
    r"\(\s*['\"](?P<path>[^'\"]*)['\"]\s*\)$",
    re.IGNORECASE,
)
CANONICAL_ROUTE_RE = re.compile(
    r"^(?P<method>GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+"
    r"(?P<path>\S+)(?:\s+->\s+(?P<function>[\w.]+))?$"
)
SHELL_FUNCTION_RE = re.compile(
    r"^\s*(?:function\s+)?(?P<name>[A-Za-z_]\w*)\s*"
    r"(?:\(\s*\))?\s*\{"
)
MARKDOWN_HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")


@dataclass(frozen=True)
class Located:
    name: str
    kind: str
    start: int
    end: int
    details: dict[str, Any] | None = None

    @property
    def line_range(self) -> str:
        return f"L{self.start}-L{self.end}"


@dataclass
class Validation:
    feature_id: str
    evidence_index: int
    current_evidence: dict[str, Any]
    inferred_kind: str
    locator: str | None
    result: str
    problem: str | None = None
    resolved: Located | None = None
    suggested_kind: str | None = None
    suggested_locator: str | None = None
    generated_line_range: str | None = None
    confidence: str = "high"
    manual_review_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["resolved"] = asdict(self.resolved) if self.resolved else None
        return data


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate discovery evidence identities and line ranges."
    )
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DISCOVERY_ROOT,
        help="Directory for the report and repair queue.",
    )
    return parser.parse_args(argv)


def load_catalog(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("catalog must be an array of feature objects")
    return data


def safe_target(repo_root: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def parse_range(raw: Any) -> tuple[int, int] | None:
    if raw in (None, ""):
        return None
    match = RANGE_RE.fullmatch(str(raw))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def extension_for(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return suffix or "[none]"


def legacy_locator(evidence: dict[str, Any]) -> str | None:
    value = evidence.get("locator", evidence.get("symbol"))
    return value if isinstance(value, str) and value.strip() else None


def infer_kind(evidence: dict[str, Any], target: Path | None) -> str:
    explicit = evidence.get("kind")
    if isinstance(explicit, str) and explicit:
        return explicit

    path = str(evidence.get("path", ""))
    suffix = Path(path).suffix.lower()
    locator = legacy_locator(evidence) or ""

    if suffix == ".py":
        if LEGACY_ROUTE_RE.fullmatch(locator) or CANONICAL_ROUTE_RE.fullmatch(locator):
            return "python-route"
        if path.startswith("tests/") and locator.startswith("test"):
            return "test-function"
        if "." in locator and all(part.isidentifier() for part in locator.split(".")):
            return "python-method"
        if locator.isupper():
            return "python-variable"
        if target and target.is_file():
            try:
                tree = ast.parse(target.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeError):
                return "manual-review"
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == locator:
                    return "python-class"
        return "python-function"
    if suffix == ".js":
        if locator.startswith("on:") or locator.startswith("event:"):
            return "javascript-event"
        if locator and locator[:1].isupper():
            return "javascript-class"
        return "javascript-function"
    if suffix in {".sh", ".bash"}:
        return "shell-function"
    if suffix == ".md":
        return "documentation-section"
    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini"}:
        return "configuration-key"
    if suffix in FILE_EXTENSIONS or Path(path).name in {"Dockerfile"}:
        return "manual-review"
    if not suffix:
        return "manual-review"
    return "manual-review"


class PythonIndex(ast.NodeVisitor):
    """Collect Python declarations, assignments, and decorated routes."""

    def __init__(self) -> None:
        self.symbols: list[Located] = []
        self.routes: list[Located] = []
        self.scope: list[str] = []
        self.constants: dict[str, str] = {}
        self.router_prefixes: dict[str, str | None] = {}

    @classmethod
    def from_path(cls, path: Path) -> "PythonIndex":
        index = cls()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        index._collect_static_values(tree)
        index.visit(tree)
        return index

    def _collect_static_values(self, tree: ast.AST) -> None:
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = self._string_value(node.value)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and value is not None:
                        self.constants[target.id] = value
                    if isinstance(target, ast.Name) and isinstance(
                        node.value, ast.Call
                    ):
                        call_name = self._call_name(node.value.func)
                        if call_name.endswith("APIRouter"):
                            prefix = self._router_prefix(node.value)
                            self.router_prefixes[target.id] = prefix

    def _qualified(self, name: str) -> str:
        return ".".join([*self.scope, name])

    @staticmethod
    def _call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{PythonIndex._call_name(node.value)}.{node.attr}".strip(".")
        return ""

    def _string_value(self, node: ast.AST | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return self.constants.get(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._string_value(node.left)
            right = self._string_value(node.right)
            return left + right if left is not None and right is not None else None
        return None

    def _keyword_string(self, call: ast.Call, name: str) -> str | None:
        for keyword in call.keywords:
            if keyword.arg == name:
                return self._string_value(keyword.value)
        return None

    def _router_prefix(self, call: ast.Call) -> str | None:
        if not any(keyword.arg == "prefix" for keyword in call.keywords):
            return ""
        return self._keyword_string(call, "prefix")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.append(
            Located(
                self._qualified(node.name),
                "python-class",
                node.lineno,
                node.end_lineno or node.lineno,
            )
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified = self._qualified(node.name)
        parent_is_class = bool(
            self.scope
            and any(
                item.kind == "python-class" and item.name == ".".join(self.scope)
                for item in self.symbols
            )
        )
        kind = (
            "test-function"
            if node.name.startswith("test")
            else "python-method"
            if parent_is_class
            else "python-function"
        )
        located = Located(
            qualified, kind, node.lineno, node.end_lineno or node.lineno
        )
        self.symbols.append(located)
        self._collect_routes(node, qualified)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _collect_routes(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, qualified: str
    ) -> None:
        methods = {"get", "post", "put", "patch", "delete", "options", "head"}
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(
                decorator.func, ast.Attribute
            ):
                continue
            method = decorator.func.attr.lower()
            if method not in methods:
                continue
            router = self._call_name(decorator.func.value)
            local_path = (
                self._string_value(decorator.args[0]) if decorator.args else None
            )
            if local_path is None:
                continue
            prefix = self.router_prefixes.get(router)
            full_path = None if router in self.router_prefixes and prefix is None else (
                f"{prefix or ''}{local_path}"
            )
            details = {
                "method": method.upper(),
                "path": local_path,
                "full_path": full_path,
                "function": qualified,
                "router": router,
                "router_prefix": prefix,
                "prefix_resolved": full_path is not None,
            }
            route_name = f"{method.upper()} {full_path or local_path} -> {qualified}"
            self.routes.append(
                Located(
                    route_name,
                    "python-route",
                    node.lineno,
                    node.end_lineno or node.lineno,
                    details,
                )
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call):
            call_name = self._call_name(node.value.func)
            if call_name.endswith("APIRouter"):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.router_prefixes[target.id] = self._router_prefix(node.value)
        for target in node.targets:
            self._collect_assignment(target, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._collect_assignment(node.target, node)
        self.generic_visit(node)

    def _collect_assignment(self, target: ast.AST, node: ast.AST) -> None:
        if isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self._collect_assignment(item, node)
            return
        if not isinstance(target, ast.Name):
            return
        self.symbols.append(
            Located(
                self._qualified(target.id),
                "python-variable",
                node.lineno,
                node.end_lineno or node.lineno,
            )
        )


NODE_PARSER = r"""
const fs = require("fs");
const parserName = process.argv[1];
const parserEntry = process.argv[2];
const filename = process.argv[3];
const source = fs.readFileSync(filename, "utf8");
const parser = require(parserEntry);
let tree;
if (parserName === "@babel/parser") {
  tree = parser.parse(source, {
    sourceType: "unambiguous",
    plugins: ["jsx", "classProperties", "optionalChaining", "topLevelAwait"]
  });
} else if (parserName === "typescript") {
  throw new Error("typescript parser normalization is not implemented");
} else {
  const parse = parser.parse || parser.Parser?.parse;
  tree = parse.call(parser, source, {
    ecmaVersion: "latest", sourceType: "module", locations: true
  });
}
const out = [];
function loc(node) {
  const l = node.loc;
  return {start: l.start.line, end: l.end.line};
}
function add(name, kind, node, extra={}) {
  if (!name || !node.loc) return;
  out.push({name, kind, ...loc(node), details: extra});
}
function walk(node, scope=[], exported=false) {
  if (!node || typeof node !== "object") return;
  if (node.type === "ExportNamedDeclaration" || node.type === "ExportDefaultDeclaration") {
    if (node.declaration) walk(node.declaration, scope, true);
    return;
  }
  if (node.type === "FunctionDeclaration") {
    const name = node.id?.name;
    add([...scope, name].filter(Boolean).join("."), exported ? "javascript-export" : "javascript-function", node);
    scope = [...scope, name].filter(Boolean);
  } else if (node.type === "ClassDeclaration") {
    const name = node.id?.name;
    add([...scope, name].filter(Boolean).join("."), exported ? "javascript-export" : "javascript-class", node);
    scope = [...scope, name].filter(Boolean);
  } else if (node.type === "MethodDefinition" || node.type === "ClassMethod") {
    const name = node.key?.name || node.key?.value;
    add([...scope, name].filter(Boolean).join("."), "javascript-function", node);
    scope = [...scope, name].filter(Boolean);
  } else if (node.type === "VariableDeclarator" && node.id?.type === "Identifier") {
    const initType = node.init?.type || "";
    const isFunction = initType === "ArrowFunctionExpression" || initType === "FunctionExpression";
    if (isFunction || exported) {
      add([...scope, node.id.name].join("."), exported ? "javascript-export" : "javascript-function", node);
    }
  } else if (node.type === "CallExpression" && node.callee?.type === "MemberExpression"
      && node.callee.property?.name === "addEventListener"
      && ["Literal", "StringLiteral"].includes(node.arguments?.[0]?.type)) {
    add("event:" + node.arguments[0].value, "javascript-event", node, {event: node.arguments[0].value});
  }
  for (const [key, value] of Object.entries(node)) {
    if (key === "loc" || key === "start" || key === "end") continue;
    if (Array.isArray(value)) value.forEach(child => walk(child, scope, exported));
    else if (value && typeof value === "object") walk(value, scope, exported);
  }
}
walk(tree.program || tree);
process.stdout.write(JSON.stringify(out));
"""


class JavascriptParser:
    CANDIDATES = ("acorn", "espree", "@babel/parser", "typescript")

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.node = self._node_binary()
        self.parser_name, self.parser_entry, self.reason = self._find_parser()

    @staticmethod
    def _node_binary() -> str | None:
        from shutil import which

        return which("node")

    def _package_roots(self) -> list[tuple[Path, set[str]]]:
        roots: list[tuple[Path, set[str]]] = []
        for package in self.repo_root.rglob("package.json"):
            if "node_modules" in package.parts:
                continue
            try:
                data = json.loads(package.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            declared: set[str] = set()
            for key in ("dependencies", "devDependencies", "peerDependencies"):
                values = data.get(key)
                if isinstance(values, dict):
                    declared.update(values)
            roots.append((package.parent, declared))
        return roots

    def _find_parser(self) -> tuple[str | None, str | None, str]:
        if not self.node:
            return None, None, "Node.js is unavailable"
        package_roots = self._package_roots()
        for name in self.CANDIDATES:
            for package_root, declared in package_roots:
                local = package_root / "node_modules" / name
                if name not in declared and not local.exists():
                    continue
                probe = subprocess.run(
                    [
                        self.node,
                        "-e",
                        (
                            "const p=require.resolve(process.argv[1],"
                            "{paths:[process.argv[2]]});process.stdout.write(p)"
                        ),
                        name,
                        str(package_root),
                    ],
                    cwd=package_root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if probe.returncode:
                    continue
                resolved = Path(probe.stdout).resolve()
                try:
                    resolved.relative_to(self.repo_root)
                except ValueError:
                    continue
                if name == "typescript":
                    return None, None, (
                        "TypeScript is repository-local but its AST "
                        "normalization is not implemented"
                    )
                return name, str(resolved), f"repository-local parser: {name}"
        return None, None, (
            "no repository-local Acorn, Espree, Babel parser, or supported "
            "TypeScript parser is available"
        )

    @property
    def supported(self) -> bool:
        return bool(self.node and self.parser_name)

    def parse(self, path: Path) -> list[Located]:
        if not self.supported:
            raise RuntimeError(self.reason)
        process = subprocess.run(
            [
                self.node or "node",
                "-e",
                NODE_PARSER,
                self.parser_name or "",
                self.parser_entry or "",
                str(path),
            ],
            cwd=self.repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode:
            raise RuntimeError(process.stderr.strip() or "JavaScript parser failed")
        return [Located(**item) for item in json.loads(process.stdout)]


def choose_symbol(
    symbols: Iterable[Located], locator: str
) -> tuple[Located | None, list[Located]]:
    candidates = list(symbols)
    exact = [item for item in candidates if item.name == locator]
    if not exact and "." not in locator:
        exact = [item for item in candidates if item.name.split(".")[-1] == locator]
    return (exact[0] if len(exact) == 1 else None), exact


def apply_range_result(
    validation: Validation, located: Located, cited: tuple[int, int] | None
) -> Validation:
    validation.resolved = located
    validation.generated_line_range = located.line_range
    validation.suggested_locator = located.name
    validation.suggested_kind = located.kind
    if cited is None:
        if validation.current_evidence.get("line_range") not in (None, ""):
            validation.result = "range-mismatch"
            validation.problem = "line_range is malformed"
        else:
            validation.result = "valid"
        return validation
    start, end = cited
    if start <= located.start <= end:
        # Evidence ranges are excerpts. They must contain the declaration that
        # gives the locator its identity, but need not contain the whole body.
        validation.result = "valid"
    else:
        validation.result = "locator-outside-range"
        validation.problem = (
            f"locator declaration at L{located.start} is outside cited "
            f"L{start}-L{end}; parser-derived span is {located.line_range}"
        )
    return validation


def suggest_nearby(
    symbols: list[Located], locator: str, cited: tuple[int, int] | None
) -> tuple[Located | None, str]:
    if cited:
        overlapping = [
            item
            for item in symbols
            if cited[0] <= item.start <= cited[1]
            or item.start <= cited[0] <= item.end
        ]
        if len(overlapping) == 1:
            return overlapping[0], "high"
        leaf_matches = [
            item
            for item in overlapping
            if item.name.split(".")[-1] == locator.split(".")[-1]
        ]
        if len(leaf_matches) == 1:
            return leaf_matches[0], "high"
    names = [item.name for item in symbols]
    close = difflib.get_close_matches(locator, names, n=1, cutoff=0.72)
    if close:
        return next(item for item in symbols if item.name == close[0]), "medium"
    return None, "low"


def validate_python(
    validation: Validation, target: Path, cited: tuple[int, int] | None
) -> Validation:
    try:
        index = PythonIndex.from_path(target)
    except (OSError, UnicodeError, SyntaxError) as exc:
        validation.result = "unsupported"
        validation.problem = f"Python AST parsing failed: {exc}"
        validation.manual_review_reason = validation.problem
        return validation

    locator = validation.locator or ""
    if validation.inferred_kind == "python-module":
        if locator:
            validation.result = "invalid-locator"
            validation.problem = "python-module evidence must not name a symbol"
        else:
            validation.result = "file-level-valid"
            validation.suggested_kind = "python-module"
        return validation

    if validation.inferred_kind == "python-route":
        return validate_route(validation, index.routes, cited)

    located, exact = choose_symbol(index.symbols, locator)
    if len(exact) > 1:
        validation.result = "ambiguous"
        validation.problem = f"locator matches {len(exact)} declarations"
        validation.manual_review_reason = validation.problem
        validation.confidence = "low"
        return validation
    if not located:
        validation.result = "invalid-locator"
        validation.problem = f"Python locator {locator!r} does not exist"
        suggestion, confidence = suggest_nearby(index.symbols, locator, cited)
        validation.confidence = confidence
        if suggestion:
            validation.suggested_kind = suggestion.kind
            validation.suggested_locator = suggestion.name
            validation.generated_line_range = suggestion.line_range
        return validation
    return apply_range_result(validation, located, cited)


def validate_route(
    validation: Validation, routes: list[Located], cited: tuple[int, int] | None
) -> Validation:
    locator = validation.locator or ""
    legacy = LEGACY_ROUTE_RE.fullmatch(locator)
    canonical = CANONICAL_ROUTE_RE.fullmatch(locator)
    if not legacy and not canonical:
        validation.result = "invalid-locator"
        validation.problem = (
            "route locator must be '@router.method(\"/path\")' or "
            "'METHOD /path -> qualified.function'"
        )
        return validation
    expected_method = (legacy or canonical).group("method").upper()
    expected_path = (legacy or canonical).group("path")
    expected_function = canonical.group("function") if canonical else None
    method_matches = [
        route
        for route in routes
        if route.details and route.details["method"] == expected_method
    ]
    path_matches = [
        route
        for route in method_matches
        if route.details
        and expected_path in {route.details["path"], route.details["full_path"]}
    ]
    if not method_matches:
        validation.result = "invalid-locator"
        validation.problem = f"HTTP method {expected_method} is not declared in this file"
        return validation
    if not path_matches:
        validation.result = "invalid-locator"
        validation.problem = (
            f"route path {expected_path!r} is not declared for {expected_method}"
        )
        return validation
    if expected_function:
        function_matches = [
            route
            for route in path_matches
            if route.details and route.details["function"] == expected_function
        ]
        if not function_matches:
            validation.result = "invalid-locator"
            validation.problem = (
                f"route exists but containing function is not {expected_function!r}"
            )
            return validation
        path_matches = function_matches
    if len(path_matches) > 1:
        validation.result = "ambiguous"
        validation.problem = f"route locator matches {len(path_matches)} functions"
        validation.manual_review_reason = validation.problem
        validation.confidence = "low"
        return validation
    route = path_matches[0]
    details = route.details or {}
    if details.get("full_path") is None and expected_path != details.get("path"):
        validation.result = "ambiguous"
        validation.problem = "final router prefix cannot be resolved statically"
        validation.manual_review_reason = validation.problem
        validation.resolved = route
        validation.generated_line_range = route.line_range
        validation.suggested_locator = route.name
        validation.suggested_kind = "python-route"
        validation.confidence = "medium"
        return validation
    return apply_range_result(validation, route, cited)


def validate_javascript(
    validation: Validation,
    target: Path,
    cited: tuple[int, int] | None,
    parser: JavascriptParser,
) -> Validation:
    if not parser.supported:
        validation.result = "unsupported"
        validation.problem = parser.reason
        validation.manual_review_reason = parser.reason
        validation.confidence = "low"
        return validation
    try:
        symbols = parser.parse(target)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        validation.result = "unsupported"
        validation.problem = f"JavaScript parser failed: {exc}"
        validation.manual_review_reason = validation.problem
        validation.confidence = "low"
        return validation
    locator = validation.locator or ""
    located, exact = choose_symbol(symbols, locator)
    if len(exact) > 1:
        validation.result = "ambiguous"
        validation.problem = f"locator matches {len(exact)} JavaScript declarations"
        validation.manual_review_reason = validation.problem
        validation.confidence = "low"
        return validation
    if not located:
        validation.result = "invalid-locator"
        validation.problem = f"JavaScript locator {locator!r} does not exist"
        suggestion, confidence = suggest_nearby(symbols, locator, cited)
        validation.confidence = confidence
        if suggestion:
            validation.suggested_kind = suggestion.kind
            validation.suggested_locator = suggestion.name
            validation.generated_line_range = suggestion.line_range
        return validation
    return apply_range_result(validation, located, cited)


def shell_functions(path: Path) -> list[Located]:
    lines = path.read_text(encoding="utf-8").splitlines()
    functions: list[Located] = []
    for index, line in enumerate(lines):
        match = SHELL_FUNCTION_RE.match(line)
        if not match:
            continue
        depth = 0
        end = index + 1
        for offset in range(index, len(lines)):
            code = lines[offset].split("#", 1)[0]
            depth += code.count("{") - code.count("}")
            end = offset + 1
            if depth <= 0:
                break
        functions.append(
            Located(match.group("name"), "shell-function", index + 1, end)
        )
    return functions


def validate_shell(
    validation: Validation, target: Path, cited: tuple[int, int] | None
) -> Validation:
    try:
        check = subprocess.run(
            ["bash", "-n", str(target)], text=True, capture_output=True, check=False
        )
    except OSError as exc:
        validation.result = "unsupported"
        validation.problem = f"bash unavailable: {exc}"
        return validation
    if check.returncode:
        validation.result = "unsupported"
        validation.problem = f"shell syntax check failed: {check.stderr.strip()}"
        return validation
    functions = shell_functions(target)
    located, exact = choose_symbol(functions, validation.locator or "")
    if len(exact) > 1:
        validation.result = "ambiguous"
        validation.problem = "shell function locator is duplicated"
        validation.manual_review_reason = validation.problem
        return validation
    if not located:
        validation.result = "invalid-locator"
        validation.problem = f"shell function {validation.locator!r} does not exist"
        return validation
    return apply_range_result(validation, located, cited)


def validate_documentation(
    validation: Validation, target: Path, cited: tuple[int, int] | None
) -> Validation:
    locator = validation.locator or ""
    if not locator:
        validation.result = "invalid-locator"
        validation.problem = "documentation-section requires a heading locator"
        return validation
    lines = target.read_text(encoding="utf-8").splitlines()
    headings: list[Located] = []
    for number, line in enumerate(lines, 1):
        match = MARKDOWN_HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group("marks"))
        end = len(lines)
        for later, later_line in enumerate(lines[number:], number + 1):
            later_match = MARKDOWN_HEADING_RE.match(later_line)
            if later_match and len(later_match.group("marks")) <= level:
                end = later - 1
                break
        headings.append(
            Located(
                match.group("title").strip(),
                "documentation-section",
                number,
                end,
            )
        )
    located, exact = choose_symbol(headings, locator)
    if len(exact) > 1:
        validation.result = "ambiguous"
        validation.problem = "documentation heading is duplicated"
        validation.manual_review_reason = validation.problem
        return validation
    if not located:
        validation.result = "invalid-locator"
        validation.problem = f"documentation heading {locator!r} does not exist"
        return validation
    return apply_range_result(validation, located, cited)


def validate_evidence(
    repo_root: Path,
    feature_id: str,
    index: int,
    evidence: dict[str, Any],
    javascript_parser: JavascriptParser,
) -> Validation:
    target = safe_target(repo_root, evidence.get("path"))
    kind = infer_kind(evidence, target)
    locator = legacy_locator(evidence)
    validation = Validation(
        feature_id=feature_id,
        evidence_index=index,
        current_evidence=evidence,
        inferred_kind=kind,
        locator=locator,
        result="ambiguous",
    )
    if target is None or not target.is_file():
        validation.result = "invalid-path"
        validation.problem = f"evidence path is unsafe or missing: {evidence.get('path')!r}"
        validation.confidence = "high"
        return validation

    cited = parse_range(evidence.get("line_range"))
    explicit_range = evidence.get("line_range")
    if explicit_range not in (None, "") and cited is None:
        validation.result = "range-mismatch"
        validation.problem = f"malformed line_range: {explicit_range!r}"
        return validation
    if cited is not None:
        line_count = len(
            target.read_text(encoding="utf-8", errors="replace").splitlines()
        )
        if cited[0] > cited[1] or cited[1] > max(line_count, 1):
            validation.result = "range-mismatch"
            validation.problem = (
                f"line_range L{cited[0]}-L{cited[1]} is outside the "
                f"{line_count}-line file"
            )
            return validation

    if kind == "file":
        if locator:
            validation.result = "invalid-locator"
            validation.problem = "file evidence must not include a locator/symbol"
            validation.suggested_kind = "file"
            validation.confidence = "high"
            return validation
        validation.result = "file-level-valid"
        validation.suggested_kind = "file"
        line_count = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
        validation.generated_line_range = f"L1-L{max(line_count, 1)}"
        return validation

    if not locator and kind not in {"python-module", "file"}:
        validation.result = "invalid-locator"
        validation.problem = f"{kind} evidence requires a locator"
        return validation

    if kind in PYTHON_KINDS:
        return validate_python(validation, target, cited)
    if kind in JAVASCRIPT_KINDS:
        return validate_javascript(validation, target, cited, javascript_parser)
    if kind == "shell-function":
        return validate_shell(validation, target, cited)
    if kind == "documentation-section":
        return validate_documentation(validation, target, cited)
    if kind == "configuration-key":
        validation.result = "ambiguous"
        validation.problem = "configuration-key requires a format-aware parser"
        validation.manual_review_reason = (
            "This validator does not guess configuration keys from text."
        )
        validation.suggested_kind = (
            "file" if evidence.get("kind") is None else "manual-review"
        )
        validation.confidence = "low"
        return validation

    validation.result = "ambiguous"
    validation.problem = f"no automatic resolver for inferred kind {kind!r}"
    validation.manual_review_reason = (
        "Use explicit file evidence if the whole file is authoritative, "
        "or manual-review with a precise reason."
    )
    if evidence.get("kind") is None:
        validation.suggested_kind = "file"
        validation.suggested_locator = None
        line_count = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
        validation.generated_line_range = f"L1-L{max(line_count, 1)}"
        validation.confidence = "medium"
    return validation


def proposed_schema() -> dict[str, Any]:
    return {
        "required": ["path", "kind", "explanation"],
        "optional": ["locator", "line_range"],
        "properties": {
            "path": "repository-relative file path",
            "kind": sorted(
                PYTHON_KINDS
                | JAVASCRIPT_KINDS
                | {
                    "shell-function",
                    "configuration-key",
                    "file",
                    "documentation-section",
                    "manual-review",
                }
            ),
            "locator": (
                "parser-resolvable identity; omit for file evidence. "
                "Routes use 'METHOD /path -> qualified.function'."
            ),
            "line_range": (
                "optional generated display metadata in Lx-Ly form; "
                "never the primary identity"
            ),
            "explanation": "why this evidence supports the feature claim",
        },
        "examples": [
            {
                "path": "src/chat_handler.py",
                "kind": "python-method",
                "locator": "ChatHandler.preprocess_message",
                "explanation": "Preprocesses attachments and URLs for chat requests.",
            },
            {
                "path": "Dockerfile",
                "kind": "file",
                "explanation": "Defines the container build.",
            },
        ],
    }


def assess_e2(
    features: list[dict[str, Any]], validations: list[Validation]
) -> list[dict[str, Any]]:
    """Record the audit's claim-relevance review for the ten frozen E2 records."""
    by_key = {
        (item.feature_id, item.current_evidence.get("path"), item.locator): item
        for item in validations
    }
    decisions = {
        "CHAT-001": (
            "yes",
            "Both cited tests exercise documented chat-stream behavior: emitted "
            "stream metrics and non-destructive resend behavior.",
            "retain",
        ),
        "MODEL-006": (
            "yes",
            "The Node-backed test exercises the Copilot device-flow start/poll "
            "contract and complete verification URI.",
            "retain",
        ),
        "MODEL-007": (
            "yes",
            "The Node-backed test exercises the ChatGPT subscription device-flow "
            "contract and verification URI.",
            "retain",
        ),
        "RESEARCH-003": (
            "partial",
            "The test covers result ranking only, not SearXNG connectivity or "
            "multi-provider dispatch in the feature claim.",
            "demote",
        ),
        "DOCUMENT-002": (
            "no",
            "The test covers removal of a PDF content marker, not PDF form "
            "processing or high-fidelity rendering.",
            "demote",
        ),
        "EMAIL-001": (
            "partial",
            "The test covers health probing of account connections, not account "
            "setup, SMTP behavior, or inbox polling.",
            "demote",
        ),
        "SECURITY-002": (
            "yes",
            "Relevant vault password-handling tests exist, but the cited test "
            "function name is fabricated.",
            "demote",
        ),
        "SECURITY-004": (
            "yes",
            "Relevant prompt-injection tests exist, but both cited locator names "
            "are fabricated umbrella names.",
            "demote",
        ),
        "SECURITY-005": (
            "yes",
            "Relevant URL and path confinement tests exist, but all three cited "
            "locator names are fabricated umbrella names.",
            "demote",
        ),
        "PLATFORM-009": (
            "manual-review",
            "The shell diagnostic is executable evidence, but no automated test "
            "function or test-suite evidence is cited and the script uses a "
            "file-like fabricated symbol.",
            "demote",
        ),
    }
    assessments: list[dict[str, Any]] = []
    for feature in features:
        if feature.get("evidence_maturity") != "E2":
            continue
        test_evidence = [
            evidence
            for evidence in feature.get("evidence", [])
            if str(evidence.get("path", "")).startswith("tests/")
        ]
        cited: list[dict[str, Any]] = []
        for evidence in test_evidence:
            item = by_key.get(
                (feature["id"], evidence.get("path"), legacy_locator(evidence))
            )
            cited.append(
                {
                    "path": evidence.get("path"),
                    "locator": legacy_locator(evidence),
                    "exists": bool(
                        item
                        and item.result
                        not in {"invalid-path", "invalid-locator", "unsupported"}
                    ),
                    "validation_result": item.result if item else "not-validated",
                }
            )
        relevance, reason, decision = decisions[feature["id"]]
        assessments.append(
            {
                "feature_id": feature["id"],
                "feature_name": feature["name"],
                "cited_test_evidence": cited,
                "test_function_exists": (
                    all(item["exists"] for item in cited) if cited else False
                ),
                "direct_support": relevance,
                "support_reason": reason,
                "suggested_decision": decision,
            }
        )
    return assessments


def build_report(
    repo_root: Path,
    catalog_path: Path,
    features: list[dict[str, Any]],
    validations: list[Validation],
    javascript_parser: JavascriptParser,
) -> dict[str, Any]:
    extensions = Counter()
    kinds = Counter()
    for item in validations:
        extensions[extension_for(str(item.current_evidence.get("path", "")))] += 1
        kinds[item.inferred_kind] += 1
    results = Counter(item.result for item in validations)
    affected = sorted(
        {
            item.feature_id
            for item in validations
            if item.result not in {"valid", "file-level-valid"}
        }
    )
    invalid_results = {
        "invalid-path",
        "invalid-locator",
        "locator-outside-range",
        "range-mismatch",
    }
    invalid_features = sorted(
        {
            item.feature_id
            for item in validations
            if item.result in invalid_results
        }
    )
    ambiguous = [
        item.to_dict()
        for item in validations
        if item.result in {"ambiguous", "unsupported"}
    ]
    return {
        "audit": {
            "repo_root": str(repo_root),
            "catalog": str(catalog_path),
            "feature_count": len(features),
            "evidence_count": len(validations),
            "javascript_parser": {
                "supported": javascript_parser.supported,
                "parser": javascript_parser.parser_name,
                "reason": javascript_parser.reason,
            },
        },
        "inventory": {
            "total_evidence_items": len(validations),
            "by_extension": dict(sorted(extensions.items())),
            "by_inferred_evidence_type": dict(sorted(kinds.items())),
            "features_with_invalid_or_unresolved_entries": affected,
            "features_with_invalid_entries": invalid_features,
            "invalid_feature_count": len(invalid_features),
            "affected_feature_count": len(affected),
            "ambiguous_or_unsupported_entries": ambiguous,
        },
        "result_counts": {name: results.get(name, 0) for name in sorted(RESULTS)},
        "summary_counts": {
            "valid": results["valid"] + results["file-level-valid"],
            "invalid": sum(
                results[name]
                for name in (
                    "invalid-path",
                    "invalid-locator",
                    "locator-outside-range",
                    "range-mismatch",
                )
            ),
            "ambiguous": results["ambiguous"],
            "unsupported": results["unsupported"],
        },
        "evidence_model": proposed_schema(),
        "e2_assessment": assess_e2(features, validations),
        "entries": [item.to_dict() for item in validations],
    }


def build_repair_queue(validations: list[Validation]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in validations:
        if item.result in {"valid", "file-level-valid"}:
            continue
        grouped[item.feature_id].append(
            {
                "evidence_index": item.evidence_index,
                "current_evidence": item.current_evidence,
                "detected_problem": item.problem or item.result,
                "result": item.result,
                "suggested_kind": item.suggested_kind,
                "suggested_locator": item.suggested_locator,
                "generated_line_range": item.generated_line_range,
                "confidence": item.confidence,
                "manual_review_reason": item.manual_review_reason,
            }
        )
    return {
        "feature_count": len(grouped),
        "defect_count": sum(len(items) for items in grouped.values()),
        "features": [
            {"feature_id": feature_id, "defects": grouped[feature_id]}
            for feature_id in sorted(grouped)
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    inventory = report["inventory"]
    summary = report["summary_counts"]
    lines = [
        "# Discovery evidence validation report",
        "",
        "This report is machine-generated. The catalog was not edited.",
        "",
        "## Summary",
        "",
        f"- Features: {report['audit']['feature_count']}",
        f"- Evidence items: {report['audit']['evidence_count']}",
        f"- Valid (including file-level): {summary['valid']}",
        f"- Invalid: {summary['invalid']}",
        f"- Ambiguous: {summary['ambiguous']}",
        f"- Unsupported: {summary['unsupported']}",
        f"- Affected features: {inventory['affected_feature_count']}",
        "",
        "## Evidence by extension",
        "",
        "| Extension | Items |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{extension}` | {count} |"
        for extension, count in inventory["by_extension"].items()
    )
    lines.extend(
        [
            "",
            "## Evidence by inferred kind",
            "",
            "| Kind | Items |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{kind}` | {count} |"
        for kind, count in inventory["by_inferred_evidence_type"].items()
    )
    lines.extend(
        [
            "",
            "## Result categories",
            "",
            "| Result | Items |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{result}` | {count} |"
        for result, count in report["result_counts"].items()
    )
    lines.extend(
        [
            "",
            "## JavaScript parser",
            "",
            report["audit"]["javascript_parser"]["reason"] + ".",
            "",
            "## Affected features",
            "",
            ", ".join(
                f"`{feature_id}`"
                for feature_id in inventory[
                    "features_with_invalid_or_unresolved_entries"
                ]
            )
            or "None.",
            "",
            "## E2 relevance review",
            "",
            "| Feature | Cited test evidence | Exists | Direct support | Decision |",
            "|---|---|---:|---|---|",
        ]
    )
    for item in report["e2_assessment"]:
        citations = "<br>".join(
            f"`{test['path']}:{test['locator']}`"
            for test in item["cited_test_evidence"]
        ) or "None"
        lines.append(
            f"| `{item['feature_id']}` | {citations} | "
            f"{'yes' if item['test_function_exists'] else 'no'} | "
            f"{item['direct_support']}: {item['support_reason']} | "
            f"**{item['suggested_decision']}** |"
        )
    lines.extend(
        [
            "",
            "### Numerical inconsistency resolved",
            "",
            "The six problematic cited E2 test records are the six nonexistent "
            "locator names in SECURITY-002 (one), SECURITY-004 (two), and "
            "SECURITY-005 (three). Seven feature demotions were suggested because "
            "PLATFORM-009 is an additional feature-level maturity problem: it "
            "cites no automated test function. The other three demotions are "
            "claim-relevance findings for existing tests, so the figures measure "
            "different things and should not be compared as the same denominator.",
            "",
            "## Proposed evidence schema",
            "",
            "Required: `path`, `kind`, and `explanation`. `locator` is required "
            "for symbol/route/section evidence and omitted for `file`. "
            "`line_range` is optional generated metadata.",
            "",
            "```json",
            json.dumps(report["evidence_model"]["examples"], indent=2),
            "```",
            "",
            "## Defects",
            "",
            "| Feature | Path | Locator | Result | Generated range | Problem |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in report["entries"]:
        if item["result"] in {"valid", "file-level-valid"}:
            continue
        evidence = item["current_evidence"]
        problem = (item["problem"] or "").replace("|", "\\|")
        lines.append(
            f"| `{item['feature_id']}` | `{evidence.get('path', '')}` | "
            f"`{item.get('locator') or ''}` | `{item['result']}` | "
            f"`{item.get('generated_line_range') or ''}` | {problem} |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(output_dir: Path, report: dict[str, Any], queue: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evidence-validation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "evidence-validation-report.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    (output_dir / "evidence-repair-queue.json").write_text(
        json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    catalog_path = args.catalog.resolve()
    features = load_catalog(catalog_path)
    javascript_parser = JavascriptParser(repo_root)
    validations = [
        validate_evidence(
            repo_root,
            str(feature.get("id", f"<feature:{feature_index}>")),
            evidence_index,
            evidence,
            javascript_parser,
        )
        for feature_index, feature in enumerate(features)
        for evidence_index, evidence in enumerate(feature.get("evidence", []))
        if isinstance(evidence, dict)
    ]
    report = build_report(
        repo_root, catalog_path, features, validations, javascript_parser
    )
    queue = build_repair_queue(validations)
    write_outputs(args.output_dir.resolve(), report, queue)
    print(json.dumps(report["summary_counts"], sort_keys=True))
    return 1 if queue["defect_count"] else 0


if __name__ == "__main__":
    sys.exit(run())
