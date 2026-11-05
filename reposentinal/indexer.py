import ast
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from reposentinal.models import FileContext


class SymbolKind(str, Enum):
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    CLASS = "CLASS"
    IMPORT = "IMPORT"


@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    file_path: str
    line_start: int
    line_end: int
    parent: Optional[str] = None  # Class name if this is a method
    parameters: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass
class ImportStatement:
    source_file: str
    module: str
    names: List[str]
    is_from: bool
    line_no: int
    level: int = 0  # Relative import level (e.g. . = 1, .. = 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DependencyGraph:
    nodes: Set[str] = field(default_factory=set)
    # file -> set of files it depends on (imports)
    edges: Dict[str, Set[str]] = field(default_factory=dict)
    # file -> set of files that depend on it
    reverse_edges: Dict[str, Set[str]] = field(default_factory=dict)
    # file -> set of external/unresolved modules (e.g. os, sys, requests)
    external_dependencies: Dict[str, Set[str]] = field(default_factory=dict)

    def add_node(self, node: str):
        self.nodes.add(node)
        if node not in self.edges:
            self.edges[node] = set()
        if node not in self.reverse_edges:
            self.reverse_edges[node] = set()
        if node not in self.external_dependencies:
            self.external_dependencies[node] = set()

    def add_edge(self, from_node: str, to_node: str):
        self.add_node(from_node)
        self.add_node(to_node)
        self.edges[from_node].add(to_node)
        self.reverse_edges[to_node].add(from_node)

    def add_external(self, from_node: str, module: str):
        self.add_node(from_node)
        self.external_dependencies[from_node].add(module)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": sorted(list(self.nodes)),
            "edges": {k: sorted(list(v)) for k, v in self.edges.items()},
            "reverse_edges": {k: sorted(list(v)) for k, v in self.reverse_edges.items()},
            "external_dependencies": {k: sorted(list(v)) for k, v in self.external_dependencies.items()},
        }


@dataclass
class RepositoryIndex:
    symbols: List[Symbol] = field(default_factory=list)
    imports: List[ImportStatement] = field(default_factory=list)
    graph: DependencyGraph = field(default_factory=DependencyGraph)
    symbols_by_name: Dict[str, List[Symbol]] = field(default_factory=dict)
    symbols_by_file: Dict[str, List[Symbol]] = field(default_factory=dict)
    calls_by_file: Dict[str, Set[str]] = field(default_factory=dict)

    def find_symbols(self, name: str) -> List[Symbol]:
        """Look up symbols by exact name across the repository."""
        return self.symbols_by_name.get(name, [])

    def get_file_symbols(self, file_path: str) -> List[Symbol]:
        """Get all symbols defined within a specific file."""
        return self.symbols_by_file.get(file_path, [])

    def get_dependencies(self, file_path: str) -> Set[str]:
        """Get repository files imported by this file."""
        return self.graph.edges.get(file_path, set())

    def get_dependents(self, file_path: str) -> Set[str]:
        """Get repository files that import this file."""
        return self.graph.reverse_edges.get(file_path, set())

    def get_external_modules(self, file_path: str) -> Set[str]:
        """Get external/stdlib modules imported by this file."""
        return self.graph.external_dependencies.get(file_path, set())

    def get_callers_of_symbol(self, symbol_name: str) -> List[str]:
        """Find files that call a function or instantiate a class named symbol_name."""
        callers = []
        for file_path, calls in self.calls_by_file.items():
            if symbol_name in calls:
                callers.append(file_path)
        return sorted(callers)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_symbols": len(self.symbols),
            "total_imports": len(self.imports),
            "classes_count": sum(1 for s in self.symbols if s.kind == SymbolKind.CLASS),
            "functions_count": sum(1 for s in self.symbols if s.kind == SymbolKind.FUNCTION),
            "methods_count": sum(1 for s in self.symbols if s.kind == SymbolKind.METHOD),
            "topology": self.graph.to_dict(),
            "symbols": [s.to_dict() for s in self.symbols],
        }


