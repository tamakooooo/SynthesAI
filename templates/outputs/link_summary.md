# {{ title }}

**来源**: {{ source }}
**URL**: {{ url }}
**字数**: {{ word_count }}
**阅读时间**: {{ reading_time }}
**难度**: {{ difficulty }}
**生成时间**: {{ created_at }}

---

## 内容摘要

{{ summary }}

---

## 核心要点

{% for point in key_points %}
{{ loop.index }}. {{ point }}
{% endfor %}

---

{% if key_concepts %}

## 关键概念解释

{% for concept in key_concepts %}
### {{ concept.term }}

{{ concept.definition }}

{% endfor %}

{% endif %}

---

## 标签

{% for tag in tags %}
#{{ tag }}{% if not loop.last %} {% endif %}
{% endfor %}

---

*由 Learning Assistant 自动生成*