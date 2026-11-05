from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from reposentinal.models import FileContext
from reposentinal.indexer import RepositoryIndex, Symbol, SymbolKind


@dataclass
class ImportedSymbolContext:
    module_file: str
    symbol_name: str
    kind: str
    parameters: List[str]
    docstring: Optional[str]
    line_start: int


@dataclass
class CallerContext:
    caller_file: str
    called_symbols: List[str]


@dataclass
class RepositoryContext:
    target_file: str
    defined_symbols: List[Symbol] = field(default_factory=list)
    imported_files: List[str] = field(default_factory=list)
    imported_symbols: List[ImportedSymbolContext] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    callers: List[CallerContext] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """
        Format the cross-file repository context into an LLM-friendly prompt block.
        Highlights interfaces, return conventions, parameter contracts, and caller relationships.
        """
        sections = [f"### 🌐 Repository Cross-File Context for `{self.target_file}`:"]

        # 1. Defined Symbols in this file
        if self.defined_symbols:
            sections.append("\n**Symbols Defined in this File:**")
            for sym in self.defined_symbols:
                params_str = f"({', '.join(sym.parameters)})" if sym.kind in (SymbolKind.FUNCTION, SymbolKind.METHOD) else ""
                parent_prefix = f"{sym.parent}." if sym.parent else ""
                doc_preview = f" - Doc: \"{sym.docstring.strip()[:80]}...\"" if sym.docstring else ""
                sections.append(f"- `{sym.kind.value}` `{parent_prefix}{sym.name}{params_str}` (Lines {sym.line_start}-{sym.line_end}){doc_preview}")

        # 2. Imported internal symbols & contracts
        if self.imported_symbols:
            sections.append("\n**Cross-File Dependencies (Imported Symbols & Contracts):**")
            # Group by file
            by_file: Dict[str, List[ImportedSymbolContext]] = {}
            for imp in self.imported_symbols:
                by_file.setdefault(imp.module_file, []).append(imp)

            for mod_file, syms in by_file.items():
                sections.append(f"- From module `{mod_file}`:")
                for s in syms:
                    params_str = f"({', '.join(s.parameters)})" if s.parameters else "()"
                    doc_snippet = f" | Doc: \"{s.docstring.strip()[:100]}\"" if s.docstring else ""
                    sections.append(f"  └── `{s.kind}` `{s.symbol_name}{params_str}`{doc_snippet}")
        elif self.imported_files:
            sections.append(f"\n**Imported Internal Modules:** {', '.join(self.imported_files)}")

        # 3. Callers / Inbound References
        if self.callers:
            sections.append("\n**Inbound Usages (Files that call into this file):**")
            for caller in self.callers:
                syms_str = ", ".join(caller.called_symbols) if caller.called_symbols else "module import"
                sections.append(f"- `{caller.caller_file}` calls: `{syms_str}`")

        # 4. External Libraries
        if self.external_dependencies:
            sections.append(f"\n**External Packages Used:** {', '.join(sorted(self.external_dependencies))}")

        return "\n".join(sections)


class RepositoryContextBuilder:
    """
    Builds structured RepositoryContext for any file in the repository index.
    """

    def __init__(self, index: RepositoryIndex):
        self.index = index

    def build_context(self, file_ctx: FileContext) -> RepositoryContext:
        rel_path = file_ctx.rel_path
        defined_symbols = self.index.get_file_symbols(rel_path)
        dependencies = sorted(list(self.index.get_dependencies(rel_path)))
        externals = sorted(list(self.index.get_external_modules(rel_path)))
        dependents = sorted(list(self.index.get_dependents(rel_path)))

        # Find imported symbols with their contracts/signatures from dependencies
        imported_symbols: List[ImportedSymbolContext] = []
        for dep_file in dependencies:
            dep_symbols = self.index.get_file_symbols(dep_file)
            for sym in dep_symbols:
                imported_symbols.append(
                    ImportedSymbolContext(
                        module_file=dep_file,
                        symbol_name=sym.name,
                        kind=sym.kind.value,
                        parameters=sym.parameters,
                        docstring=sym.docstring,
                        line_start=sym.line_start,
                    )
                )

        # Find inbound callers calling symbols in this file
        callers: List[CallerContext] = []
        defined_names = {s.name for s in defined_symbols}
        for dep_file in dependents:
            called = [name for name in defined_names if name in self.index.calls_by_file.get(dep_file, set())]
            callers.append(CallerContext(caller_file=dep_file, called_symbols=called))

        return RepositoryContext(
            target_file=rel_path,
            defined_symbols=defined_symbols,
            imported_files=dependencies,
            imported_symbols=imported_symbols,
            external_dependencies=externals,
            callers=callers,
        )
