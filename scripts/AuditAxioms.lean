-- Trusted axiom auditor: inspects compiled kernel constants without importing
-- submission syntax, macros, or command elaborators.
import Lean
import Lean.Util.CollectAxioms

def main (args : List String) : IO Unit := do
  let modStr :: declStrs := args
    | throw (IO.userError "usage: AuditAxioms <module> <decl>...")
  if declStrs.isEmpty then
    throw (IO.userError "expected at least one declaration name")
  Lean.initSearchPath (← Lean.findSysroot)
  let modName := modStr.toName
  let env ← Lean.importModules #[{ module := modName }] {} (loadExts := false)
  for declStr in declStrs do
    let declName := declStr.toName
    unless env.contains declName do
      throw (IO.userError s!"unknown declaration '{declStr}'")
    let (axiomsArr, _) ← Lean.Core.CoreM.toIO (Lean.collectAxioms declName)
      { fileName := "<audit>", fileMap := default }
      { env := env }
    let axioms := axiomsArr.toList.map toString |>.mergeSort (· < ·)
    if axioms.isEmpty then
      IO.println s!"'{declStr}' does not depend on any axioms"
    else
      IO.println s!"'{declStr}' depends on axioms: [{String.intercalate ", " axioms}]"
