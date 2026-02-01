---
layout: default
title: 公約
---

# 参議院選挙　東京選挙区

{% for person in site.politicians %}
---

## {{ person.name }}

![議員の顔写真]({{ site.baseurl }}{{ person.photo }}){: width="200" }


{{ person.party }}

### 公約

{% for item in person.promises %}
- **{{ item.topic }}**: {{ item.description }}  

{% endfor %}

{% endfor %}


