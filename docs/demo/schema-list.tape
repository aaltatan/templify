Output docs/demo/schema-list.gif
Set Height 820
Source docs/demo/common.tape

Type "Get-Content team.md" Enter Sleep 1500ms
Type "templify jsl --js person.schema.json -t team.md -o out"
Sleep 300ms
Enter
Sleep 3s
Type "Ada" Sleep 300ms Enter Sleep 300ms
Type "Lovelace" Sleep 300ms Enter Sleep 300ms
Type "36" Sleep 300ms Enter Sleep 600ms
Type "y" Sleep 800ms
Type "Alan" Sleep 300ms Enter Sleep 300ms
Type "Turing" Sleep 300ms Enter Sleep 300ms
Type "41" Sleep 300ms Enter Sleep 600ms
Type "n"
Sleep 2s
Type "Get-Content out/team.md" Enter
Sleep 4s
