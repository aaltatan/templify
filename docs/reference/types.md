# Type filters

Every [jinja-types](https://pypi.org/project/jinja-types/) member available in
templates. `templify types` prints the same list, and
`templify types -n <namespace> -k <kind>` narrows it. How to use them is in
[Type filters](../guide/type-filters.md).

| Kind | Used as |
|------|---------|
| filter | `{{ value \| str.zfill(5) }}` |
| test | `{% if value is str.isdigit %}` |
| attribute | `decimal.ROUND_HALF_UP` |
| global | `{{ today() }}` |

Namespaces: [`helpers`](#helpers), [`ar`](#ar), [`date`](#date), [`datetime`](#datetime), [`decimal`](#decimal), [`dict`](#dict), [`float`](#float), [`fraction`](#fraction), [`int`](#int), [`list`](#list), [`match`](#match), [`path`](#path), [`pattern`](#pattern), [`re`](#re), [`str`](#str), [`time`](#time), [`timedelta`](#timedelta), [`uuid`](#uuid).

## helpers

| Name | Kinds | Description |
|------|-------|-------------|
| `decimal` | global | The `decimal` namespace object. |
| `fmt` | filter | Return `format(value, spec)`; works for numbers, Decimal and dates. |
| `now` | global | Return the current datetime, local or in `tz` (a `tzinfo`). |
| `random` | global | The `random` object; `random.Random(seed)` gives a repeatable generator. |
| `re` | global | The `re` flags object, with `re.compile(pattern, flags=0)` for the `pattern` namespace. |
| `secrets` | global | The `secrets` object: cryptographically strong tokens and choices. |
| `to_bool` | filter | Convert strictly: true/yes/on/1 or false/no/off/0 (any case), bools, and ints 0 or 1. |
| `to_date` | filter | Parse an ISO date, or use `format` with `strptime`. A datetime gives its date. |
| `to_datetime` | filter | Parse an ISO datetime, or use `format` with `strptime`. A date becomes midnight. |
| `to_decimal` | filter | Convert to `Decimal`. Floats go through `repr()`, so `0.1` gives `Decimal('0.1')`. |
| `to_float` | filter | Convert to `float`. |
| `to_fraction` | filter | Convert to `Fraction` (`'3/4'`, `'0.75'`, numbers). |
| `to_int` | filter | Convert to `int`. `base` applies to strings; numbers are truncated like `int()`. |
| `to_path` | filter | Convert to a `PurePath` (never touches the disk). |
| `to_str` | filter | Return `str(value)`. |
| `to_time` | filter | Parse an ISO time, or use `format` with `strptime`. A datetime gives its time (with tz). |
| `to_timedelta` | filter | Convert seconds (or `str(timedelta)` text) to a timedelta, plus `days`/`hours`/`minutes`. |
| `to_uuid` | filter | Convert to `UUID`. |
| `today` | global | Return today's local date. |
| `uuid1` | global | Return a time-based UUID; without `node`, a random node id is used, never the MAC. |
| `uuid4` | global | Return a random UUID (different on every call). |
| `uuid5` | global | Return the name-based (SHA-1) UUID; same input, same UUID. `namespace` may be UUID text. |

## ar

| Name | Kinds | Description |
|------|-------|-------------|
| `ar.duration` | filter | A duration in words, largest unit first: «أسبوع ويومان». |
| `ar.equals` | filter, test | Return True if both strings match after normalizing them. Also a test. |
| `ar.format_date` | filter | Format with Arabic names: strftime directives, `%O` for the ordinal day. |
| `ar.format_money` | filter | Format an amount with the currency symbol. Money is never rounded. |
| `ar.format_number` | filter | Format a number with a digit set, thousands separator and decimal mark. |
| `ar.format_percent` | filter | Format a fraction as a percentage with the `٪` sign. |
| `ar.month_name` | filter | The month's Arabic name: «كانون الثاني», «يناير», … |
| `ar.normalize` | filter | Normalize Arabic text with a preset: `search`, `names` or `sort`. |
| `ar.ordinal` | filter | The ordinal of a number from 1 to 100: «الثالث». |
| `ar.ordinal_adverb` | filter | The list marker for a number from 1 to 100: «أولًا»، «ثانيًا». |
| `ar.parse_date` | filter | Strictly parse Arabic date text, in any digit set. `months=None` accepts every style. |
| `ar.parse_datetime` | filter | Strictly parse Arabic datetime text, in any digit set. |
| `ar.parse_number` | filter | Parse a number written in any digit set into an exact `Decimal`. |
| `ar.reshape_only` | filter | Join the letters but keep the logical order. Needs `jinja-types[shape]`. |
| `ar.shape` | filter | Join the letters and reorder for left-to-right drawing. Needs `jinja-types[shape]`. |
| `ar.since` | filter | How long ago (or how far ahead) the datetime is, in its largest whole unit. |
| `ar.sort` | filter | Sort in Arabic alphabetical order. `key` is an attribute name or a macro. |
| `ar.to_arabic_digits` | filter | Replace Latin and Persian digits with Arabic-Indic digits. |
| `ar.to_hijri` | filter | The same day in the Hijri (Umm al-Qura) calendar. Needs `jinja-types[hijri]`. |
| `ar.to_latin_digits` | filter | Replace Arabic-Indic and Persian digits with Latin digits. |
| `ar.to_persian_digits` | filter | Replace Latin and Arabic-Indic digits with Persian digits. |
| `ar.to_words` | filter | Write a number in Arabic words (تفقيط), optionally counting a noun or a currency. |
| `ar.weekday_name` | filter | The weekday's Arabic name: «الاثنين» … «الأحد». |

## date

| Name | Kinds | Description |
|------|-------|-------------|
| `date.ctime` | filter | Return a `ctime()` style string. |
| `date.day` | attribute | The day of the month. |
| `date.fromisocalendar` | filter | Return the date for an ISO year, week and weekday (classmethod; the year is piped in). |
| `date.fromisoformat` | filter | Parse an ISO date (classmethod; the string is piped in). |
| `date.fromordinal` | filter | Return the date for a proleptic Gregorian ordinal (classmethod; the ordinal is piped in). |
| `date.fromtimestamp` | filter | Return the local date for a POSIX timestamp (classmethod; the timestamp is piped in). |
| `date.isocalendar` | filter | Return `(year, week, weekday)` of the ISO calendar. |
| `date.isoformat` | filter | Return the date as `YYYY-MM-DD`. |
| `date.isoweekday` | filter | Return the day of the week, Monday is 1 and Sunday is 7. |
| `date.month` | attribute | The month, 1 to 12. |
| `date.replace` | filter | Return the date with the given fields replaced. |
| `date.strftime` | filter | Format the date with a `strftime` format string. |
| `date.timetuple` | filter | Return a `time.struct_time`. |
| `date.toordinal` | filter | Return the proleptic Gregorian ordinal, where 0001-01-01 is 1. |
| `date.weekday` | filter | Return the day of the week, Monday is 0 and Sunday is 6. |
| `date.year` | attribute | The year. |

## datetime

| Name | Kinds | Description |
|------|-------|-------------|
| `datetime.astimezone` | filter | Convert to the timezone `tz`: a `tzinfo`, an IANA name, or None for local time. |
| `datetime.combine` | filter | Join a date and a time (classmethod; the date is piped in). |
| `datetime.ctime` | filter | Return a `ctime()` style string. |
| `datetime.date` | filter | Return the date part. |
| `datetime.dst` | filter | Return the daylight saving offset, or None if unknown. |
| `datetime.fold` | attribute | 0 or 1: which of two repeated wall times this is. |
| `datetime.fromisoformat` | filter | Parse an ISO datetime (classmethod; the string is piped in). |
| `datetime.fromtimestamp` | filter | Return the datetime for a POSIX timestamp (classmethod; the timestamp is piped in). |
| `datetime.hour` | attribute | The hour, 0 to 23. |
| `datetime.isoformat` | filter | Return the datetime in ISO 8601 format. |
| `datetime.microsecond` | attribute | The microsecond. |
| `datetime.minute` | attribute | The minute. |
| `datetime.replace` | filter | Return the datetime with the given fields replaced. `tzinfo=none` makes it naive. |
| `datetime.second` | attribute | The second. |
| `datetime.strptime` | filter | Parse a string with a `strptime` format (classmethod; the string is piped in). |
| `datetime.time` | filter | Return the time part, without the timezone. |
| `datetime.timestamp` | filter | Return the POSIX timestamp. Naive values are taken as local time. |
| `datetime.timetuple` | filter | Return a `time.struct_time`. |
| `datetime.timetz` | filter | Return the time part, with the timezone. |
| `datetime.tzinfo` | attribute | The timezone, or None for a naive datetime. |
| `datetime.tzname` | filter | Return the timezone name, or None for a naive datetime. |
| `datetime.utcoffset` | filter | Return the UTC offset, or None for a naive datetime. |
| `datetime.utctimetuple` | filter | Return a `time.struct_time` in UTC. |

## decimal

| Name | Kinds | Description |
|------|-------|-------------|
| `decimal.adjusted` | filter | Return the exponent of the most significant digit. |
| `decimal.as_integer_ratio` | filter | Return the exact ratio `(numerator, denominator)`. |
| `decimal.as_tuple` | filter | Return `(sign, digits, exponent)`. |
| `decimal.canonical` | filter | Return the canonical encoding (the value itself). |
| `decimal.compare` | filter | Compare numerically: -1, 0 or 1 (NaN if either is NaN). |
| `decimal.compare_signal` | filter | Like `compare`, but signal on any NaN. |
| `decimal.compare_total` | filter | Compare by abstract representation (1.50 sorts before 1.5). |
| `decimal.compare_total_mag` | filter | Like `compare_total`, ignoring signs. |
| `decimal.conjugate` | filter | Return the complex conjugate (the value itself). |
| `decimal.copy_abs` | filter | Return the absolute value, without rounding. |
| `decimal.copy_negate` | filter | Return the negated value, without rounding. |
| `decimal.copy_sign` | filter | Return the value with the sign of `other`. |
| `decimal.exp` | filter | Return e raised to the value. |
| `decimal.fma` | filter | Fused multiply-add: `value * other + third`, rounded once. |
| `decimal.from_float` | filter | Return the exact Decimal for a float (classmethod; the float is piped in). |
| `decimal.imag` | attribute | The imaginary part (always 0). |
| `decimal.is_canonical` | filter, test | Return True (Decimals are always canonical). |
| `decimal.is_finite` | filter, test | Return True if the value is neither infinite nor NaN. |
| `decimal.is_infinite` | filter, test | Return True if the value is infinite. |
| `decimal.is_nan` | filter, test | Return True if the value is a NaN (quiet or signalling). |
| `decimal.is_normal` | filter, test | Return True if the value is a normal finite non-zero number. |
| `decimal.is_qnan` | filter, test | Return True if the value is a quiet NaN. |
| `decimal.is_signed` | filter, test | Return True if the sign is negative (including -0). |
| `decimal.is_snan` | filter, test | Return True if the value is a signalling NaN. |
| `decimal.is_subnormal` | filter, test | Return True if the value is subnormal. |
| `decimal.is_zero` | filter, test | Return True if the value is zero (of either sign). |
| `decimal.ln` | filter | Return the natural logarithm. |
| `decimal.log10` | filter | Return the base-10 logarithm. |
| `decimal.logb` | filter | Return the adjusted exponent as a Decimal. |
| `decimal.logical_and` | filter | Digit-wise AND of two logical operands. |
| `decimal.logical_invert` | filter | Digit-wise inversion of a logical operand, to the context precision. |
| `decimal.logical_or` | filter | Digit-wise OR of two logical operands. |
| `decimal.logical_xor` | filter | Digit-wise XOR of two logical operands. |
| `decimal.max` | filter | Return the larger of the value and `other`. |
| `decimal.max_mag` | filter | Return the one with the larger absolute value. |
| `decimal.min` | filter | Return the smaller of the value and `other`. |
| `decimal.min_mag` | filter | Return the one with the smaller absolute value. |
| `decimal.next_minus` | filter | Return the largest representable number smaller than the value. |
| `decimal.next_plus` | filter | Return the smallest representable number larger than the value. |
| `decimal.next_toward` | filter | Return the next representable number toward `other`. |
| `decimal.normalize` | filter | Strip trailing zeros (and use exponent form where needed). |
| `decimal.number_class` | filter | Return the class of the number, such as `+Normal` or `-Zero`. |
| `decimal.quantize` | filter | Round to the exponent of `exp` (`decimal.Decimal('0.01')` gives two places). |
| `decimal.radix` | filter | Return 10, the radix of Decimal arithmetic. |
| `decimal.real` | attribute | The real part (the value itself). |
| `decimal.remainder_near` | filter | Return the remainder of dividing by `other`, choosing the quotient nearest to exact. |
| `decimal.rotate` | filter | Rotate the digits by `other` places, to the context precision. |
| `decimal.same_quantum` | filter, test | Return True if both have the same exponent. |
| `decimal.scaleb` | filter | Return the value with its exponent adjusted by `other`. |
| `decimal.shift` | filter | Shift the digits by `other` places, to the context precision. |
| `decimal.sqrt` | filter | Return the square root, to the context precision. |
| `decimal.to_eng_string` | filter | Return engineering notation (exponent a multiple of 3). |
| `decimal.to_integral` | filter | Round to an integer (same as `to_integral_value`). |
| `decimal.to_integral_exact` | filter | Round to an integer, signalling Inexact and Rounded when it changes. |
| `decimal.to_integral_value` | filter | Round to an integer without signalling Inexact or Rounded. |

## dict

| Name | Kinds | Description |
|------|-------|-------------|
| `dict.clear` | filter | Return an empty dict. |
| `dict.copy` | filter | Return a shallow copy. |
| `dict.fromkeys` | filter | Return a dict with the piped keys, all set to `v` (classmethod; the keys are piped in). |
| `dict.get` | filter | Return the value for `key`, or `default`. |
| `dict.items` | filter | Return a view of the `(key, value)` pairs. |
| `dict.keys` | filter | Return a view of the keys. |
| `dict.pop` | filter | Return the value for `key` (or `default`; raises without one). The input keeps it. |
| `dict.popitem` | filter | Return the last `(key, value)` pair. The input keeps it. |
| `dict.setdefault` | filter | Return the value for `key`, or `default` if missing. The input is unchanged. |
| `dict.update` | filter | Return a copy updated from `other` and keyword arguments. |
| `dict.values` | filter | Return a view of the values. |

## float

| Name | Kinds | Description |
|------|-------|-------------|
| `float.as_integer_ratio` | filter | Return the exact ratio `(numerator, denominator)`. |
| `float.conjugate` | filter | Return the complex conjugate (the value itself). |
| `float.fromhex` | filter | Parse a hexadecimal float string (classmethod; the string is piped in). |
| `float.hex` | filter | Return the hexadecimal representation. |
| `float.imag` | attribute | The imaginary part (always 0.0). |
| `float.is_integer` | filter, test | Return True if the float has no fractional part. |
| `float.real` | attribute | The real part (the value itself). |

## fraction

| Name | Kinds | Description |
|------|-------|-------------|
| `fraction.as_integer_ratio` | filter | Return `(numerator, denominator)`. |
| `fraction.conjugate` | filter | Return the complex conjugate (the value itself). |
| `fraction.denominator` | attribute | The denominator, in lowest terms. |
| `fraction.from_decimal` | filter | Return the exact fraction for a Decimal (classmethod; the Decimal is piped in). |
| `fraction.from_float` | filter | Return the exact fraction for a float (classmethod; the float is piped in). |
| `fraction.imag` | attribute | The imaginary part (always 0). |
| `fraction.is_integer` | filter, test | Return True if the fraction is a whole number. |
| `fraction.limit_denominator` | filter | Return the closest fraction with a denominator of at most `max_denominator`. |
| `fraction.numerator` | attribute | The numerator, in lowest terms. |
| `fraction.real` | attribute | The real part (the value itself). |

## int

| Name | Kinds | Description |
|------|-------|-------------|
| `int.as_integer_ratio` | filter | Return `(value, 1)`. |
| `int.bit_count` | filter | Return the number of ones in the binary form of the absolute value. |
| `int.bit_length` | filter | Return the number of bits needed to represent the value, without sign. |
| `int.conjugate` | filter | Return the complex conjugate (the value itself). |
| `int.denominator` | attribute | The denominator (always 1). |
| `int.from_bytes` | filter | Return the integer represented by the bytes (classmethod; the bytes are piped in). |
| `int.imag` | attribute | The imaginary part (always 0). |
| `int.is_integer` | filter, test | Return True (for duck-type compatibility with float). |
| `int.numerator` | attribute | The numerator (the value itself). |
| `int.real` | attribute | The real part (the value itself, as an int). |
| `int.to_bytes` | filter | Return the bytes representing the value. |

## list

| Name | Kinds | Description |
|------|-------|-------------|
| `list.append` | filter | Return a copy with `x` added at the end. |
| `list.clear` | filter | Return an empty list. |
| `list.copy` | filter | Return a shallow copy. |
| `list.count` | filter | Return how many items equal `x`. |
| `list.extend` | filter | Return a copy with the items of `iterable` added at the end. |
| `list.index` | filter | Return the position of the first `x` (between `start` and `stop`). |
| `list.insert` | filter | Return a copy with `x` inserted before `index`. |
| `list.pop` | filter | Return the item at `index` (the last by default). The input keeps it. |
| `list.remove` | filter | Return a copy without the first `x`. Raises if `x` is missing. |
| `list.reverse` | filter | Return a reversed copy. |
| `list.sort` | filter | Return a sorted copy. `key` is a macro or an attribute name (a macro's result is text). |

## match

| Name | Kinds | Description |
|------|-------|-------------|
| `match.end` | filter | Return the end index of a group. |
| `match.endpos` | attribute | The `endpos` the search stopped at. |
| `match.expand` | filter | Fill a `re.sub` style template (`\1`, `\g<name>`) from this match. |
| `match.group` | filter | Return one group (by number or name; 0 or nothing is the whole match), or a tuple. |
| `match.groupdict` | filter | Return the named groups as a dict. |
| `match.groups` | filter | Return every group; groups that did not take part get `default`. |
| `match.lastgroup` | attribute | The name of the last group that matched, or None. |
| `match.lastindex` | attribute | The index of the last group that matched, or None. |
| `match.pos` | attribute | The `pos` the search started from. |
| `match.re` | attribute | The compiled pattern that produced this match. |
| `match.span` | filter | Return `(start, end)` of a group. |
| `match.start` | filter | Return the start index of a group. |
| `match.string` | attribute | The string that was searched. |

## path

| Name | Kinds | Description |
|------|-------|-------------|
| `path.anchor` | attribute | The drive and root together. |
| `path.as_posix` | filter | Return the path with forward slashes. |
| `path.as_uri` | filter | Return a `file:` URI. The path must be absolute. |
| `path.drive` | attribute | The drive letter or UNC share (empty on POSIX). |
| `path.is_absolute` | filter, test | Return True if the path has a root (and a drive, on Windows). |
| `path.is_relative_to` | filter, test | Return True if the path is under `other`. |
| `path.joinpath` | filter | Return the path with the segments appended. |
| `path.match` | filter, test | Return True if the path matches the glob pattern, matched from the right. |
| `path.name` | attribute | The final component. |
| `path.parent` | attribute | The logical parent. |
| `path.parents` | attribute | Every logical ancestor, nearest first. |
| `path.parts` | attribute | The components, as a tuple. |
| `path.relative_to` | filter | Return the path relative to `other`. Raises if it is not under it (unless `walk_up`). |
| `path.root` | attribute | The root separator, if any. |
| `path.stem` | attribute | The final component without its last suffix. |
| `path.suffix` | attribute | The last suffix of the final component, with the dot. |
| `path.suffixes` | attribute | Every suffix of the final component. |
| `path.with_name` | filter | Return the path with the final component replaced. |
| `path.with_stem` | filter | Return the path with the stem replaced. |
| `path.with_suffix` | filter | Return the path with the last suffix replaced (or removed with `''`). |

## pattern

| Name | Kinds | Description |
|------|-------|-------------|
| `pattern.findall` | filter | Return every non-overlapping match: strings, or tuples of groups. |
| `pattern.finditer` | filter | Return an iterator of match objects. |
| `pattern.flags` | attribute | The flags the pattern was compiled with, plus the engine's defaults. |
| `pattern.fullmatch` | filter, test | Return the match if the pattern matches all of `string[pos:endpos]`, or None. Also a test. |
| `pattern.groupindex` | attribute | Map each named group to its number. |
| `pattern.groups` | attribute | The number of capturing groups. |
| `pattern.match` | filter, test | Return the match at the start of `string[pos:endpos]`, or None. Also a test. |
| `pattern.pattern` | attribute | The pattern string. |
| `pattern.search` | filter, test | Return the first match in `string[pos:endpos]`, or None. Also a test. |
| `pattern.split` | filter | Split `string` by the matches. Groups in the pattern are kept. |
| `pattern.sub` | filter | Replace matches in `string` with `repl`: a string (`\1`, `\g<name>`) or a macro. |
| `pattern.subn` | filter | Like `pattern.sub`, but return `(new_string, number_of_substitutions)`. |

## re

| Name | Kinds | Description |
|------|-------|-------------|
| `re.escape` | filter | Escape every regex special character in the value. |
| `re.findall` | filter | Return every non-overlapping match: strings, or tuples of groups. |
| `re.finditer` | filter | Return an iterator of match objects. |
| `re.fullmatch` | filter, test | Return the match if `pattern` matches the whole value, or None. Also a test. |
| `re.match` | filter, test | Return the match of `pattern` at the start of the value, or None. Also a test. |
| `re.search` | filter, test | Return the first match of `pattern` anywhere in the value, or None. Also a test. |
| `re.split` | filter | Split the value by the matches of `pattern`. Groups in the pattern are kept. |
| `re.sub` | filter | Replace matches with `repl`: a string (`\1`, `\g<name>`) or a macro taking the match. |
| `re.subn` | filter | Like `re.sub`, but return `(new_string, number_of_substitutions)`. |

## str

| Name | Kinds | Description |
|------|-------|-------------|
| `str.capitalize` | filter | Return a copy with the first character upper-cased and the rest lower-cased. |
| `str.casefold` | filter | Return a casefolded copy, for caseless comparisons. |
| `str.center` | filter | Return the string centered in a field of `width`. |
| `str.count` | filter | Return the number of non-overlapping occurrences of `sub`. |
| `str.encode` | filter | Encode to bytes. |
| `str.endswith` | filter, test | Return True if the string ends with `suffix` (or any suffix in a tuple). |
| `str.expandtabs` | filter | Return a copy with tabs expanded to spaces. |
| `str.find` | filter | Return the lowest index of `sub`, or -1. |
| `str.format` | filter | Format the string with `str.format` (sandboxed: no unsafe attribute access). |
| `str.format_map` | filter | Format the string with values from `mapping` (sandboxed). |
| `str.index` | filter | Like `find`, but raise when `sub` is not found. |
| `str.isalnum` | filter, test | Return True if all characters are alphanumeric. |
| `str.isalpha` | filter, test | Return True if all characters are alphabetic. |
| `str.isascii` | filter, test | Return True if all characters are ASCII. |
| `str.isdecimal` | filter, test | Return True if all characters are decimal characters. |
| `str.isdigit` | filter, test | Return True if all characters are digits. |
| `str.isidentifier` | filter, test | Return True if the string is a valid Python identifier. |
| `str.islower` | filter, test | Return True if all cased characters are lower case. |
| `str.isnumeric` | filter, test | Return True if all characters are numeric. |
| `str.isprintable` | filter, test | Return True if all characters are printable. |
| `str.isspace` | filter, test | Return True if all characters are whitespace. |
| `str.istitle` | filter, test | Return True if the string is title-cased. |
| `str.isupper` | filter, test | Return True if all cased characters are upper case. |
| `str.join` | filter | Join the strings in `iterable` with the value as separator (`sep \| str.join(items)`). |
| `str.ljust` | filter | Return the string left-justified in a field of `width`. |
| `str.lower` | filter | Return a lower-cased copy. |
| `str.lstrip` | filter | Return a copy with leading `chars` (default whitespace) removed. |
| `str.partition` | filter | Split at the first `sep`: `(head, sep, tail)`. |
| `str.removeprefix` | filter | Return a copy without `prefix`, if it starts with it. |
| `str.removesuffix` | filter | Return a copy without `suffix`, if it ends with it. |
| `str.replace` | filter | Return a copy with `old` replaced by `new` (at most `count` times). |
| `str.rfind` | filter | Return the highest index of `sub`, or -1. |
| `str.rindex` | filter | Like `rfind`, but raise when `sub` is not found. |
| `str.rjust` | filter | Return the string right-justified in a field of `width`. |
| `str.rpartition` | filter | Split at the last `sep`: `(head, sep, tail)`. |
| `str.rsplit` | filter | Split from the right on `sep`, at most `maxsplit` times. |
| `str.rstrip` | filter | Return a copy with trailing `chars` (default whitespace) removed. |
| `str.split` | filter | Split on `sep` (default runs of whitespace), at most `maxsplit` times. |
| `str.splitlines` | filter | Split at line boundaries. |
| `str.startswith` | filter, test | Return True if the string starts with `prefix` (or any prefix in a tuple). |
| `str.strip` | filter | Return a copy with leading and trailing `chars` (default whitespace) removed. |
| `str.swapcase` | filter | Return a copy with upper case and lower case swapped. |
| `str.title` | filter | Return a title-cased copy. |
| `str.translate` | filter | Map characters through `table` (code point → string, code point or None to delete). |
| `str.upper` | filter | Return an upper-cased copy. |
| `str.zfill` | filter | Pad a numeric string with zeros on the left, after any sign. |

## time

| Name | Kinds | Description |
|------|-------|-------------|
| `time.dst` | filter | Return the daylight saving offset, or None if unknown. |
| `time.fold` | attribute | 0 or 1: which of two repeated wall times this is. |
| `time.fromisoformat` | filter | Parse an ISO time (classmethod; the string is piped in). |
| `time.hour` | attribute | The hour, 0 to 23. |
| `time.isoformat` | filter | Return the time in ISO 8601 format. |
| `time.microsecond` | attribute | The microsecond. |
| `time.minute` | attribute | The minute. |
| `time.replace` | filter | Return the time with the given fields replaced. `tzinfo=none` makes it naive. |
| `time.second` | attribute | The second. |
| `time.strftime` | filter | Format the time with a `strftime` format string. |
| `time.tzinfo` | attribute | The timezone, or None for a naive time. |
| `time.tzname` | filter | Return the timezone name, or None for a naive time. |
| `time.utcoffset` | filter | Return the UTC offset, or None for a naive time. |

## timedelta

| Name | Kinds | Description |
|------|-------|-------------|
| `timedelta.days` | attribute | The days part. |
| `timedelta.microseconds` | attribute | The microseconds part, below one second. |
| `timedelta.seconds` | attribute | The seconds part, below one day. |
| `timedelta.total_seconds` | filter | Return the whole duration in seconds. |

## uuid

| Name | Kinds | Description |
|------|-------|-------------|
| `uuid.bytes` | attribute | The 16 bytes, big-endian. |
| `uuid.bytes_le` | attribute | The 16 bytes, with the first three fields little-endian. |
| `uuid.clock_seq` | attribute | The 14-bit clock sequence. |
| `uuid.clock_seq_hi_variant` | attribute | The high byte of the clock sequence, with the variant bits. |
| `uuid.clock_seq_low` | attribute | The low byte of the clock sequence. |
| `uuid.fields` | attribute | The six integer fields. |
| `uuid.hex` | attribute | The 32 hex digits, without dashes. |
| `uuid.int` | attribute | The UUID as a 128-bit integer. |
| `uuid.is_safe` | attribute | Whether the UUID was generated in a multiprocessing-safe way. |
| `uuid.node` | attribute | The 48-bit node id (meaningful for version 1). |
| `uuid.time` | attribute | The 60-bit timestamp (meaningful for version 1). |
| `uuid.time_hi_version` | attribute | The next 16 bits, with the version bits. |
| `uuid.time_low` | attribute | The first 32 bits of the UUID. |
| `uuid.time_mid` | attribute | The next 16 bits of the UUID. |
| `uuid.urn` | attribute | The UUID as a URN. |
| `uuid.variant` | attribute | The variant, as one of the `uuid.RESERVED_*` / `uuid.RFC_4122` strings. |
| `uuid.version` | attribute | The version number (1 to 8), or None if the variant is not RFC 4122. |
