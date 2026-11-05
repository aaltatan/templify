Output docs/demo/each.gif
Set Height 600
Source docs/demo/common.tape

Type "Get-Content welcome.md" Enter Sleep 1500ms
Type "templify render --each -t welcome.md -d employees.json -o out -n name --numbered"
Sleep 300ms
Enter
Sleep 3s
Type "Get-ChildItem out -Name" Enter Sleep 1500ms
Type "Get-Content 'out/1 - Rama.md'" Enter
Sleep 4s