class PythonASTVisitor(ast.NodeVisitor):
    """
    AST visitor to extract functions, classes, methods, imports, and function calls from Python files.
    """

    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.symbols: List[Symbol] = []
        self.imports: List[ImportStatement] = []
        self.calls: Set[str] = set()
        self._class_stack: List[str] = []

    def _decorator_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._decorator_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._decorator_name(node.func)
        return ""

    def visit_ClassDef(self, node: ast.ClassDef):
        name = node.name
        doc = ast.get_docstring(node)
        decorators = [self._decorator_name(d) for d in node.decorator_list if self._decorator_name(d)]
        end_lineno = getattr(node, "end_lineno", node.lineno)

        self.symbols.append(
            Symbol(
                name=name,
                kind=SymbolKind.CLASS,
                file_path=self.rel_path,
                line_start=node.lineno,
                line_end=end_lineno,
                parent=self._class_stack[-1] if self._class_stack else None,
                docstring=doc,
                decorators=decorators,
            )
        )

        self._class_stack.append(name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_func(node)

    def _process_func(self, node: ast.AST):
        name = node.name
        is_method = bool(self._class_stack)
        kind = SymbolKind.METHOD if is_method else SymbolKind.FUNCTION
        parent = self._class_stack[-1] if is_method else None
        doc = ast.get_docstring(node)
        decorators = [self._decorator_name(d) for d in node.decorator_list if self._decorator_name(d)]
        params = [arg.arg for arg in node.args.args]
        end_lineno = getattr(node, "end_lineno", node.lineno)

        self.symbols.append(
            Symbol(
                name=name,
                kind=kind,
                file_path=self.rel_path,
                line_start=node.lineno,
                line_end=end_lineno,
                parent=parent,
                parameters=params,
                docstring=doc,
                decorators=decorators,
            )
        )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(
                ImportStatement(
                    source_file=self.rel_path,
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    is_from=False,
                    line_no=node.lineno,
                    level=0,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        names = [alias.name for alias in node.names]
        self.imports.append(
            ImportStatement(
                source_file=self.rel_path,
                module=module,
                names=names,
                is_from=True,
                line_no=node.lineno,
                level=node.level or 0,
            )
        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            self.calls.add(func.id)
        elif isinstance(func, ast.Attribute):
            self.calls.add(func.attr)
        self.generic_visit(node)


def _resolve_module_to_file(
    source_file: str,
    module: str,
    level: int,
    available_files: Set[str],
) -> Optional[str]:
    """
    Resolve an imported module string to a concrete repository file path.
    Supports absolute (e.g. reposentinal.models) and relative (e.g. .models) imports.
    """
    source_path = Path(source_file)
    source_dir = source_path.parent

    # 1. Handle relative imports
    if level > 0:
        base_dir = source_dir
        for _ in range(level - 1):
            base_dir = base_dir.parent

        if module:
            target_rel = base_dir / module.replace(".", "/")
        else:
            target_rel = base_dir

        for candidate in [
            f"{target_rel}.py",
            f"{target_rel}/__init__.py",
        ]:
            normalized = candidate.replace("\\", "/").lstrip("./")
            if normalized in available_files:
                return normalized
        return None

    # 2. Handle absolute imports
    if not module:
        return None

    path_candidate = module.replace(".", "/")
    for candidate in [
        f"{path_candidate}.py",
        f"{path_candidate}/__init__.py",
    ]:
        normalized = candidate.replace("\\", "/").lstrip("./")
        if normalized in available_files:
            return normalized

    # 3. Check if module matches a file directly under root or relative to source directory
    local_candidate = (source_dir / path_candidate).as_posix()
    for candidate in [
        f"{local_candidate}.py",
        f"{local_candidate}/__init__.py",
    ]:
        normalized = candidate.replace("\\", "/").lstrip("./")
        if normalized in available_files:
            return normalized

    # 4. Check if stripping leading package components matches available files
    # E.g. if module is "reposentinal.models" and available_files has "models.py"
    parts = module.split(".")
    for i in range(1, len(parts)):
        subpath = "/".join(parts[i:])
        for candidate in [f"{subpath}.py", f"{subpath}/__init__.py"]:
            normalized = candidate.replace("\\", "/").lstrip("./")
            if normalized in available_files:
                return normalized

    # 5. Check if any file in available_files ends with the target candidate
    for candidate in [f"{path_candidate}.py", f"{path_candidate}/__init__.py"]:
        for av in available_files:
            if av == candidate or av.endswith(f"/{candidate}"):
                return av

    return None


def build_repository_index(files: List[FileContext]) -> RepositoryIndex:
    """
    Construct a complete repository symbol index and dependency topology
    from a collection of FileContexts.
    """
    index = RepositoryIndex()
    available_files: Set[str] = {f.rel_path.replace("\\", "/") for f in files}

    for f in files:
        index.graph.add_node(f.rel_path)

        if f.language == "python":
            try:
                tree = ast.parse(f.content, filename=f.rel_path)
                visitor = PythonASTVisitor(rel_path=f.rel_path)
                visitor.visit(tree)

                index.symbols.extend(visitor.symbols)
                index.imports.extend(visitor.imports)
                index.calls_by_file[f.rel_path] = visitor.calls

                for s in visitor.symbols:
                    index.symbols_by_name.setdefault(s.name, []).append(s)
                    index.symbols_by_file.setdefault(f.rel_path, []).append(s)

            except Exception:
                # Syntax error or unparseable Python file, continue gracefully
                continue

    # Build dependency graph edges by resolving import statements
    for imp in index.imports:
        resolved_file = _resolve_module_to_file(
            source_file=imp.source_file,
            module=imp.module,
            level=imp.level,
            available_files=available_files,
        )

        if resolved_file and resolved_file != imp.source_file:
            index.graph.add_edge(imp.source_file, resolved_file)
        else:
            # External or unresolved dependency
            external_name = imp.module.split(".")[0] if imp.module else "unknown"
            if external_name:
                index.graph.add_external(imp.source_file, external_name)

    return index
