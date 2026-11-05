# Hidden setup for the tapes: run templify from this checkout in a scratch folder with demo files.
$env:PYTHONIOENCODING = "utf-8"
$global:repo = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location (New-Item -ItemType Directory -Force "$env:TEMP/templify-demo")
Remove-Item -Recurse -ErrorAction Ignore out
function global:templify { uv run -q --project $repo templify @args }
function global:prompt { "> " }

@'
{
  "title": "Person",
  "type": "object",
  "properties": {
    "first": { "title": "First name", "type": "string" },
    "last": { "title": "Last name", "type": "string" },
    "age": { "type": "integer" },
    "full_name": {
      "title": "Full name",
      "type": "string",
      "x-compute": { "fn": "join", "from": ["first", "last"] }
    }
  },
  "required": ["first", "last", "full_name"],
  "additionalProperties": false
}
'@ | Set-Content person.schema.json

"Dear {{ object.full_name }}, happy {{ object.age }}th birthday!" | Set-Content letter.md

@'
# Team
{% for p in objects %}
- {{ p.full_name }} ({{ p.age }})
{% endfor %}
'@ | Set-Content team.md
