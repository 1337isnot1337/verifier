-- Local cache preparation, 2026-10-09. Uses pinned Lake's hash implementation.
-- This changes only hash sidecars, never source or compiled proof objects.
import Lake

def main (args : List String) : IO Unit := do
  let [manifest] := args | throw (IO.userError "expected cache hash input list")
  let lines := (← IO.FS.readFile manifest).splitOn "\n"
  for line in lines do
    if line.isEmpty then continue
    let [kind, path] := line.splitOn "\t"
      | throw (IO.userError "invalid cache hash input")
    Lake.cacheFileHash path (text := kind == "text")
