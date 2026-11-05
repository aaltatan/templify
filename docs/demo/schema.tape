Output docs/demo/schema.gif
Set Height 600
Source docs/demo/common.tape

Type "Get-Content letter.md" Enter Sleep 1500ms
Type "templify render --object -s person.schema.json -t letter.md -o out"
Sleep 300ms
Enter
Sleep 3s
Type "Ada" Sleep 300ms Enter Sleep 400ms
Type "Lovelace" Sleep 300ms Enter Sleep 400ms
Type "36" Sleep 300ms Enter
Sleep 2s
Type "Get-Content out/letter.md" Enter
Sleep 4s
