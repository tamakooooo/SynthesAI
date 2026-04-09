# {{ title }}

**来源**: {{ source }}
**URL**: {{ url }}
**字数**: {{ word_count }}
**阅读时间**: {{ reading_time }}
**难度**: {{ difficulty }}
**生成时间**: {{ created_at }}

---

## 摘要

{{ summary }}

---

## 核心要点

{% for point in key_points %}
{{ loop.index }}. {{ point }}
{% endfor %}

---

## 标签

{% for tag in tags %}
#{{ tag }}{% if not loop.last %} {% endif %}
{% endfor %}

---

{% if qa_pairs %}

## 问答对

{% for qa in qa_pairs %}

### Q{{ loop.index }}: {{ qa.question }}

**难度**: {{ qa.difficulty }}

{{ qa.answer }}

{% endfor %}

{% endif %}

---

{% if quiz %}

## 测验题

{% for q in quiz %}

### 问题 {{ loop.index }}

**类型**: {{ q.type }}

{{ q.question }}

{% if q.options %}

**选项**:
{% for option in q.options %}
{{ loop.index }}. {{ option }}
{% endfor %}

{% endif %}

**正确答案**: {{ q.correct }}

{% if q.explanation %}

**解释**: {{ q.explanation }}

{% endif %}

{% endfor %}

{% endif %}

---

*由 Learning Assistant 自动生成*