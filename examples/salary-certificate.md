# شهادة راتب

نشهد بأن السيد/ة **{{ name }}** يعمل لدينا في قسم {{ department }} منذ
{{ hired | to_date | ar.format_date("%d %B %Y") }}، وأن راتبه الشهري
{{ salary | ar.format_number }} دولار أمريكي ({{ salary | ar.to_words }} دولار أمريكي لا غير).

أُعطيت هذه الشهادة بناءً على طلبه.
